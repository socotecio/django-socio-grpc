from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, List, Optional, Type, Union

from rest_framework.serializers import BaseSerializer

from django_socio_grpc.protobuf.proto_classes import (
    FieldCardinality,
    FieldDict,
    ProtoField,
    ProtoMessage,
    ProtoRpc,
    ProtoService,
    RequestProtoMessage,
    ResponseProtoMessage,
)
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.constants import (
    DEFAULT_LIST_FIELD_NAME,
    LIST_ATTR_MESSAGE_NAME,
    REQUEST_SUFFIX,
    RESPONSE_SUFFIX,
)
from django_socio_grpc.utils.tools import rreplace

if TYPE_CHECKING:
    from django_socio_grpc.services import Service


@dataclass
class MessageNameConstructor:
    action_name: str
    service: Type["Service"]

    def __post_init__(self):
        self.service_name = self.service.get_service_name()

    @classmethod
    def get_base_name_from_serializer(cls, serializer: Type[BaseSerializer]) -> str:
        name = serializer.__name__
        if "ProtoSerializer" in name:
            name = rreplace(name, "ProtoSerializer", "", 1)
        elif "Serializer" in name:
            name = rreplace(name, "Serializer", "", 1)

        return name

    def construct_name(
        self,
        message: Optional[Union[str, Type[BaseSerializer], List[FieldDict]]],
        message_name: Optional[str],
    ):
        if message_name:
            return message_name
        if isinstance(message, type) and issubclass(message, BaseSerializer):
            return self.get_base_name_from_serializer(message)
        else:
            return f"{self.service_name}{self.action_name}"

    def construct_request_name(
        self,
        message: Optional[Union[str, Type[BaseSerializer], List[FieldDict]]],
        message_name: Optional[str],
    ):
        name = self.construct_name(message, message_name)

        if grpc_settings.SEPARATE_READ_WRITE_MODEL:
            name += REQUEST_SUFFIX

        return name

    def construct_response_name(
        self,
        message: Optional[Union[str, Type[BaseSerializer], List[FieldDict]]],
        message_name: Optional[str],
    ):
        name = self.construct_name(message, message_name)

        if grpc_settings.SEPARATE_READ_WRITE_MODEL:
            name += RESPONSE_SUFFIX

        return name
