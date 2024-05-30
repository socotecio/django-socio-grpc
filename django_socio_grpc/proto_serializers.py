from typing import Dict, MutableSequence

from asgiref.sync import sync_to_async
from django.core.validators import MaxLengthValidator
from django.db.models.fields import NOT_PROVIDED
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import (
    LIST_SERIALIZER_KWARGS,
    BaseSerializer,
    Field,
    ListSerializer,
    ModelSerializer,
    ReadOnlyField,
    Serializer,
)
from rest_framework.settings import api_settings
from rest_framework.utils.formatting import lazy_format

from django_socio_grpc.protobuf.exceptions import (
    FutureAnnotationError,
    ListWithMultipleArgsError,
    NoReturnTypeError,
    ProtoRegistrationError,
    UnknownTypeError,
)
from django_socio_grpc.protobuf.json_format import message_to_dict, parse_dict
from django_socio_grpc.protobuf.proto_classes import ProtoField, ProtoFieldConvertible
from django_socio_grpc.utils.constants import (
    DEFAULT_LIST_FIELD_NAME,
    LIST_ATTR_MESSAGE_NAME,
    PARTIAL_UPDATE_FIELD_NAME,
)
from django_socio_grpc.utils.model_meta import get_model_pk

LIST_PROTO_SERIALIZER_KWARGS = (*LIST_SERIALIZER_KWARGS, LIST_ATTR_MESSAGE_NAME, "message")


class _NoDictData(Exception):
    pass


def get_default_value(field_default):
    if callable(field_default):
        return field_default()
    else:
        return field_default


class BaseProtoSerializer(BaseSerializer):
    fields: Dict[str, Field]

    def __init__(self, *args, **kwargs):
        if "message" in kwargs and "data" in kwargs:
            raise ValueError(
                "If you pass a 'message' you should not pass a 'data' argument. The 'data' will be generated from the 'message'."
            )
        message = kwargs.pop("message", None)
        self.stream = kwargs.pop("stream", None)
        self.message_list_attr = kwargs.pop(LIST_ATTR_MESSAGE_NAME, DEFAULT_LIST_FIELD_NAME)
        super().__init__(*args, **kwargs)
        if message is not None:
            self.initial_message = message
            # INFO - LG - 23/05/2024 - initial_data is empty at this point
            self.initial_data = self.message_to_data(message)

    def message_to_data(self, message):
        """Protobuf message -> Dict of python primitive datatypes."""
        return self._MessageToData(message, self).get_data()

    def data_to_message(self, data):
        """Protobuf message <- Dict of python primitive datatypes."""
        assert hasattr(
            self, "Meta"
        ), f'Class {self.__class__.__name__} missing "Meta" attribute'
        assert hasattr(
            self.Meta, "proto_class"
        ), f'Class {self.__class__.__name__} missing "Meta.proto_class" attribute'
        return parse_dict(data, self.Meta.proto_class())

    @property
    def message(self):
        if not hasattr(self, "_message"):
            self._message = self.data_to_message(self.data)
        return self._message

    async def asave(self, **kwargs):
        return await sync_to_async(self.save)(**kwargs)

    async def ais_valid(self, *, raise_exception=False):
        return await sync_to_async(self.is_valid)(raise_exception=raise_exception)

    async def acreate(self, validated_data):
        return await sync_to_async(self.create)(validated_data)

    async def aupdate(self, instance, validated_data):
        return await sync_to_async(self.update)(instance, validated_data)

    @property
    async def adata(self):
        return await sync_to_async(getattr)(self, "data")

    @property
    async def amessage(self):
        if not hasattr(self, "_message"):
            self._message = self.data_to_message(await self.adata)
        return self._message

    @classmethod
    def many_init(cls, *args, **kwargs):
        allow_empty = kwargs.pop("allow_empty", None)
        child_serializer = cls(*args, **kwargs)
        list_kwargs = {"child": child_serializer}
        if allow_empty is not None:
            list_kwargs["allow_empty"] = allow_empty
        list_kwargs.update(
            {
                key: value
                for key, value in kwargs.items()
                if key in LIST_PROTO_SERIALIZER_KWARGS
            }
        )
        meta = getattr(cls, "Meta", None)
        list_serializer_class = getattr(meta, "list_serializer_class", ListProtoSerializer)
        return list_serializer_class(*args, **list_kwargs)

    def to_proto_message(self):
        raise NotImplementedError(
            "If you want to use BaseProtoSerializer instead of ProtoSerializer you need to implement 'to_proto_message' method as there is no fields to introspect from. Please read the documentation"
        )

    class _MessageToData:
        """
        This nested class is used to handle the conversion of a protobuf message to a dict of python primitive datatypes.
        It is responsible for dealing with edge cases such as partial updates and optional fields.
        """

        def __init__(self, message, serializer):
            self.message = message
            self.serializer: Serializer = serializer
            self.base_data = message_to_dict(message)

        @property
        def partial_fields(self):
            return self.base_data.get(PARTIAL_UPDATE_FIELD_NAME, [])

        def get_data(self):
            """
            This method allow to populate the data dictionary with None for optional field that allow_null and not send in the request.
            It's also allow to deal with partial update correctly.
            This is mandatory for having null value received in request as DRF expect to have None value for field that are required.
            We can't rely only on required True/False as in DSG if a field is required it will have the default value of it's type (empty string for string type) and not None

            When refactoring serializer to only use message we will be able to determine the default value of the field depending of the same logic followed here

            set default value for field except if optional or partial update
            """
            # INFO - AM - 04/01/2024 - If we are in a partial serializer with a message we need to have the PARTIAL_UPDATE_FIELD_NAME in the data_dict. If not we raise an exception
            if self.serializer.partial and PARTIAL_UPDATE_FIELD_NAME not in self.base_data:
                raise ValidationError(
                    {
                        PARTIAL_UPDATE_FIELD_NAME: [
                            f"Field {PARTIAL_UPDATE_FIELD_NAME} not set in message when using partial=True"
                        ]
                    },
                    code="missing_partial_message_attribute",
                )

            cleaned_data = {}

            for name, field in self.serializer.fields.items():
                try:
                    cleaned_data[name] = self.get_cleaned_field_value(field)
                except _NoDictData:
                    continue

            return cleaned_data

        def get_nullable_field_value(self, field: Field):
            if field.allow_null or (field.default in [None, empty] and field.required):
                return None

            raise _NoDictData

        def get_partial_field_value(self, field: Field):
            # INFO - AM - 04/01/2024 - if field is not in the data_dict but in PARTIAL_UPDATE_FIELD_NAME
            # we need to set the default value if existing or raise exception to avoid having default
            # grpc value by mistake
            if field.field_name in self.partial_fields:
                if field.allow_null:
                    return None
                elif field.default not in [None, empty]:
                    return get_default_value(field.default)
                # INFO - AM - 11/03/2024 - Here we set the default value especially for the blank authorized data.
                # We debated about raising a ValidationError but prefered this behavior.
                # Can be changed if it create issue with users
                return self.message.DESCRIPTOR.fields_by_name[field.field_name].default_value
            raise _NoDictData

        def get_cleaned_field_value(
            self,
            field: Field,
        ):
            # INFO - AM - 04/01/2024 - If we are in a partial serializer we only
            # need to have field specified in PARTIAL_UPDATE_FIELD_NAME attribute
            # in the data. Meaning deleting fields that should not be here and not adding
            # None to allow_null field that are not specified
            if self.serializer.partial and field.field_name not in self.partial_fields:
                raise _NoDictData

            if field.field_name in self.base_data:
                return self.base_data[field.field_name]

            try:
                return self.get_partial_field_value(field)
            except _NoDictData:
                pass

            return self.get_nullable_field_value(field)


class ProtoSerializer(BaseProtoSerializer, Serializer):
    pass


class ListProtoSerializer(ListSerializer, BaseProtoSerializer):
    def message_to_data(self, message):
        """
        List of protobuf messages -> List of dicts of python primitive datatypes.
        """

        assert hasattr(
            self.child, "Meta"
        ), f'Class {self.__class__.__name__} missing "Meta" attribute'

        message_list_attr = getattr(
            self.child.Meta, LIST_ATTR_MESSAGE_NAME, DEFAULT_LIST_FIELD_NAME
        )
        # INFO A.Rx. 23/02/2022: allow keeping instance 'message_list_attr' if Meta's is default
        if (
            message_list_attr == DEFAULT_LIST_FIELD_NAME
            and self.message_list_attr != DEFAULT_LIST_FIELD_NAME
        ):
            message_list_attr = self.message_list_attr

        repeated_message = getattr(message, message_list_attr, "")
        if not isinstance(repeated_message, MutableSequence):
            error_message = self.default_error_messages["not_a_list"].format(
                input_type=repeated_message.__class__.__name__
            )
            raise ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: [error_message]}, code="not_a_list"
            )
        ret = []
        for item in repeated_message:
            ret.append(self.child.message_to_data(item))
        return ret

    def data_to_message(self, data):
        """
        List of protobuf messages <- List of dicts of python primitive datatypes.
        """

        assert hasattr(
            self.child, "Meta"
        ), f'Class {self.__class__.__name__} missing "Meta" attribute'
        assert hasattr(
            self.child.Meta, "proto_class_list"
        ), f'Class {self.__class__.__name__} missing "Meta.proto_class_list" attribute'

        if getattr(self.child, "stream", False):
            return [self.child.data_to_message(item) for item in data]
        else:
            response = self.child.Meta.proto_class_list()
            response_result_attr = getattr(
                self.child.Meta, LIST_ATTR_MESSAGE_NAME, DEFAULT_LIST_FIELD_NAME
            )
            getattr(response, response_result_attr).extend(
                [self.child.data_to_message(item) for item in data]
            )
            return response


class PropertyReadOnlyField(ReadOnlyField, ProtoFieldConvertible):
    def __init__(self, **kwargs):
        self.property_field: property = kwargs.pop("property_field")
        super().__init__(**kwargs)

    def to_proto_field(
        self, proto_field_class: ProtoField = ProtoField, **kwargs
    ) -> ProtoField:
        method = self.property_field.fget
        serializer: ModelSerializer = self.parent

        try:
            field_type, cardinality = proto_field_class._extract_method_info(method)
        except FutureAnnotationError as e:
            raise ProtoRegistrationError(
                "You have likely used a PEP 604 return type hint in "
                f"{serializer.Meta.model}.{self.field_name}. "
                "Using `__future__.annotations` is not supported by the field inspection "
                "mechanism. Please use the `typing` module instead."
            ) from e
        except NoReturnTypeError as e:
            raise ProtoRegistrationError(
                f"You are trying to register the serializer {serializer.__class__.__name__} "
                f"with a property on the model {serializer.Meta.model}.{self.field_name}. "
                f"But this property doesn't have a return annotation. "
                "Please look at the example: https://github.com/socotecio/django-socio-grpc/"
                "blob/master/django_socio_grpc/tests/fakeapp/serializers.py#L111. "
                "And the python doc: https://docs.python.org/3.8/library/typing.html"
            ) from e
        except ListWithMultipleArgsError as e:
            raise ProtoRegistrationError(
                f"You are trying to register the serializer {serializer.__class__.__name__} "
                f"with a property on the model {serializer.Meta.model}.{self.field_name}. "
                "But the property return type is a List with multiple arguments. DSG only supports one."
            ) from e
        except UnknownTypeError as e:
            raise ProtoRegistrationError(
                f"You are trying to register the serializer {serializer.__class__.__name__} "
                f"with a property on the model {serializer.Meta.model}.{self.field_name}. "
                f"But the property return type ({e.return_type}) is not supported by DSG."
            ) from e

        return proto_field_class(
            name=self.field_name,
            field_type=field_type,
            cardinality=cardinality,
        )


class ModelProtoSerializer(ProtoSerializer, ModelSerializer):
    def build_property_field(self, field_name, model_class):
        """
        To generate the correct types of a model property field we have
        to know that the field is a property, by default the field is only
        a ReadOnlyField. PropertyReadOnlyField has the property information
        we need.
        """
        field_class = PropertyReadOnlyField
        field_kwargs = {"property_field": getattr(model_class, field_name)}

        return field_class, field_kwargs

    class _MessageToData(ProtoSerializer._MessageToData):
        """
        ModelProtoSerializer._MessageToData should handle update/create differentially
        and handle the default values of model fields.
        """

        @property
        def model(self):
            return self.serializer.Meta.model

        @property
        def updating(self):
            return get_model_pk(self.model).name in self.base_data

        def get_nullable_field_value(
            self,
            field: Field,
        ):
            value = super().get_nullable_field_value(field)
            if self.updating or field.default not in [None, empty]:
                return value
            try:
                deferred_attribute = getattr(self.model, field.field_name)
                if deferred_attribute.field.default != NOT_PROVIDED:
                    return get_default_value(deferred_attribute.field.default)
            except AttributeError:
                return value


class BinaryField(Field):
    default_error_messages = {
        "max_length": _("Ensure this field has no more than {max_length} characters."),
    }

    def __init__(self, **kwargs):
        self.max_length = kwargs.pop("max_length", None)
        super().__init__(**kwargs)
        if self.max_length is not None:
            message = lazy_format(
                self.error_messages["max_length"], max_length=self.max_length
            )
            self.validators.append(MaxLengthValidator(self.max_length, message=message))

    def to_internal_value(self, data):
        # INFO - AM - 03/02/2022 - For now as we do not know what to do because we miss some use cas we just return the data and let the user to whatever he want
        # Some idea is to pass extra kwargs to convert string into bytes. We can use base64 or directly bytes(value)
        return data

    def to_representation(self, value):
        # INFO - AM - 03/02/2022 - For now as we do not know what to do because we miss some use cas we just return the value and let the user to whatever he want
        # Some idea is to pass extra kwargs to convert bytes into string. We can use base64 or unicode(value)
        return value


class SlugRelatedConvertedField(SlugRelatedField):
    """
    A read-write field that represents the target of the relationship
    by a unique 'slug' attribute. And support a type converter to be sure that the field is in the correct protobuf type
    """

    def __init__(self, convert_type=None, **kwargs):
        assert (
            callable(convert_type) is True
        ), "The `convert_type` argument need to be callable."
        self.convert_type = convert_type
        super().__init__(**kwargs)

    def to_representation(self, obj):
        slug_value = super().to_representation(obj)
        if slug_value is not None and self.convert_type:
            return self.convert_type(slug_value)
        return slug_value
