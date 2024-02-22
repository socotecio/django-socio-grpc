import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Tuple, Type

from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.protobuf.proto_classes import FieldCardinality, ProtoField, ProtoMessage
from django_socio_grpc.settings import FilterAndPaginationBehaviorOptions, grpc_settings
from django_socio_grpc.utils.constants import REQUEST_SUFFIX, RESPONSE_SUFFIX

if TYPE_CHECKING:
    from django_socio_grpc.services import Service

logger = logging.getLogger("django_socio_grpc.generation")


@dataclass
class BaseGenerationPlugin:
    def check_condition(
        self,
        service: Type["Service"],
        request_message: ProtoMessage,
        response_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> bool:
        return True

    def transform_request_message(
        self,
        service: Type["Service"],
        proto_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        return proto_message

    def transform_response_message(
        self,
        service: Type["Service"],
        proto_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        return proto_message

    def run_validation_and_transform(
        self,
        service: Type["Service"],
        request_message: ProtoMessage,
        response_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> Tuple[ProtoMessage, ProtoMessage]:
        if not self.check_condition(
            service, request_message, response_message, message_name_constructor
        ):
            return request_message, response_message

        return self.transform_request_message(
            service, request_message, message_name_constructor
        ), self.transform_response_message(service, response_message, message_name_constructor)

    # def insert_suffix_before_response_or_request(self, proto_message: ProtoMessage, suffix_to_add:str):
    #     if not grpc_settings.SEPARATE_READ_WRITE_MODEL:
    #         return proto_message.name + suffix_to_add

    #     last_request_index = proto_message.name.rfind(REQUEST_SUFFIX)
    #     last_response_index = proto_message.name.rfind(RESPONSE_SUFFIX)

    #     if last_request_index > last_response_index:
    #         return proto_message.name[:last_request_index] + f"{suffix_to_add}{REQUEST_SUFFIX}"
    #     elif last_response_index > last_request_index:
    #         return proto_message.name[:last_response_index] + f"{suffix_to_add}{RESPONSE_SUFFIX}"
    #     else:
    #         return proto_message.name + suffix_to_add


@dataclass
class BaseAddFieldRequestGenerationPlugin(BaseGenerationPlugin):
    field_name: ClassVar[str] = None
    field_cardinality: ClassVar[str] = None
    field_type: ClassVar[str] = None

    def __post_init__(self):
        error_message = "You try to instanciate a class that inherit from BaseGenerationPlugin. to do that you need to specify a {0} attribute"

        assert self.field_name is not None, error_message.format("field_name")
        assert self.field_cardinality is not None, error_message.format("field_cardinality")
        assert self.field_type is not None, error_message.format("field_type")

    def transform_request_message(
        self,
        service: Type["Service"],
        proto_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ):
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
        message_name_constructor: MessageNameConstructor,
    ) -> bool:
        # INFO - AM - 20/02/2024 - If service don't support filtering we do not add filter field
        if (
            not hasattr(service, "filter_backends")
            or not service.filter_backends
            and not grpc_settings.DEFAULT_FILTER_BACKENDS
        ):
            logger.warning(
                "You are using FilterGenerationPlugin but no filter_backends as been found on the service. Please set a filter_backends in the service or set it globally with DEFAULT_FILTER_BACKENDS setting."
            )
            return False

        if grpc_settings.FILTER_BEHAVIOR == FilterAndPaginationBehaviorOptions.METADATA_STRICT:
            logger.warning(
                "You are using FilterGenerationPlugin but FILTER_BEHAVIOR settings is set to 'METADATA_STRICT' so it will have no effect. Please change FILTER_BEHAVIOR."
            )
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
        message_name_constructor: MessageNameConstructor,
    ) -> bool:
        # INFO - AM - 20/02/2024 - If service don't support filtering we do not add filter field
        if (
            not hasattr(service, "pagination_class")
            or not service.pagination_class
            and not grpc_settings.DEFAULT_PAGINATION_CLASS
        ):
            logger.warning(
                "You are using PaginationGenerationPlugin but no pagination_class as been found on the service. Please set a pagination_class in the service or set it globally with DEFAULT_PAGINATION_CLASS setting."
            )
            return False

        if (
            grpc_settings.PAGINATION_BEHAVIOR
            == FilterAndPaginationBehaviorOptions.METADATA_STRICT
        ):
            logger.warning(
                "You are using PaginationGenerationPlugin but PAGINATION_BEHAVIOR settings is set to 'METADATA_STRICT' so it will have no effect. Please change PAGINATION_BEHAVIOR."
            )
            return False

        return True


@dataclass
class AsListGenerationPlugin(BaseGenerationPlugin):
    list_field_name: str = "results"

    def transform_message_to_list(
        self, service: Type["Service"], proto_message: ProtoMessage, list_name: str
    ) -> ProtoMessage:
        try:
            list_field_name = proto_message.serializer.Meta.message_list_attr
        except AttributeError:
            list_field_name = self.list_field_name

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

        if grpc_settings.SEPARATE_READ_WRITE_MODEL:
            pass

        list_message = ProtoMessage(
            name=list_name,
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
        self,
        service: Type["Service"],
        proto_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        request_constructed_name = message_name_constructor.request_constructed_name
        # HACK - AM - 22/02/2024 - If dev used specific message name that end by request we can't known without doing this
        if request_constructed_name.endswith(REQUEST_SUFFIX):
            request_constructed_name = request_constructed_name[: -len(REQUEST_SUFFIX)]
        list_name = request_constructed_name + "List" + REQUEST_SUFFIX
        return self.transform_message_to_list(service, proto_message, list_name)


@dataclass
class ResponseAsListGenerationPlugin(AsListGenerationPlugin):
    def transform_response_message(
        self,
        service: Type["Service"],
        proto_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        response_constructed_name = message_name_constructor.response_constructed_name
        # HACK - AM - 22/02/2024 - If dev used specific message name that end by response we can't known without doing this
        if response_constructed_name.endswith(RESPONSE_SUFFIX):
            response_constructed_name = response_constructed_name[: -len(RESPONSE_SUFFIX)]
        list_name = response_constructed_name + "List" + RESPONSE_SUFFIX
        return self.transform_message_to_list(service, proto_message, list_name)


class RequestAndResponseAsListGenerationPlugin(
    RequestAsListGenerationPlugin, ResponseAsListGenerationPlugin
):
    ...
