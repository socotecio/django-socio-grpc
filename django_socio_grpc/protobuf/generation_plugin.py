import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple, Type, Union

from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.protobuf.proto_classes import FieldCardinality, ProtoField, ProtoMessage
from django_socio_grpc.settings import FilterAndPaginationBehaviorOptions, grpc_settings

if TYPE_CHECKING:
    from django_socio_grpc.services import Service

logger = logging.getLogger("django_socio_grpc.generation")


class BaseGenerationPlugin:
    """
    The base class to create generation plugins.
    """

    def check_condition(
        self,
        service: Type["Service"],
        request_message: ProtoMessage,
        response_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> bool:
        """
        Method that allow to return with modifying the proto if some conditions are not met
        """
        return True

    def transform_request_message(
        self,
        service: Type["Service"],
        proto_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        """
        The actual method that transform the request ProtoMessage
        """
        return proto_message

    def transform_response_message(
        self,
        service: Type["Service"],
        proto_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        """
        The actual method that transform the response ProtoMessage
        """
        return proto_message

    def run_validation_and_transform(
        self,
        service: Type["Service"],
        request_message: ProtoMessage,
        response_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> Tuple[ProtoMessage, ProtoMessage]:
        """
        The main orchestrator method of the plugin. This is the first entrypoint.
        It check the confition setted by check_condition method and then call transform_request_message and transform_response_message
        """
        if not self.check_condition(
            service, request_message, response_message, message_name_constructor
        ):
            return request_message, response_message

        return self.transform_request_message(
            service, request_message, message_name_constructor
        ), self.transform_response_message(service, response_message, message_name_constructor)


class BaseAddFieldRequestGenerationPlugin(BaseGenerationPlugin):
    """
    Util class to inherit for adding a field in a request proto message.
    By inerhit it and fill field_name, field_cardinality and field_type it will create a plugin that add a field without having to override any method.
    """

    field_name: str
    field_type: Union[str, ProtoMessage]
    field_cardinality: FieldCardinality

    def __init__(self, *args, **kwargs):
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


class FilterGenerationPlugin(BaseAddFieldRequestGenerationPlugin):
    """
    Plugin to add the _filters field in the request ProtoMessage. See https://django-socio-grpc.readthedocs.io/en/stable/features/filters.html#djangofilterbackend
    """

    field_name: str = "_filters"
    field_type: Union[str, ProtoMessage] = "google.protobuf.Struct"
    field_cardinality: FieldCardinality = FieldCardinality.OPTIONAL

    def __init__(self, display_warning_message=True):
        self.display_warning_message = display_warning_message
        super().__init__()

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
            if self.display_warning_message:
                logger.warning(
                    "You are using FilterGenerationPlugin but no filter_backends as been found on the service. Please set a filter_backends in the service or set it globally with DEFAULT_FILTER_BACKENDS setting."
                )
            return False

        if grpc_settings.FILTER_BEHAVIOR == FilterAndPaginationBehaviorOptions.METADATA_STRICT:
            if self.display_warning_message:
                logger.warning(
                    "You are using FilterGenerationPlugin but FILTER_BEHAVIOR settings is set to 'METADATA_STRICT' so it will have no effect. Please change FILTER_BEHAVIOR."
                )
            return False

        return True


class PaginationGenerationPlugin(BaseAddFieldRequestGenerationPlugin):
    """
    Plugin to add the _pagination field in the request ProtoMessage. See https://django-socio-grpc.readthedocs.io/en/stable/features/pagination.html
    """

    field_name: str = "_pagination"
    field_type: Union[str, ProtoMessage] = "google.protobuf.Struct"
    field_cardinality: FieldCardinality = FieldCardinality.OPTIONAL

    def __init__(self, display_warning_message=True):
        self.display_warning_message = display_warning_message
        super().__init__()

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
            if self.display_warning_message:
                logger.warning(
                    "You are using PaginationGenerationPlugin but no pagination_class as been found on the service. Please set a pagination_class in the service or set it globally with DEFAULT_PAGINATION_CLASS setting."
                )
            return False

        if (
            grpc_settings.PAGINATION_BEHAVIOR
            == FilterAndPaginationBehaviorOptions.METADATA_STRICT
        ):
            if self.display_warning_message:
                logger.warning(
                    "You are using PaginationGenerationPlugin but PAGINATION_BEHAVIOR settings is set to 'METADATA_STRICT' so it will have no effect. Please change PAGINATION_BEHAVIOR."
                )
            return False

        return True


@dataclass
class AsListGenerationPlugin(BaseGenerationPlugin):
    """
    Plugin allowing to encapsulate a message into an other message and put it as a repeated field to return multiple instance.
    Do not use directly, use one of it's subclass RequestAsListGenerationPlugin, ResponseAsListGenerationPlugin or RequestAndResponseAsListGenerationPlugin
    """

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

        list_message = ProtoMessage(
            name=list_name,
            fields=fields,
        )

        # INFO - AM - If the original proto message is a serializer then we keep the comment at the serializer level. Else we put them at the list level
        if not proto_message.serializer:
            list_message.comments = proto_message.comments
            proto_message.comments = None

        return list_message


class RequestAsListGenerationPlugin(AsListGenerationPlugin):
    """
    Transform a request ProtoMessage in a list ProtoMessage
    """

    def transform_request_message(
        self,
        service: Type["Service"],
        proto_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        list_name = message_name_constructor.construct_request_list_name()
        return self.transform_message_to_list(service, proto_message, list_name)


class ResponseAsListGenerationPlugin(AsListGenerationPlugin):
    """
    Transform a response ProtoMessage in a list ProtoMessage
    """

    def transform_response_message(
        self,
        service: Type["Service"],
        proto_message: ProtoMessage,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        list_name = message_name_constructor.construct_response_list_name()
        return self.transform_message_to_list(service, proto_message, list_name)


class RequestAndResponseAsListGenerationPlugin(
    RequestAsListGenerationPlugin, ResponseAsListGenerationPlugin
):
    """
    Transform both request and response ProtoMessage in list ProtoMessage
    """

    ...
