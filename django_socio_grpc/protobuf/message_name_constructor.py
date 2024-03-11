from abc import ABC, abstractmethod
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
class MessageNameConstructor(ABC):
    action_name: str
    service: Type["Service"]
    action_request: Optional[Union[str, Type[BaseSerializer], List["FieldDict"]]]
    request_name: Optional[str]
    action_response: Optional[Union[str, Type[BaseSerializer], List["FieldDict"]]]
    response_name: Optional[str]

    def __post_init__(self):
        self.service_name = self.service.get_service_name()

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

    @abstractmethod
    def construct_request_list_name(self):
        """
        Inherit from this method to get the name of the request list message as displayed in the proto file
        """
        pass

    @abstractmethod
    def construct_response_list_name(self):
        """
        Inherit from this method to get the name of the response list message as displayed in the proto file
        """
        pass

    @abstractmethod
    def construct_request_name(
        self,
        before_suffix: str = "",
    ):
        """
        Inherit from this method to get the name of the request as displayed in the proto file
        """
        pass

    @abstractmethod
    def construct_response_name(
        self,
        before_suffix: str = "",
    ):
        """
        Inherit from this method to get the name of the response as displayed in the proto file
        """
        pass


@dataclass
class DefaultMessageNameConstructor(MessageNameConstructor):
    def __post_init__(self):
        self.service_name = self.service.get_service_name()

    def construct_base_name(self, is_request: bool = True):
        action_message = self.action_request if is_request else self.action_response

        if isinstance(action_message, type) and issubclass(action_message, BaseSerializer):
            return self.get_base_name_from_serializer(action_message)
        else:
            return f"{self.service_name}{self.action_name}"

    def construct_name(
        self,
        is_request: bool = True,
        before_suffix: str = "",
    ):
        """
        Construct the ProtoMessage name from the message and potentialy the name the user specified
        """

        message_name = self.request_name if is_request else self.response_name
        suffix = REQUEST_SUFFIX if is_request else RESPONSE_SUFFIX

        name = ""
        if message_name:
            name = message_name
        else:
            name = self.construct_base_name(is_request=is_request)

        # HACK - AM - 22/02/2024 - If dev used specific message name that end by "Request" or "Response" we can't known without doing this.
        # We put it back after inserting the before_suffix thank to force_suffix
        force_suffix = False
        if name.endswith(suffix) and grpc_settings.SEPARATE_READ_WRITE_MODEL:
            name = name[: -len(suffix)]
            force_suffix = True

        # INFO - AM - 27/02/2024 - We choose to not duplicate if the name end by the before suffix. If you want something different please just create your own name constructor class
        if before_suffix and not name.endswith(before_suffix):
            name += before_suffix

        # INFO - AM - 27/02/2024 - Finally add the suffix only if not already finishing by the suffix
        if (
            grpc_settings.SEPARATE_READ_WRITE_MODEL
            and not name.endswith(suffix)
            and (not message_name or force_suffix)
        ):
            name += suffix

        return name

    def construct_request_list_name(self):
        """
        Get the name of the request list message as displayed in the proto file
        """
        return self.construct_name(is_request=True, before_suffix="List")

    def construct_response_list_name(self):
        """
        Get the name of the response list message as displayed in the proto file
        """
        return self.construct_name(is_request=False, before_suffix="List")

    def construct_request_name(
        self,
        before_suffix: str = "",
    ):
        """
        Get the name of the request as displayed in the proto file
        """

        return self.construct_name(is_request=True, before_suffix=before_suffix)

    def construct_response_name(
        self,
        before_suffix: str = "",
    ):
        """
        Get the name of the response as displayed in the proto file
        """

        return self.construct_name(is_request=False, before_suffix=before_suffix)
