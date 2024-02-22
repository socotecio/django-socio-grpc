import logging
import traceback
from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import (
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from rest_framework import serializers
from rest_framework.fields import HiddenField
from rest_framework.utils.model_meta import RelationInfo, get_field_info

from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.utils.constants import REQUEST_SUFFIX, RESPONSE_SUFFIX
from django_socio_grpc.utils.debug import ProtoGeneratorPrintHelper
from django_socio_grpc.utils.model_meta import get_model_pk

from .exceptions import ProtoRegistrationError
from .typing import FieldCardinality, FieldDict

logger = logging.getLogger("django_socio_grpc.generation")


class ProtoComment:
    """
    This class is used to represent a comment in a proto file.
    It allows adding a comment in a serializer field help_text.
    """

    def __init__(self, comments):
        if isinstance(comments, str):
            # INFO - AM - 20/07/2022 - if only pass a string we do not want to display a empty comment
            if not comments:
                self.comments = []
            else:
                self.comments = [comments]
        elif isinstance(comments, Iterable):
            self.comments = comments

    def __iter__(self):
        return iter(self.comments)

    def __bool__(self):
        return len(self.comments) != 0


@dataclass
class ProtoField:
    """
    Represents a field in a proto message.

    ```
    {comments}
    {cardinality} {field_type} {name} = {index};
    ```
    """

    name: str
    field_type: Union[str, "ProtoMessage"]
    cardinality: FieldCardinality = FieldCardinality.NONE
    comments: Optional[List[str]] = None
    index: int = 0

    @property
    def field_type_str(self) -> str:
        if isinstance(self.field_type, str):
            return self.field_type
        return self.field_type.name

    @property
    def field_line(self) -> str:
        values = [self.field_type_str, self.name, f"= {self.index};"]
        if self.cardinality != FieldCardinality.NONE:
            values.insert(0, self.cardinality)
        return " ".join(values)

    @classmethod
    def _get_cardinality(self, field: serializers.Field):
        return FieldCardinality.OPTIONAL if field.allow_null else FieldCardinality.NONE

    @classmethod
    def from_field_dict(cls, field_dict: FieldDict) -> "ProtoField":
        cardinality = field_dict.get("cardinality", FieldCardinality.NONE)
        name = field_dict["name"]
        field_type = field_dict["type"]
        type_parts = field_type.split(" ")
        if len(type_parts) == 2:
            if cardinality:
                raise ProtoRegistrationError(
                    f"Cardinality `{cardinality}` is set in both `cardinality` and `type` field. ({name})"
                )
            cardinality, field_type = type_parts

            stack = traceback.StackSummary.extract(
                traceback.walk_stack(None), capture_locals=True
            )
            for frame in stack:
                if frame.name == "make_proto_rpc":
                    logger.warning(
                        f"Setting cardinality `{cardinality}` in `type` field is deprecated. ({name})"
                        " Please set it in the `cardinality` key instead.\n"
                        f"`{frame.locals['self']}`"
                    )
                    break

        elif len(type_parts) > 2:
            raise ProtoRegistrationError(
                f"Unknown field type `{field_type}` for field `{name}`"
            )
        if cardinality not in FieldCardinality.__members__.values():
            raise ProtoRegistrationError(
                f"Unknown cardinality `{cardinality}` for field `{name}`"
            )

        if comments := field_dict.get("comment"):
            if isinstance(comments, str):
                comments = [comments]

        if field_type in PRIMITIVE_TYPES:
            field_type = PRIMITIVE_TYPES[field_type]

        return cls(
            name=name,
            field_type=field_type,
            cardinality=cardinality,
            comments=comments,
        )

    @classmethod
    def from_field(
        cls,
        field: serializers.Field,
        to_message: Callable = None,
        parent_serializer: serializers.Serializer = None,
        name_if_recursive: str = None,
    ) -> "ProtoField":
        """
        to_message, parent_serializer, name_if_recursive only used if field is ListSerializer with a child being a Serializer
        """
        cardinality = cls._get_cardinality(field)

        if isinstance(field, serializers.SerializerMethodField):
            ProtoGeneratorPrintHelper.print(f"{field.field_name} is SerializerMethodField")
            return cls._from_serializer_method_field(field)

        elif isinstance(field, serializers.ManyRelatedField):
            ProtoGeneratorPrintHelper.print(f"{field.field_name} is ManyRelatedField")
            proto_field = cls._from_related_field(
                field.child_relation, source_attrs=field.source_attrs
            )
            proto_field.name = field.field_name
            proto_field.cardinality = FieldCardinality.REPEATED
            return proto_field

        elif isinstance(field, serializers.RelatedField):
            ProtoGeneratorPrintHelper.print(f"{field.field_name} is RelatedField")
            return cls._from_related_field(field)

        if isinstance(field, serializers.ListField):
            ProtoGeneratorPrintHelper.print(f"{field.field_name} is ListField")
            cardinality = FieldCardinality.REPEATED
            if isinstance(field.child, serializers.BaseSerializer):
                ProtoGeneratorPrintHelper.print(
                    f"{field.field_name} ListField child is a serializer"
                )
                proto_field = cls.from_serializer(
                    field.child, to_message, parent_serializer, name_if_recursive
                )
                field_type = proto_field.field_type
            else:
                ProtoGeneratorPrintHelper.print(
                    f"{field.field_name} ListField child is a simple field"
                )
                field_type = get_proto_type(field.child)
        else:
            ProtoGeneratorPrintHelper.print(f"{field.field_name} is simple type")
            field_type = get_proto_type(field)

        comments = None
        if isinstance(help_text := getattr(field, "help_text", None), ProtoComment):
            comments = help_text.comments

        return cls(
            name=field.field_name,
            field_type=field_type,
            cardinality=cardinality,
            comments=comments,
        )

    @classmethod
    def from_serializer(
        cls,
        field: serializers.Serializer,
        to_message: Callable,
        parent_serializer: serializers.Serializer = None,
        name_if_recursive: str = None,
    ) -> "ProtoField":
        """
        Create a ProtoField from a Serializer, which will be converted to a ProtoMessage with `to_message`
        """
        cardinality = cls._get_cardinality(field)
        serializer_class = field.__class__
        if getattr(field, "many", False):
            cardinality = FieldCardinality.REPEATED
            serializer_class = field.child.__class__
        # INFO - AM - 05/05/2023 - if serializer_class == parent_serializer that mean we are in a recursive serializer and so we need to have a specific behavior to avoid code recursion with the to_message function
        if parent_serializer and serializer_class == parent_serializer:
            if not name_if_recursive:
                raise ProtoRegistrationError(
                    "You are trying to define a recursive serializer without a specific name"
                )
            return cls(
                name=field.field_name,
                field_type=name_if_recursive,
                cardinality=cardinality,
            )

        return cls(
            name=field.field_name,
            field_type=to_message(serializer_class),
            cardinality=cardinality,
        )

    @classmethod
    def _from_related_field(
        cls, field: serializers.RelatedField, source_attrs: Optional[List[str]] = None
    ) -> "ProtoField":
        serializer: serializers.Serializer = field.root

        cardinality = cls._get_cardinality(field)

        if not source_attrs:
            source_attrs = field.source_attrs
        try:
            model: models.Model = serializer.Meta.model
        except AttributeError:
            source_attrs = []
            try:
                model = field.queryset.model
            except AttributeError:
                raise ProtoRegistrationError(
                    f"No Model in serializer {serializer.__class__.__name__} "
                    f"related to field {field.field_name}"
                )

        for source in source_attrs:
            relationships: OrderedDict[str, RelationInfo] = get_field_info(model).relations
            if not (relation := relationships.get(source)):
                break
            model = relation.related_model

        if isinstance(field, serializers.PrimaryKeyRelatedField):
            field_type = get_proto_type(
                field.pk_field if field.pk_field else get_model_pk(model)
            )

        elif isinstance(field, serializers.SlugRelatedField):
            try:
                slug_field = model._meta.get_field(field.slug_field)
            except FieldDoesNotExist:
                raise ProtoRegistrationError(
                    f"Related Model {model} has no field {field.slug_field} ({serializer.__class__})"
                )
            field_type = get_proto_type(slug_field)

        # INFO - LG - 20/12/2022 - Other RelatedField need to implement their own proto_type else default is string
        else:
            field_type = get_proto_type(field)

        return cls(
            name=field.field_name,
            field_type=field_type,
            cardinality=cardinality,
        )

    @classmethod
    def _from_serializer_method_field(
        cls, field: serializers.SerializerMethodField
    ) -> "ProtoField":
        cardinality = cls._get_cardinality(field)
        method_name = field.method_name

        try:
            method = getattr(field.parent, method_name)
        except AttributeError:
            raise ProtoRegistrationError(
                f"Method {method_name} not found in {field.parent.__class__.__name__}"
            )

        if not (return_type := get_type_hints(method).get("return")):
            raise ProtoRegistrationError(
                f"You are trying to register the serializer {field.parent.__class__.__name__} "
                f"with a SerializerMethodField on the field {field.field_name}. "
                f"But the method {method_name} doesn't have a return annotations. "
                "Please look at the example: https://github.com/socotecio/django-socio-grpc/"
                "blob/master/django_socio_grpc/tests/fakeapp/serializers.py#L111. "
                "And the python doc: https://docs.python.org/3.8/library/typing.html"
            )

        # https://docs.python.org/3/library/typing.html#typing.get_origin
        args = get_args(return_type)
        if get_origin(return_type) is list:
            cardinality = FieldCardinality.REPEATED
            if len(args) > 1:
                raise ProtoRegistrationError(
                    f"You are trying to register the serializer {field.parent.__class__.__name__} "
                    f"with a SerializerMethodField on the field {field.field_name}. But the method "
                    "associated returns a List type with multiple arguments. DSG only supports one."
                )

            # INFO - LG - 03/01/2023 - By default a list is a list of str
            (return_type,) = args or [str]

        # When a method returns an Optional, it is considered as an Union of the return_type with None
        elif get_origin(return_type) is Union and len(args) == 2 and type(None) in args:
            cardinality = FieldCardinality.OPTIONAL
            (return_type,) = (t for t in args if not issubclass(t, type(None)))

        if proto_type := TYPING_TO_PROTO_TYPES.get(return_type):
            field_type = proto_type
        elif isinstance(return_type, type) and issubclass(
            return_type, serializers.BaseSerializer
        ):
            field_type = ResponseProtoMessage.from_serializer(return_type)

        else:
            raise ProtoRegistrationError(
                f"You are trying to register the serializer {field.parent.__class__.__name__} "
                f"with a SerializerMethodField on the field {field.field_name}. But the method "
                "associated returns a type not supported by DSG."
            )

        return cls(
            name=field.field_name,
            field_type=field_type,
            cardinality=cardinality,
        )


# TODO Frozen
@dataclass
class ProtoMessage:
    """
    Represents a proto message with its fields and comments

    ```
    {comments}
    message {name} {
        [{fields}]
    }
    """

    name: str
    fields: List["ProtoField"] = dataclass_field(default_factory=list)
    comments: Optional[List[str]] = None
    serializer: Optional[serializers.BaseSerializer] = None
    imported_from: Optional[str] = None

    def get_all_messages(self) -> Dict[str, "ProtoMessage"]:
        messages = {self.name: self}
        for field in self.fields:
            # Retrieve all messages from nested messages
            if isinstance(field.field_type, ProtoMessage):
                messages.update(field.field_type.get_all_messages())
        return messages

    def set_indices(self, indices: Dict[int, str]) -> None:
        """
        Set the field index that is writed in the proto file while trying to keep the same order that the one passed in the incides parameter
        :param indices: dictionnary mapping the field number with the field name that we want to keep order too. Usually it come from the lecture of the previous proto file before it is generated again
        """
        curr_idx = 0
        if indices:
            # INFO - AM - 14/04/2023 - We filter the indices to only keep the ones we still have in self.fields[name]. See __getitem__ to understand why self is self.fields[name].
            indices = {idx: field for idx, field in indices.items() if field in self}
            for idx, field in indices.items():
                self[field].index = idx

            # INFO - AM - 14/04/2023 - Sometimes all the fields have changed and so max(indices.keys()) is not working
            if indices.keys():
                curr_idx = max(indices.keys())

        # INFO - AM - 14/04/2023 - We set index for all the fiels of the current ProtoMessage taht was not already in the previous ProtoMessage. Note that it is set only if index is not set.
        for field in self.fields:
            if not field.index:
                curr_idx += 1
                field.index = curr_idx

    @classmethod
    def create(
        cls,
        value: Optional[Union[Type[serializers.BaseSerializer], List[FieldDict], str]],
        name: str,
    ) -> Union["ProtoMessage", str]:
        if isinstance(value, type) and issubclass(value, serializers.BaseSerializer):
            ProtoGeneratorPrintHelper.print("Message from serializer")
            proto_message = cls.from_serializer(value, name=name)
            return proto_message
        elif isinstance(value, str):
            ProtoGeneratorPrintHelper.print("Message from string")
            return PRIMITIVE_TYPES.get(value, value)
        # Empty value means an EmptyMessage, this is handled in the from_field_dicts
        elif isinstance(value, list) or not value:
            ProtoGeneratorPrintHelper.print("Message from field dicts")
            proto_message = cls.from_field_dicts(value, name=name)
            return proto_message
        else:
            raise TypeError()

    @classmethod
    def from_field_dicts(
        cls,
        fields: List[FieldDict],
        name: str,
    ) -> "ProtoMessage":
        if fields is None:
            fields = []
        return cls(
            name=name,
            fields=[ProtoField.from_field_dict(field) for field in fields],
        )

    @classmethod
    def from_serializer(
        cls,
        serializer: Type[serializers.BaseSerializer],
        name: Optional[str] = None,
    ) -> "ProtoMessage":
        meta = getattr(serializer, "Meta", None)
        pk_name = None
        if getattr(meta, "model", None):
            pk_name = get_model_pk(meta.model).name
        comments = getattr(meta, "proto_comment", None)
        if isinstance(comments, ProtoComment):
            comments = comments.comments
        elif isinstance(comments, str):
            comments = [comments]

        fields = []

        # INFO - LG - 30/12/2022 - The Serializer needs to implement either
        # fields or to_proto_message
        if hasattr(serializer, "fields"):
            for field in serializer().fields.values():
                field: Union[serializers.Field, serializers.BaseSerializer]

                ProtoGeneratorPrintHelper.set_field_name(field.field_name)

                if cls.skip_field(field, pk_name):
                    ProtoGeneratorPrintHelper.print(f"field {field.field_name} is skipped")
                    continue

                if isinstance(field, serializers.BaseSerializer):
                    ProtoGeneratorPrintHelper.print(f"field {field.field_name} is serializer")
                    fields.append(
                        ProtoField.from_serializer(
                            field,
                            cls.from_serializer,
                            parent_serializer=serializer,
                            name_if_recursive=name
                            or MessageNameConstructor.get_base_name_from_serializer_with_suffix(
                                serializer, getattr(cls, "suffix", "")
                            ),
                        )
                    )
                else:
                    ProtoGeneratorPrintHelper.print(
                        f"field {field.field_name} is simple field"
                    )
                    fields.append(
                        ProtoField.from_field(
                            field,
                            cls.from_serializer,
                            parent_serializer=serializer,
                            name_if_recursive=name
                            or MessageNameConstructor.get_base_name_from_serializer_with_suffix(
                                serializer, getattr(cls, "suffix", "")
                            ),
                        )
                    )
        # INFO - AM - 07/01/2022 - else the serializer needs to implement to_proto_message
        elif hasattr(serializer, "to_proto_message"):
            fields = [
                ProtoField.from_field_dict(dict_field)
                for dict_field in serializer().to_proto_message()
            ]
        else:
            raise ProtoRegistrationError(
                f"Serializer {serializer.__name__} needs to either implement "
                "`fields` or `to_proto_message`"
            )

        proto_message = cls(
            name=name
            or MessageNameConstructor.get_base_name_from_serializer_with_suffix(
                serializer, getattr(cls, "suffix", "")
            ),
            fields=fields,
            comments=comments,
            serializer=serializer,
        )

        return proto_message

    @classmethod
    def skip_field(
        cls, field: Union[serializers.Field, serializers.BaseSerializer], pk_name: str
    ) -> bool:
        # INFO - AM - 21/01/2022 - HiddenField are not used in api so not showed in protobuf file
        return isinstance(field, HiddenField)

    def __getitem__(self, key: str) -> "ProtoField":
        for field in self.fields:
            if field.name == key:
                return field
        raise KeyError(f"Field {key} not found in {self.name}")

    def __contains__(self, key: str) -> bool:
        try:
            self[key]
            return True
        except KeyError:
            return False


class RequestProtoMessage(ProtoMessage):
    suffix: ClassVar = REQUEST_SUFFIX

    @classmethod
    def skip_field(
        cls, field: Union[serializers.Field, serializers.BaseSerializer], pk_name: str
    ) -> bool:
        """
        Skip fields that are read_only on Request
        """
        return (
            super().skip_field(field, pk_name)
            or field.field_name != pk_name
            and field.read_only
        )


class ResponseProtoMessage(ProtoMessage):
    suffix: ClassVar = RESPONSE_SUFFIX

    @classmethod
    def skip_field(
        cls, field: Union[serializers.Field, serializers.BaseSerializer], pk_name: str
    ) -> bool:
        """
        Skip fields that are write_only on Response
        """
        return (
            super().skip_field(field, pk_name)
            or field.field_name != pk_name
            and field.write_only
        )


EmptyMessage = ProtoMessage(
    name="google.protobuf.Empty",
    fields=[],
    imported_from="google/protobuf/empty.proto",
)

StructMessage = ProtoMessage(
    name="google.protobuf.Struct",
    fields=[],
    imported_from="google/protobuf/struct.proto",
)


@dataclass
class ProtoRpc:
    """
    Represent a RPC method in a service

    ```
    rpc {name}({request_stream?} {request.name}) returns ({response_stream?} {response.name}) {}
    ```
    """

    name: str
    request: Union[ProtoMessage, str]
    response: Union[ProtoMessage, str]
    request_stream: bool = False
    response_stream: bool = False

    @property
    def request_name(self) -> str:
        return self.request.name if isinstance(self.request, ProtoMessage) else self.request

    @property
    def response_name(self) -> str:
        return self.response.name if isinstance(self.response, ProtoMessage) else self.response

    def get_all_messages(self) -> Dict[str, ProtoMessage]:
        messages = {}
        if isinstance(self.request, ProtoMessage):
            messages.update(self.request.get_all_messages())
        if isinstance(self.response, ProtoMessage):
            messages.update(self.response.get_all_messages())
        return messages


@dataclass
class ProtoService:
    """
    Represents a service in a proto file

    ```
    service {name} {
        [{rpcs}]
    }
    ```
    """

    name: str
    rpcs: List[ProtoRpc] = dataclass_field(default_factory=list)

    def add_rpc(self, rpc: ProtoRpc):
        for existing_rpc in self.rpcs:
            if existing_rpc.name == rpc.name:
                raise ProtoRegistrationError(
                    f"RPC {rpc.name} already exists in service {self.name}"
                )
        self.rpcs.append(rpc)

    def get_all_messages(self) -> Dict[str, ProtoMessage]:
        messages = {}
        for rpc in self.rpcs:
            messages.update(rpc.get_all_messages())
        return messages


def get_proto_type(
    field: Union[models.Field, serializers.Field],
    default="string",
) -> str:
    """
    Return the proto type of a field, fields can either implement a `proto_type`
    attribute or be a subclass of a known field type.
    """
    if hasattr(field, "proto_type"):
        return field.proto_type

    if isinstance(field, serializers.ModelField):
        return get_proto_type(field.model_field)

    # ChoiceFields need to look into the choices to determine the type
    if isinstance(field, serializers.ChoiceField):
        choices = field.choices
        first_type = type(list(choices.keys())[0])
        if all(isinstance(choice, first_type) for choice in choices.keys()):
            return TYPING_TO_PROTO_TYPES.get(first_type, "string")

    proto_type = None
    field_mro = field.__class__.mro()
    while proto_type is None:
        try:
            parent_class_name = field_mro.pop(0).__name__
        except IndexError:
            break
        proto_type = FIELDS_TO_PROTO_TYPES.get(parent_class_name)
    return proto_type or default


# TODO : Find a way to use `ModelSerializer.serializer_field_mapping` instead of this
# (not usable as it is because of int64)
FIELDS_TO_PROTO_TYPES = {
    # Numeric
    models.IntegerField.__name__: "int32",
    models.AutoField.__name__: "int32",
    models.BigAutoField.__name__: "int64",
    models.SmallIntegerField.__name__: "int32",
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
    # Structs
    "JSONField": StructMessage,
    "DictField": StructMessage,
    # Other
    models.BinaryField.__name__: "bytes",
    "PositiveBigIntegerField": "int64",
    # Default
    models.Field.__name__: "string",
}

PRIMITIVE_TYPES = {
    "google.protobuf.Struct": StructMessage,
    "google.protobuf.Empty": EmptyMessage,
}

TYPING_TO_PROTO_TYPES = {
    int: "int32",
    str: "string",
    bool: "bool",
    float: "float",
    dict: StructMessage,
    bytes: "bytes",
    Dict: StructMessage,
}
