from typing import MutableSequence

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
    Serializer,
)
from rest_framework.settings import api_settings
from rest_framework.utils.formatting import lazy_format

from django_socio_grpc.protobuf.json_format import message_to_dict, parse_dict
from django_socio_grpc.utils.constants import (
    DEFAULT_LIST_FIELD_NAME,
    LIST_ATTR_MESSAGE_NAME,
    PARTIAL_UPDATE_FIELD_NAME,
)

LIST_PROTO_SERIALIZER_KWARGS = (*LIST_SERIALIZER_KWARGS, LIST_ATTR_MESSAGE_NAME, "message")


def get_default_value(field_default):
    if callable(field_default):
        return field_default()
    else:
        return field_default


class BaseProtoSerializer(BaseSerializer):
    def __init__(self, *args, **kwargs):
        message = kwargs.pop("message", None)
        self.stream = kwargs.pop("stream", None)
        self.message_list_attr = kwargs.pop(LIST_ATTR_MESSAGE_NAME, DEFAULT_LIST_FIELD_NAME)
        # INFO - AM - 04/01/2023 - Need to manually define partial before the super().__init__ as it's used in populate_dict_with_none_if_not_required that is used in message_to_data that is call before the super init
        self.partial = kwargs.get("partial", False)
        if message is not None:
            self.initial_message = message
            kwargs["data"] = self.message_to_data(message)
        super().__init__(*args, **kwargs)

    def message_to_data(self, message):
        """Protobuf message -> Dict of python primitive datatypes."""
        data_dict = message_to_dict(message)
        data_dict = self.populate_dict_with_none_if_not_required(data_dict, message=message)
        return data_dict

    def populate_dict_with_none_if_not_required(self, data_dict, message=None):
        """
        This method allow to populate the data dictionary with None for optional field that allow_null and not send in the request.
        It's also allow to deal with partial update correctly.
        This is mandatory for having null value received in request as DRF expect to have None value for field that are required.
        We can't rely only on required True/False as in DSG if a field is required it will have the default value of it's type (empty string for string type) and not None

        When refactoring serializer to only use message we will be able to determine the default value of the field depending of the same logic followed here

        set default value for field except if optional or partial update
        """
        # INFO - AM - 04/01/2024 - If we are in a partial serializer with a message we need to have the PARTIAL_UPDATE_FIELD_NAME in the data_dict. If not we raise an exception
        if self.partial and PARTIAL_UPDATE_FIELD_NAME not in data_dict:
            raise ValidationError(
                {
                    PARTIAL_UPDATE_FIELD_NAME: [
                        f"Field {PARTIAL_UPDATE_FIELD_NAME} not set in message when using partial=True"
                    ]
                },
                code="missing_partial_message_attribute",
            )

        is_update_process = (
            hasattr(self.Meta, "model") and self.Meta.model._meta.pk.name in data_dict
        )
        for field in self.fields.values():
            # INFO - AM - 04/01/2024 - If we are in a partial serializer we only need to have field specified in PARTIAL_UPDATE_FIELD_NAME attribute in the data. Meaning deleting fields that should not be here and not adding None to allow_null field that are not specified
            if self.partial and field.field_name not in data_dict.get(
                PARTIAL_UPDATE_FIELD_NAME, {}
            ):
                if field.field_name in data_dict:
                    del data_dict[field.field_name]
                continue
            # INFO - AM - 04/01/2024 - if field already existing in the data_dict we do not need to do something else
            if field.field_name in data_dict:
                continue

            # INFO - AM - 04/01/2024 - if field is not in the data_dict but in PARTIAL_UPDATE_FIELD_NAME we need to set the default value if existing or raise exception to avoid having default grpc value by mistake
            if self.partial and field.field_name in data_dict.get(
                PARTIAL_UPDATE_FIELD_NAME, {}
            ):
                if field.allow_null:
                    data_dict[field.field_name] = None
                    continue
                if field.default not in [None, empty]:
                    data_dict[field.field_name] = get_default_value(field.default)
                    continue

                # INFO - AM - 11/03/2024 - Here we set the default value especially for the blank authorized data. We debated about raising a ValidaitonError but prefered this behavior. Can be changed if it create issue with users
                data_dict[field.field_name] = message.DESCRIPTOR.fields_by_name[
                    field.field_name
                ].default_value

            if field.allow_null or (field.default in [None, empty] and field.required is True):
                if is_update_process:
                    data_dict[field.field_name] = None
                    continue

                if field.default not in [None, empty]:
                    data_dict[field.field_name] = None
                    continue

                if (
                    hasattr(self, "Meta")
                    and hasattr(self.Meta, "model")
                    and hasattr(self.Meta.model, field.field_name)
                ):
                    deferred_attribute = getattr(self.Meta.model, field.field_name)
                    if deferred_attribute.field.default != NOT_PROVIDED:
                        data_dict[field.field_name] = get_default_value(
                            deferred_attribute.field.default
                        )
                        continue

                data_dict[field.field_name] = None
        return data_dict

    def data_to_message(self, data):
        """Protobuf message <- Dict of python primitive datatypes."""
        assert hasattr(
            self, "Meta"
        ), 'Class {serializer_class} missing "Meta" attribute'.format(
            serializer_class=self.__class__.__name__
        )
        assert hasattr(
            self.Meta, "proto_class"
        ), 'Class {serializer_class} missing "Meta.proto_class" attribute'.format(
            serializer_class=self.__class__.__name__
        )
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


class ModelProtoSerializer(ProtoSerializer, ModelSerializer):
    pass


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
