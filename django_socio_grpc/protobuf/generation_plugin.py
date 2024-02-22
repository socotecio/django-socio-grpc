from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from django_socio_grpc.protobuf.proto_classes import (
    EmptyMessage,
    FieldCardinality,
    ProtoField,
    ProtoMessage,
)
from django_socio_grpc.settings import FilterAndPaginationBehaviorOptions, grpc_settings

if TYPE_CHECKING:
    from django_socio_grpc.services import Service


@dataclass
class BaseGenerationPlugin:
    def check_condition(
        self,
        service: Type["Service"],
        request_message: ProtoMessage,
        response_message: ProtoMessage,
    ) -> bool:
        return True

    def transform_request_message(
        self, service: Type["Service"], proto_message: ProtoMessage
    ) -> ProtoMessage:
        return proto_message

    def transform_response_message(
        self, service: Type["Service"], proto_message: ProtoMessage
    ) -> ProtoMessage:
        return proto_message

    def run_validation_and_transform(
        self,
        service: Type["Service"],
        request_message: ProtoMessage,
        response_message: ProtoMessage,
    ) -> Tuple[ProtoMessage, ProtoMessage]:
        if not self.check_condition(service, request_message, response_message):
            return request_message, response_message

        return self.transform_request_message(
            service, request_message
        ), self.transform_response_message(service, response_message)


@dataclass
class BaseAddFieldRequestGenerationPlugin(BaseGenerationPlugin):
    field_name: ClassVar[str] = None
    field_cardinality: ClassVar[str] = None
    field_type: ClassVar[str] = None

    def __post_init__(self):
        error_message = "You try to instanciate a class that inherit from BaseGenerationPlugin. to do that you need to specify a %s attribute"

        assert self.field_name is not None, error_message.format("field_name")
        assert self.field_cardinality is not None, error_message.format("field_cardinality")
        assert self.field_type is not None, error_message.format("field_type")

    def transform_request_message(self, service: Type["Service"], proto_message: ProtoMessage):
        proto_message.fields.append(
            ProtoField.from_field_dict(
                {
                    "name": self.field_name,
                    "type": self.field_type,
                    "cardinality": self.field_cardinality,
                }
            )
        )
        return proto_message


@dataclass
class FilterGenerationPlugin(BaseAddFieldRequestGenerationPlugin):
    field_name: ClassVar[str] = "_filters"
    field_type: ClassVar[str] = "google.protobuf.Struct"
    field_cardinality: ClassVar[str] = FieldCardinality.OPTIONAL

    def check_condition(
        self,
        service: Type["Service"],
        request_message: ProtoMessage,
        response_message: ProtoMessage,
    ) -> bool:
        # INFO - AM - 20/02/2024 - If service don't support filtering we do not add filter field
        if (
            not hasattr(service, "filter_backends")
            or not service.filter_backends
            and not grpc_settings.DEFAULT_FILTER_BACKENDS
        ):
            return False

        if grpc_settings.FILTER_BEHAVIOR == FilterAndPaginationBehaviorOptions.METADATA_STRICT:
            return False

        return True


@dataclass
class PaginationGenerationPlugin(BaseAddFieldRequestGenerationPlugin):
    field_name: ClassVar[str] = "_pagination"
    field_type: ClassVar[str] = "google.protobuf.Struct"
    field_cardinality: ClassVar[str] = FieldCardinality.OPTIONAL

    def check_condition(
        self,
        service: Type["Service"],
        request_message: ProtoMessage,
        response_message: ProtoMessage,
    ) -> bool:
        # INFO - AM - 20/02/2024 - If service don't support filtering we do not add filter field
        if (
            not hasattr(service, "pagination_class")
            or not service.pagination_class
            and not grpc_settings.DEFAULT_PAGINATION_CLASS
        ):
            return False

        if (
            grpc_settings.PAGINATION_BEHAVIOR
            == FilterAndPaginationBehaviorOptions.METADATA_STRICT
        ):
            return False


@dataclass
class AsListGenerationPlugin(BaseGenerationPlugin):
    list_field_name: str = "results"

    def transform_message_to_list(
        self, service: Type["Service"], proto_message: ProtoMessage
    ) -> ProtoMessage:
        try:
            list_field_name = proto_message.serializer.Meta.message_list_attr
        except AttributeError:
            list_field_name = list_field_name or "results"

        fields = [
            ProtoField(
                name=list_field_name,
                field_type=proto_message,
                cardinality=FieldCardinality.REPEATED,
            ),
        ]

        if hasattr(service, "pagination_class"):
            fields.append(
                ProtoField(
                    name="count",
                    field_type="int32",
                )
            ),

        list_message = ProtoMessage(
            name=f"{proto_message.name}List",
            fields=fields,
        )

        # INFO - AM - If the original proto message is a serializer then we keep the comment at the serializer level. Else we put them at the list level
        if not proto_message.serializer:
            list_message.comments = proto_message.comments
            proto_message.comments = None

        return list_message


@dataclass
class RequestAsListGenerationPlugin(AsListGenerationPlugin):
    def transform_request_message(
        self, service: Type["Service"], proto_message: ProtoMessage
    ) -> ProtoMessage:
        return self.transform_message_to_list(service, proto_message)


@dataclass
class ResponseAsListGenerationPlugin(AsListGenerationPlugin):
    def transform_response_message(
        self, service: Type["Service"], proto_message: ProtoMessage
    ) -> ProtoMessage:
        return self.transform_message_to_list(service, proto_message)
