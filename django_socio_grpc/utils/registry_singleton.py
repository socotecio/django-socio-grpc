import inspect
import logging
from collections import OrderedDict
from typing import TYPE_CHECKING, Dict, List, Tuple, Type

from django.db import models
from rest_framework.fields import (
    DictField,
    HiddenField,
    ListField,
    ModelField,
    ReadOnlyField,
    SerializerMethodField,
)
from rest_framework.relations import ManyRelatedField, RelatedField, SlugRelatedField
from rest_framework.serializers import BaseSerializer, ListSerializer
from rest_framework.utils.model_meta import get_field_info

from django_socio_grpc.proto_serializers import (
    BaseProtoSerializer,
    ListProtoSerializer,
    ProtoSerializer,
)
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils import model_meta
from django_socio_grpc.utils.tools import ProtoComment, rreplace

from .constants import (
    DEFAULT_LIST_FIELD_NAME,
    LIST_ATTR_MESSAGE_NAME,
    REQUEST_SUFFIX,
    RESPONSE_SUFFIX,
)

if TYPE_CHECKING:
    from django_socio_grpc.services import Service
    from django_socio_grpc.utils.servicer_register import AppHandlerRegistry

logger = logging.getLogger("django_socio_grpc")


class RegisterServiceException(Exception):
    pass


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


TYPE_MAPPING = {
    # Numeric
    models.AutoField.__name__: "int32",
    models.BigAutoField.__name__: "int64",
    models.SmallIntegerField.__name__: "int32",
    models.IntegerField.__name__: "int32",
    models.BigIntegerField.__name__: "int64",
    models.PositiveSmallIntegerField.__name__: "int32",
    models.PositiveIntegerField.__name__: "int32",
    models.FloatField.__name__: "float",
    models.DecimalField.__name__: "double",
    # Boolean
    models.BooleanField.__name__: "bool",
    models.NullBooleanField.__name__: "bool",
    # Date and time
    models.DateField.__name__: "string",
    models.TimeField.__name__: "string",
    models.DateTimeField.__name__: "string",
    models.DurationField.__name__: "string",
    # String
    models.CharField.__name__: "string",
    models.TextField.__name__: "string",
    models.EmailField.__name__: "string",
    models.SlugField.__name__: "string",
    models.URLField.__name__: "string",
    models.UUIDField.__name__: "string",
    models.GenericIPAddressField.__name__: "string",
    models.FilePathField.__name__: "string",
    # Other
    models.BinaryField.__name__: "bytes",
    # Default
    models.Field.__name__: "string",
}


class RegistrySingleton(metaclass=SingletonMeta):
    """
    Registry Singleton is a singleton class allowing to grab all the service declared in grpc_settings.ROOT_HANDLERS_HOOK
    and introspect django model and serializer to determine the proto to generate
    """

    # JSONField and PositiveBigIntegerField not available on Django 2.2
    try:
        # Special
        TYPE_MAPPING[models.JSONField.__name__] = "google.protobuf.Struct"
    except AttributeError:
        from django.contrib.postgres.fields import JSONField

        TYPE_MAPPING[JSONField.__name__] = "google.protobuf.Struct"

    try:
        TYPE_MAPPING[models.PositiveBigIntegerField.__name__] = "int64"
    except AttributeError:
        pass

    _instances = {}

    @classmethod
    def clean_all(cls):
        cls._instances = {}

    def __init__(self):
        self.registered_app: OrderedDict[str, "AppHandlerRegistry"] = OrderedDict()

    ############################################################################
    #
    # Common function used by both generation method (decorator and know_method)
    #
    ############################################################################

    def register_serializer_as_message_if_not_exist(
        self, app_name, serializer_instance, message_name=None, is_request=True
    ):
        """
        Register a message if not already exsting in the registered_messages of an app_name
        This message need to be in a correct format that will be used by generators to transform it into generators
        """
        if message_name is None:
            message_name = get_message_name_from_field_or_serializer_instance(
                serializer_instance, is_request
            )

        pk_name = None
        if getattr(serializer_instance.Meta, "model", None):
            pk_name = model_meta.get_model_pk(serializer_instance.Meta.model).name

        if message_name in self.registered_app[app_name].registered_messages:
            return message_name

        self.registered_app[app_name].registered_messages[message_name] = []

        # Add comment for whole message if proto_comment exists in Meta
        if hasattr(serializer_instance.Meta, "proto_comment"):
            self.registered_app[app_name].registered_messages_comments[message_name] = (
                serializer_instance.Meta.proto_comment
                if isinstance(serializer_instance.Meta.proto_comment, ProtoComment)
                else ProtoComment(serializer_instance.Meta.proto_comment)
            )

        if issubclass(serializer_instance.__class__, ProtoSerializer):
            for field_name, field_type in serializer_instance.get_fields().items():

                # INFO - AM - 21/01/2022 - HiddenField are not used in api so not showed in protobuf file
                if issubclass(field_type.__class__, HiddenField):
                    continue

                # INFO - AM - 21/01/2022 - if SEPARATE_READ_WRITE_MODEL is true (by default yes) then we
                # need to filter read only or write only field depend of if is requets message or not
                # By defautl in DRF Pk are read_only. But in grpc we want them
                # to be in the message
                if grpc_settings.SEPARATE_READ_WRITE_MODEL and field_name != pk_name:
                    if is_request and self.field_type_is_read_only(field_type):
                        continue
                    if not is_request and self.field_type_is_write_only(field_type):
                        continue

                field_grpc_generator_format = (
                    field_name,
                    self.get_proto_type(
                        app_name,
                        field_type,
                        field_name,
                        serializer_instance,
                        is_request=is_request,
                    ),
                    getattr(field_type, "help_text", ""),
                )

                self.registered_app[app_name].registered_messages[message_name].append(
                    field_grpc_generator_format
                )
        # INFO - AM - 07/01/2022 - else if the field type inherit from base proto
        # serializer and not protoserializer get_fields method is not implemented
        # so we need a custom action here
        else:
            message = serializer_instance.to_proto_message()
            messages_fields = [
                (item["name"], item["type"], ProtoComment(item.get("comment", "")))
                for item in message
            ]
            self.registered_app[app_name].registered_messages[message_name] = messages_fields

        return message_name

    def field_type_is_read_only(self, field_type):
        # INFO - AM - 07/01/2022 - If the field type inherit of ListProtoSerializer that mean we have
        if issubclass(field_type.__class__, ReadOnlyField):
            return True
        return field_type.read_only is True

    def field_type_is_write_only(self, field_type):
        return field_type.write_only is True

    def get_proto_type(
        self, app_name, field_type, field_name, serializer_instance, is_request=None
    ):
        """
        Return a proto_type  to use in the proto file from a field type.
        For SerializerMethodField we also need field_name and serializer_instance
        """

        # If field type is a str that mean we use a custom field
        if isinstance(field_type, str):
            return field_type

        proto_type = TYPE_MAPPING.get(field_type.__class__.__name__, "string")

        # if  field_name == "slug_many_many":
        #     print(f"class is : {field_type.__class__}")
        #     print(f"is subclas of ListProtoSerializer: {issubclass(field_type.__class__, ListProtoSerializer)}")
        #     print(f"is subclas of BaseProtoSerializer: {issubclass(field_type.__class__, BaseProtoSerializer)}")
        #     print(f"is subclas of SlugRelatedField: {issubclass(field_type.__class__, SlugRelatedField)}")
        #     print(
        #         f"is subclas of ManyRelatedField: {issubclass(field_type.__class__, ManyRelatedField)}"
        #     )
        #     print(f"is subclas of RelatedField: {issubclass(field_type.__class__, RelatedField)}")
        #     print(f"is subclas of ListSerializer: {issubclass(field_type.__class__, ListSerializer)}")
        #     print(f"is subclas of ListField: {issubclass(field_type.__class__, ListField)}")
        #     print(f"is subclas of DictField: {issubclass(field_type.__class__, DictField)}")
        #     print(f"is subclas of BaseSerializer: {issubclass(field_type.__class__, BaseSerializer)}")
        #     print(f"is subclas of SerializerMethodField: {issubclass(field_type.__class__, SerializerMethodField)}")

        # INFO - AM - 07/01/2022 - If the field type inherit of ListProtoSerializer that mean we have
        if issubclass(field_type.__class__, ListProtoSerializer):
            proto_type = f"repeated {get_message_name_from_field_or_serializer_instance(field_type.child, is_request=is_request)}"
            # INFO - AM - 07/01/2022 - If nested serializer not used anywhere else we need to add it too
            self.register_serializer_as_message_if_not_exist(
                app_name, field_type.child, is_request=is_request
            )

        # INFO - AM - 07/01/2022 - else if the field type inherit from proto serializer that mean that it is generated as a message in the proto file
        elif issubclass(field_type.__class__, BaseProtoSerializer):
            proto_type = get_message_name_from_field_or_serializer_instance(
                field_type, is_request=is_request
            )
            # INFO - AM - 07/01/2022 - If nested serializer not used anywhere else we need to add it too
            self.register_serializer_as_message_if_not_exist(
                app_name, field_type, is_request=is_request
            )

        # INFO - AM - 07/01/2022 - Else if the field type inherit from the SlugRelatedField that mean the type is the type name attribute in the foreign model
        elif issubclass(field_type.__class__, SlugRelatedField):
            proto_type = self.get_pk_from_slug_related_field(
                field_type, field_name, serializer_instance
            )

        # INFO - AM - 07/01/2022 - Else if the field type inherit from the ManyRelatedField that mean the type is the type of the pk of the child_relation (see relations.py of drf)
        elif issubclass(field_type.__class__, ManyRelatedField):
            child_proto_type = self.get_proto_type(
                app_name,
                field_type.child_relation,
                field_name,
                serializer_instance,
                is_request=is_request,
            )
            # INFO - AM - 03/02/2022 - if the returned child_proto_type returned is repeated (this can happen with slud related field in a many many relationships) we remove it because we only need one repeated
            if child_proto_type.startswith("repeated "):
                child_proto_type = child_proto_type[9:]
            proto_type = f"repeated {child_proto_type}"

        # INFO - AM - 07/01/2022 - Else if the field type inherit from the RelatedField that mean the type is the type of the pk of the foreign model
        elif issubclass(field_type.__class__, RelatedField):
            proto_type = self.get_pk_from_related_field(field_type)

        # INFO - AM - 07/01/2022 - Else if the field type inherit from the ListSerializer that mean it's a repeated Struct
        elif issubclass(field_type.__class__, ListSerializer):
            proto_type = "repeated google.protobuf.Struct"

        # INFO - AM - 07/01/2022 - Else if the field type inherit from the ListField that mean it's a repeated of the child attr proto type
        elif issubclass(field_type.__class__, ModelField):
            proto_type = TYPE_MAPPING.get(field_type.model_field.__class__.__name__, "string")

        # INFO - AM - 07/01/2022 - Else if the field type inherit from the ListField that mean it's a repeated of the child attr proto type
        elif issubclass(field_type.__class__, ListField):
            child_proto_type = self.get_proto_type(
                app_name,
                field_type.child,
                field_name,
                serializer_instance,
                is_request=is_request,
            )
            # INFO - AM - 03/02/2022 - if the returned child_proto_type returned is repeated
            # (this can happen with slud related field in a many many relationships) we remove it because we only need one repeated
            if child_proto_type.startswith("repeated "):
                child_proto_type = child_proto_type[9:]
            proto_type = f"repeated {child_proto_type}"

        # INFO - AM - 07/01/2022 - Else if the field type inherit from the DictField that mean it's a Struct
        elif issubclass(field_type.__class__, DictField):
            proto_type = "google.protobuf.Struct"

        # INFO - AM - 07/01/2022 - Else if the field type inherit from the BaseSerializer that mean it's a Struct
        elif issubclass(field_type.__class__, BaseSerializer):
            proto_type = "google.protobuf.Struct"

        # INFO - AM - 07/01/2022 - Else if the field type inherit from the BaseSerializer that mean it's a Struct
        elif issubclass(field_type.__class__, SerializerMethodField):
            proto_type = get_proto_type_from_inspect(
                field_type, field_name, serializer_instance
            )

        return proto_type

    def get_pk_from_related_field(self, related_field):
        """
        When we have RelatedField (relation by id) we need to find the type of this relation.
        it can be specified by the pk_field or the queryset of the relatedfield
        """
        if related_field.pk_field:
            type_name = related_field.pk_field.__class__.__name__
        else:
            # INFO - AM - 08/10/2022 - happen if read_only = True
            if related_field.queryset is None:
                try:
                    logger.warning(
                        "One of your related field in your seriliazer is in read only without queryset parameter and without pk_field parameter. We can't automatically determine the type of this related field. Defaulting to DEFAULT_AUTO_FIELD or string for django < 3.2. Please use pk_field param to specify the type if needed."
                    )
                    from django.conf import settings

                    # INFO - AM - 08/10/2022 - settings.DEFAULT_AUTO_FIELD look like django.db.models.AutoField
                    type_name = settings.DEFAULT_AUTO_FIELD.split(".")[-1]
                except Exception:  # INFO - AM - 08/10/2022 - before django 3.2  DEFAULT_AUTO_FIELD does not exist
                    type_name = models.CharField.__name__
            else:
                type_name = model_meta.get_model_pk(
                    related_field.queryset.model
                ).__class__.__name__
        grpc_field_type = TYPE_MAPPING.get(type_name, "related_not_found")
        if grpc_field_type == "related_not_found":
            logger.error(f"No mapping found in registry_singleton for {type_name}")
        return grpc_field_type

    def get_pk_from_slug_related_field(
        self, slug_related_field, field_name, serializer_instance
    ):
        """
        When we have SlugRelatedField (relation by a field) we need to find the type of the field used in the relation by its name.
        it is specified by slug_field
        """

        if not hasattr(serializer_instance.Meta, "model"):
            print(
                f"GENERATION ERROR: No Model in serializer {serializer_instance.__class__.__name__} Meta but using a SlugRelatedField"
            )
            return "string"

        # INFO - AM - 27/01/2022 - get_field_info is drf utils methods to get all the informations about the fields and the relations of a model
        # See: https://github.com/encode/django-rest-framework/blob/master/rest_framework/utils/model_meta.py
        (
            pk,
            fields,
            forward_relations,
            reverse_relations,
            fields_and_pk,
            relationships,
        ) = get_field_info(serializer_instance.Meta.model)

        # INFO - AM - 27/01/2022 - the field name need to match with an existing relation ship to have a correct SlugRelatedField
        if field_name not in relationships:
            print(
                f"GENERATION ERROR: slug_related field name {field_name} not found in relationships of {serializer_instance.Meta.model}"
            )
            return "string"

        (
            model_field,
            related_model,
            to_many,
            to_field,
            has_through_model,
            reverse,
        ) = relationships[field_name]

        # INFO - AM - 27/01/2022 - A SlugRelatedFiel has a required slug_field attribute that is the name of the attibute in the related model we want to find the proto type
        slug_defered_attribute = getattr(related_model, slug_related_field.slug_field, None)
        if slug_defered_attribute is None:
            print(
                f"GENERATION ERROR: Related_Model_{str(related_model)}_as_no_field_{slug_related_field.slug_field}"
            )
            return "string"

        # INFO - AM - 27/01/2022 - As there is reverse relationship django return a slug_defered_attribute that has a field attribute that is the field that we want to find the prototype
        slug_field_class_name = slug_defered_attribute.field.__class__.__name__

        proto_type = TYPE_MAPPING.get(slug_field_class_name, "slug_field type not found")

        # INFO - AM - 27/01/2022 - If to_many args is true that mean we have a repeated proto type
        if to_many:
            proto_type = f"repeated {proto_type}"

        return proto_type

    def register_list_message_of_serializer(
        self,
        app_name,
        service_instance,
        base_name,
        list_response_field_name,
        child_response_message_name,
        message_name=None,
        is_request=False,
    ):

        pagination = service_instance.pagination_class
        if pagination is None:
            pagination = grpc_settings.DEFAULT_PAGINATION_CLASS is not None

        response_fields = [
            (list_response_field_name, f"repeated {child_response_message_name}", "")
        ]
        if pagination:
            response_fields += [("count", "int32", "")]

        # INFO - AM - 04/02/2022 - For list message with a custom name we need to add
        # List Before Response or Request end of word if seperate settings is true
        if message_name:
            if grpc_settings.SEPARATE_READ_WRITE_MODEL:
                suffix_len = 0
                if is_request and message_name.endswith(REQUEST_SUFFIX):
                    suffix_len = len(REQUEST_SUFFIX)
                elif not is_request and message_name.endswith(RESPONSE_SUFFIX):
                    suffix_len = len(RESPONSE_SUFFIX)

                response_message_name = (
                    message_name[:-suffix_len] + "List" + message_name[-suffix_len:]
                )
            else:
                response_message_name = f"{message_name}List"
        else:
            response_message_name = f"{base_name}List{RESPONSE_SUFFIX}"

        self.registered_app[app_name].registered_messages[
            response_message_name
        ] = response_fields

        return response_message_name

    def get_list_response_field_name_from_serializer_instance(self, serializer_instance):
        # INFO - AM - 14/01/2022 - We let the possibility to the user to customize the name of the attr where the list items are set by message_list_attr attr in meta class. If not present we use the default results
        serializer_meta = getattr(serializer_instance, "Meta", None)
        if not serializer_meta:
            return DEFAULT_LIST_FIELD_NAME
        return getattr(serializer_meta, LIST_ATTR_MESSAGE_NAME, DEFAULT_LIST_FIELD_NAME)

    ############################################################################
    #
    # Decorator Registration
    #
    ############################################################################
    def register_custom_action(
        self,
        service_class: Type["Service"],
        function_name,
        request=None,
        response=None,
        request_name=None,
        response_name=None,
        request_stream=False,
        response_stream=False,
        use_request_list=False,
        use_response_list=False,
    ):
        app_name = service_class._app_handler.app_name

        service_instance = service_class()
        service_name = service_instance.get_service_name()

        (
            request_message_name,
            list_response_field_name,
        ) = self.register_message_for_custom_action(
            app_name,
            service_name,
            function_name,
            request,
            is_request=True,
            message_name=request_name,
        )
        if use_request_list:
            base_name = self.get_base_name_for_list_message(
                service_name, function_name, message_name=request_message_name, is_request=True
            )
            request_message_name = self.register_list_message_of_serializer(
                app_name,
                service_instance,
                base_name=base_name,
                list_response_field_name=list_response_field_name,
                child_response_message_name=request_message_name,
                message_name=request_name,
                is_request=True,
            )

        (
            response_message_name,
            list_response_field_name,
        ) = self.register_message_for_custom_action(
            app_name,
            service_name,
            function_name,
            response,
            is_request=False,
            message_name=response_name,
        )
        if use_response_list:
            base_name = self.get_base_name_for_list_message(
                service_name,
                function_name,
                message_name=response_message_name,
                is_request=False,
            )
            response_message_name = self.register_list_message_of_serializer(
                app_name,
                service_instance,
                base_name=base_name,
                list_response_field_name=list_response_field_name,
                child_response_message_name=response_message_name,
                message_name=response_name,
                is_request=False,
            )

        self.register_method_for_custom_action(
            app_name,
            service_instance.get_controller_name(),
            function_name,
            request_message_name,
            response_message_name,
            request_stream,
            response_stream,
        )

        return request_message_name, response_message_name

    def register_method_for_custom_action(
        self,
        app_name,
        controller_name,
        function_name,
        request_message_name,
        response_message_name,
        request_stream,
        response_stream,
    ):
        if controller_name not in self.registered_app[app_name].registered_controllers:
            self.registered_app[app_name].registered_controllers[
                controller_name
            ] = OrderedDict()
        self.registered_app[app_name].registered_controllers[controller_name][
            function_name
        ] = {
            "request": {"is_stream": request_stream, "message": request_message_name},
            "response": {"is_stream": response_stream, "message": response_message_name},
        }

    def register_message_for_custom_action(
        self, app_name, service_name, function_name, message, is_request, message_name=None
    ):
        if isinstance(message, list):
            if len(message) == 0 and not message_name:
                return "google.protobuf.Empty", DEFAULT_LIST_FIELD_NAME

            messages_fields = [
                (item["name"], item["type"], ProtoComment(item.get("comment", "")))
                for item in message
            ]
            if message_name is None:
                message_name = f"{service_name}{function_name}{REQUEST_SUFFIX if is_request else RESPONSE_SUFFIX}"
            self.registered_app[app_name].registered_messages[message_name] = messages_fields
            return message_name, DEFAULT_LIST_FIELD_NAME

        elif isinstance(message, str):
            # TODO - AM - 27/01/2022 - Maybe check for authorized string like google.protobuf.empty to avoid developer making syntax mistake
            return message, DEFAULT_LIST_FIELD_NAME
        elif inspect.isclass(message) and issubclass(message, BaseSerializer):
            serializer_instance = message()
            list_response_field_name = (
                self.get_list_response_field_name_from_serializer_instance(serializer_instance)
            )
            message_name = self.register_serializer_as_message_if_not_exist(
                app_name, serializer_instance, message_name, is_request=is_request
            )
            return (
                message_name,
                list_response_field_name,
            )
        else:
            raise RegisterServiceException(
                f"{REQUEST_SUFFIX if is_request else RESPONSE_SUFFIX} message for function {function_name} in app {app_name} is not a list, a serializer or a string"
            )

    def get_base_name_for_list_message(
        self, service_name, function_name, message_name, is_request=True
    ):
        suffix = REQUEST_SUFFIX if is_request else RESPONSE_SUFFIX
        # INFO - AM - 09/02/2022 - If special protobuf message we have to determine the name for the message
        if self.is_special_protobuf_message(message_name):
            base_name = f"{service_name}{function_name}"
        else:
            base_name = rreplace(message_name, suffix, "", 1)
        return base_name

    def get_app_name_from_service_class(self, service_class):
        return service_class.__module__.split(".")[0]

    def is_special_protobuf_message(self, message_name):
        return message_name.startswith("google.protobuf")


def get_message_name_from_field_or_serializer_instance(
    class_or_field_instance, is_request=None, append_type=True
):
    # INFO - AM - 21/01/2022 - if SEPARATE_READ_WRITE_MODEL is true (by default yes) then we have two different message for the same serializer
    class_name = class_or_field_instance.__class__.__name__
    if "ProtoSerializer" in class_name:
        message_name = rreplace(class_name, "ProtoSerializer", "", 1)
    elif "Serializer" in class_name:
        message_name = rreplace(class_name, "Serializer", "", 1)
    else:
        message_name = class_name

    if grpc_settings.SEPARATE_READ_WRITE_MODEL and append_type:
        message_name = f"{message_name}{REQUEST_SUFFIX if is_request else RESPONSE_SUFFIX}"
    return message_name


def get_lookup_field_from_serializer(serializer_instance, service_instance, field_name=None):
    """
    Find the field associated to the lookup field
    serializer_instance: instance of the serializer used in this service where the lookup field should be present
    service_instance: the service instance itself where we can introspect for lookupfield
    field_name: If e do not want to use the default lookup field of the service but a specific field we just have to specify this params

    return: iterable: [str, <drf.serializers.Field>]
    """
    if field_name is None:
        field_name = service_instance.get_lookup_request_field()

    # TODO - AM - 07/01/2022 - Check if the fied name in the existing field
    if field_name not in serializer_instance.fields:
        raise RegisterServiceException(
            f"Trying to build a Retrieve or Destroy request with retrieve field named: {field_name} but this field is not existing in the serializer: {serializer_instance.__class__.__name__}"
        )

    field_proto_type = TYPE_MAPPING.get(
        serializer_instance.fields[field_name].__class__.__name__,
        "lookup_field_type_not_found",
    )

    # INFO - AM - 07/01/2022 - to match the format retuned by get_fields used for the generation we need to return an iterable with first element field_name and second element the proto type format
    return [field_name, field_proto_type]


def get_proto_type_from_inspect(field_type, field_name, serializer_instance):
    """
    In some cases (for now only SerializerMethodField) we need to introspect method and ask user to specify the return type to be able to find the correct proto type
    """
    method_name = field_type.method_name
    if method_name is None:
        method_name = f"get_{field_name}"
    method = getattr(serializer_instance, method_name, None)
    if method is None:
        # TODO - AM - 21/01/2022 - What todo here ? raise an excpetion or let DRF handle this kind of problems ?
        return "string"

    if "return" not in method.__annotations__:
        raise RegisterServiceException(
            f"You are trying to register the serializer {serializer_instance.__class__.__name__} with a SerializerMethodField on the field {field_name}. But the method associated does'nt have a return annotations. Please look at the example: https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/tests/fakeapp/serializers.py#L83. And the python doc: https://docs.python.org/3.8/library/typing.html"
        )

    python_type_to_proto_type = {
        int: "int32",
        str: "string",
        bool: "bool",
        float: "float",
        list: "repeated string",
        dict: "google.protobuf.Struct",
        bytes: "bytes",
        List: "repeated string",
        Dict: "google.protobuf.Struct",
        List[int]: "repeated int32",
        List[str]: "repeated string",
        List[bool]: "repeated bool",
        List[Tuple]: "repeated google.protobuf.Struct",
        List[Dict]: "repeated google.protobuf.Struct",
    }

    return python_type_to_proto_type[method.__annotations__["return"]]
