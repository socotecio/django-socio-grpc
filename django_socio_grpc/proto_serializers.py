from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext as _
from google.protobuf.pyext._message import RepeatedCompositeContainer
from rest_framework.exceptions import ValidationError
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
from django_socio_grpc.utils.constants import DEFAULT_LIST_FIELD_NAME, LIST_ATTR_MESSAGE_NAME

LIST_PROTO_SERIALIZER_KWARGS = (*LIST_SERIALIZER_KWARGS, LIST_ATTR_MESSAGE_NAME, "message")


class BaseProtoSerializer(BaseSerializer):
    def __init__(self, *args, **kwargs):
        message = kwargs.pop("message", None)
        self.stream = kwargs.pop("stream", None)
        self.message_list_attr = kwargs.pop(LIST_ATTR_MESSAGE_NAME, DEFAULT_LIST_FIELD_NAME)
        if message is not None:
            self.initial_message = message
            kwargs["data"] = self.message_to_data(message)
        super().__init__(*args, **kwargs)

    def message_to_data(self, message):
        """Protobuf message -> Dict of python primitive datatypes."""
        return message_to_dict(message)

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
        if not isinstance(repeated_message, RepeatedCompositeContainer):
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
        slug_value = getattr(obj, self.slug_field)
        if self.convert_type:
            return self.convert_type(slug_value)
        return slug_value
