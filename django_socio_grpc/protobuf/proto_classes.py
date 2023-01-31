import logging
from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import Enum
from textwrap import indent
from typing import (
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

from django_socio_grpc.utils.constants import REQUEST_SUFFIX, RESPONSE_SUFFIX
from django_socio_grpc.utils.model_meta import get_model_pk
from django_socio_grpc.utils.tools import rreplace

from .exceptions import ProtoRegistrationError
from .typing import FieldDict

logger = logging.getLogger("django_socio_grpc")


class FieldCardinality(Enum):
    NONE = ""
    OPTIONAL = "optional"
    REPEATED = "repeated"
    # TODO: ONEOF = "oneof"
    # TODO: MAP = "map"


class ProtoComment:
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
    name: str
    # field_type can temporarily be a Serializer class, which will have to
    # be replaced by a ProtoMessage
    field_type: Union[str, "ProtoMessage", Type[serializers.BaseSerializer]]
    cardinality: FieldCardinality = FieldCardinality.NONE
    comments: Optional[List[str]] = None
    index: int = 0

    @property
    def field_type_str(self) -> str:
        if self.has_serializer_field:
            raise ProtoRegistrationError(
                f"Serializer {self.field_type} was not registered as ProtoMessage"
            )
        if isinstance(self.field_type, str):
            return self.field_type
        return self.field_type.name

    @property
    def field_line(self) -> str:
        values = [self.field_type_str, self.name, f"= {self.index};"]
        if self.cardinality != FieldCardinality.NONE:
            values.insert(0, self.cardinality.value)
        return " ".join(values)

    @property
    def has_serializer_field(self) -> bool:
        return isinstance(self.field_type, type) and issubclass(
            self.field_type, serializers.BaseSerializer
        )

    @classmethod
    def _get_cardinality(self, field: serializers.Field):
        return FieldCardinality.OPTIONAL if field.allow_null else FieldCardinality.NONE

    @classmethod
    def from_field_dict(cls, field_dict: FieldDict) -> "ProtoField":
        cardinality = FieldCardinality.NONE
        field_type = field_dict["type"]
        type_parts = field_type.split(" ")
        if len(type_parts) == 2:
            try:
                cardinality = FieldCardinality(type_parts[0])
            except ValueError as exc:
                raise ProtoRegistrationError(
                    f"Unknown cardinality {type_parts[0]} for field {field_dict['name']}"
                ) from exc
            field_type = type_parts[1]
        elif len(type_parts) > 2:
            raise ProtoRegistrationError(
                f"Unknown field type {field_type} for field {field_dict['name']}"
            )

        if comments := field_dict.get("comment"):
            if isinstance(comments, str):
                comments = [comments]

        if field_type in PRIMITIVE_TYPES:
            field_type = PRIMITIVE_TYPES[field_type]

        return cls(
            name=field_dict["name"],
            field_type=field_type,
            cardinality=cardinality,
            comments=comments,
        )

    @classmethod
    def from_field(cls, field: serializers.Field) -> "ProtoField":

        cardinality = cls._get_cardinality(field)

        if hasattr(field, "proto_type"):
            pass

        elif isinstance(field, serializers.SerializerMethodField):
            return cls._from_serializer_method_field(field)

        elif isinstance(field, serializers.ManyRelatedField):
            proto_field = cls._from_related_field(
                field.child_relation, source_attrs=field.source_attrs
            )
            proto_field.name = field.field_name
            proto_field.cardinality = FieldCardinality.REPEATED
            return proto_field

        elif isinstance(field, serializers.RelatedField):
            return cls._from_related_field(field)

        if isinstance(field, serializers.ChoiceField):
            choices = field.choices
            first_type = type(list(choices.keys())[0])
            if all(isinstance(choice, first_type) for choice in choices.keys()):
                field_type = TYPING_TO_PROTO_TYPES.get(first_type, "string")
            else:
                field_type = "string"

        else:
            field_type = get_proto_type(field)

        if isinstance(field, serializers.ListField):
            cardinality = FieldCardinality.REPEATED
            field_type = get_proto_type(field.child)

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
    def from_serializer(cls, field: serializers.Serializer) -> "ProtoField":
        cardinality = cls._get_cardinality(field)
        field_type = field.__class__
        if getattr(field, "many", False):
            cardinality = FieldCardinality.REPEATED
            field_type = field.child.__class__

        return cls(
            name=field.field_name,
            field_type=field_type,
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
        if get_origin(return_type) is list:
            cardinality = FieldCardinality.REPEATED
            args = get_args(return_type)
            if len(args) > 1:
                raise ProtoRegistrationError(
                    f"You are trying to register the serializer {field.parent.__class__.__name__} "
                    f"with a SerializerMethodField on the field {field.field_name}. But the method "
                    "associated returns a List type with multiple arguments. DSG only supports one."
                )

            # INFO - LG - 03/01/2023 - By default a list is a list of str
            (return_type,) = args or [str]

        if (proto_type := TYPING_TO_PROTO_TYPES.get(return_type)) or issubclass(
            return_type, serializers.BaseSerializer
        ):
            field_type = proto_type or return_type
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

    def __str__(self) -> str:
        comms = [f"// {c}" for c in self.comments or []]
        return "\n".join(comms + [self.field_line])

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"


@dataclass
class ProtoMessage:
    base_name: str
    fields: List["ProtoField"] = dataclass_field(default_factory=list)
    comments: Optional[List[str]] = None
    serializer: Optional[serializers.BaseSerializer] = None
    imported_from: Optional[str] = None
    suffixable: bool = True
    prefixable: bool = True

    prefix: str = ""
    suffix: ClassVar = ""

    def __post_init__(self) -> None:
        for field in self.fields:
            if field.has_serializer_field:
                field.field_type = self.from_serializer(field.field_type)

    def get_all_messages(self) -> Dict[str, "ProtoMessage"]:
        messages = {self.name: self}
        for field in self.fields:
            if isinstance(field.field_type, ProtoMessage):
                messages.update(field.field_type.get_all_messages())
        return messages

    def set_indices(self, indices: Dict[int, str]) -> None:
        curr_idx = 0
        if indices:
            indices = {idx: field for idx, field in indices.items() if field in self}
            for idx, field in indices.items():
                self[field].index = idx

            curr_idx = max(indices.keys())

        for field in self.fields:
            if not field.index:
                curr_idx += 1
                field.index = curr_idx

    def append_name(self) -> str:
        name = self.base_name
        if self.suffixable:
            name = f"{self.base_name}{self.suffix}"
        if self.prefixable:
            name = f"{self.prefix}{name}"
        return name

    @property
    def name(self) -> str:
        if self.imported_from:
            return self.base_name
        return self.append_name()

    @classmethod
    def get_base_name_from_serializer(
        cls, serializer: Type[serializers.BaseSerializer]
    ) -> str:
        name = serializer.__name__
        if "ProtoSerializer" in name:
            name = rreplace(name, "ProtoSerializer", "", 1)
        elif "Serializer" in name:
            name = rreplace(name, "Serializer", "", 1)

        return name

    @classmethod
    def create(
        cls,
        value: Optional[Union[Type[serializers.BaseSerializer], List[FieldDict], str]],
        base_name: str,
        appendable_name: bool,
        prefix: str = "",
    ) -> Union["ProtoMessage", str]:
        if isinstance(value, type) and issubclass(value, serializers.BaseSerializer):
            return cls.from_serializer(value, name=None if appendable_name else base_name)
        elif isinstance(value, list) or not value:
            return cls.from_field_dicts(
                value, base_name=base_name, appendable_name=appendable_name, prefix=prefix
            )
        elif isinstance(value, str):
            if value in PRIMITIVE_TYPES:
                return PRIMITIVE_TYPES[value]
            return value
        else:
            raise TypeError()

    @classmethod
    def from_field_dicts(
        cls,
        fields: List[FieldDict],
        base_name: str,
        appendable_name: bool = True,
        prefix: str = "",
    ) -> "ProtoMessage":
        if not fields and appendable_name:
            return EmptyMessage

        return cls(
            base_name=base_name,
            fields=[ProtoField.from_field_dict(field) for field in fields],
            suffixable=appendable_name,
            prefixable=appendable_name,
            prefix=prefix,
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

                if cls.skip_field(field, pk_name):
                    continue

                if isinstance(field, serializers.BaseSerializer):
                    fields.append(ProtoField.from_serializer(field))
                else:
                    fields.append(ProtoField.from_field(field))
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
            base_name=name or cls.get_base_name_from_serializer(serializer),
            fields=fields,
            comments=comments,
            serializer=serializer,
            suffixable=not name,
            prefixable=False,
        )

        return proto_message

    @classmethod
    def skip_field(
        cls, field: Union[serializers.Field, serializers.BaseSerializer], pk_name: str
    ) -> bool:
        # INFO - AM - 21/01/2022 - HiddenField are not used in api so not showed in protobuf file
        return isinstance(field, HiddenField)

    @classmethod
    def as_list_message(
        cls,
        base_message: "ProtoMessage",
        base_name: Optional[str] = None,
        list_field_name: Optional[str] = None,
    ) -> "ProtoMessage":

        if list_field_name is None:
            try:
                list_field_name = base_message.serializer.Meta.message_list_attr
            except AttributeError:
                list_field_name = "results"

        fields = [
            ProtoField(
                name=list_field_name,
                field_type=base_message,
                cardinality=FieldCardinality.REPEATED,
            ),
            ProtoField(
                name="count",
                field_type="int32",
            ),
        ]

        list_message = cls(
            base_name=f"{base_name or rreplace(base_message.base_name, cls.suffix, '', 1)}List",
            fields=fields,
            prefixable=base_message.prefixable,
            prefix=base_message.prefix,
        )

        if not base_message.serializer:
            list_message.comments = base_message.comments
            base_message.comments = None

        return list_message

    def __str__(self) -> str:
        # INFO - LG - 06/01/2023 - Imported messages are not displayed
        if self.imported_from:
            return ""
        fields = "\n".join(str(f) for f in sorted(self.fields, key=lambda x: x.index))
        fields = indent(fields, "    ")
        if fields:
            fields += "\n"
        comms = [f"// {c}" for c in self.comments or []]

        return "\n".join(comms + [f"message {self.name} {{\n{fields}}}"])

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"

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
    base_name="google.protobuf.Empty",
    fields=[],
    imported_from="google/protobuf/empty.proto",
)

StructMessage = ProtoMessage(
    base_name="google.protobuf.Struct",
    fields=[],
    imported_from="google/protobuf/struct.proto",
)


@dataclass
class ProtoRpc:
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

    def __str__(self) -> str:
        rpcs_str = "\n".join(str(rpc) for rpc in sorted(self.rpcs, key=lambda x: x.name))
        return f"service {self.name} {{\n{indent(rpcs_str,'    ')}\n}}"


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

    proto_type = None
    field_mro = field.__class__.mro()
    while proto_type is None:
        proto_type = FIELDS_TO_PROTO_TYPES.get(field.__class__.__name__)
        try:
            field = field_mro.pop()
        except IndexError:
            break
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
