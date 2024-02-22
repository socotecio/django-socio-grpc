from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Type, Union

from rest_framework.serializers import BaseSerializer

from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.constants import REQUEST_SUFFIX, RESPONSE_SUFFIX
from django_socio_grpc.utils.tools import rreplace

if TYPE_CHECKING:
    from django_socio_grpc.protobuf.proto_classes import FieldDict
    from django_socio_grpc.services import Service


@dataclass
class MessageNameConstructor:
    action_name: str
    service: Type["Service"]

    _request_constructed_name: Optional[str] = None
    _response_constructed_name: Optional[str] = None

    _request_full_name: Optional[str] = None
    _response_full_name: Optional[str] = None

    def __post_init__(self):
        self.service_name = self.service.get_service_name()

    @property
    def request_constructed_name(self) -> str:
        """
        That name of the request constructed from the message and message_name(name specifically specified by the dev)
        This property can only be call after construct_request_name
        """
        if self._request_constructed_name is None:
            raise Exception("request_constructed_name called before construct_request_name")
        return self._request_constructed_name

    @property
    def response_constructed_name(self) -> str:
        """
        That name of the response constructed from the message and message_name(name specifically specified by the dev)
        This property can only be call after construct_response_name
        """
        if self._response_constructed_name is None:
            raise Exception("response_constructed_name called before construct_response_name")
        return self._response_constructed_name

    @property
    def request_full_name(self) -> str:
        """
        The request_constructed_name with the correct suffix if SEPARATE_READ_WRITE_MODEL settings is True
        This property can only be call after construct_request_name
        """
        if self._request_full_name is None:
            raise Exception("request_full_name called before construct_request_name")
        return self._request_full_name

    @property
    def response_full_name(self) -> str:
        """
        The response_constructed_name with the correct suffix if SEPARATE_READ_WRITE_MODEL settings is True
        This property can only be call after construct_response_name
        """
        if self._response_full_name is None:
            raise Exception("response_full_name called before construct_response_name")
        return self._response_full_name

    @classmethod
    def get_base_name_from_serializer(cls, serializer: Type[BaseSerializer]) -> str:
        """
        Get the name that will be displayed for the message in a .proto file for a specific Serializer.
        It is the name of the serializer class without "ProtoSerializer" or "Serializer" at the end if any.
        """
        name = serializer.__name__
        if "ProtoSerializer" in name:
            name = rreplace(name, "ProtoSerializer", "", 1)
        elif "Serializer" in name:
            name = rreplace(name, "Serializer", "", 1)

        return name

    @classmethod
    def get_base_name_from_serializer_with_suffix(
        cls, serializer: Type[BaseSerializer], suffix: str = ""
    ) -> str:
        """
        Add the correct suffix ("REQUEST", "RESPONSE", "") to the name from the serializer (see get_base_name_from_serializer)
        """
        base_name = cls.get_base_name_from_serializer(serializer)

        return base_name + suffix

    def construct_name(
        self,
        message: Optional[Union[str, Type[BaseSerializer], List["FieldDict"]]],
        message_name: Optional[str],
    ):
        """
        Construct the ProtoMessage name without the suffix ("REQUEST", "RESPONSE", "") from the message and potentialy the name the user specified
        """
        if message_name:
            return message_name
        if isinstance(message, type) and issubclass(message, BaseSerializer):
            return self.get_base_name_from_serializer(message)
        else:
            return f"{self.service_name}{self.action_name}"

    def construct_request_name(
        self,
        message: Optional[Union[str, Type[BaseSerializer], List["FieldDict"]]],
        message_name: Optional[str],
    ):
        """
        Get the name of the request as displayed in the proto file
        """
        self._request_constructed_name = self._request_full_name = self.construct_name(
            message, message_name
        )

        if grpc_settings.SEPARATE_READ_WRITE_MODEL and not message_name:
            self._request_full_name += REQUEST_SUFFIX

        return self._request_full_name

    def construct_response_name(
        self,
        message: Optional[Union[str, Type[BaseSerializer], List["FieldDict"]]],
        message_name: Optional[str],
    ):
        """
        Get the name of the response as displayed in the proto file
        """
        self._response_constructed_name = self._response_full_name = self.construct_name(
            message, message_name
        )

        if grpc_settings.SEPARATE_READ_WRITE_MODEL and not message_name:
            self._response_full_name += RESPONSE_SUFFIX

        return self._response_full_name
