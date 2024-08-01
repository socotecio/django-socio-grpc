from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from google.protobuf.message import Message

from django_socio_grpc.request_transformer.grpc_internal_proxy import (
    GRPCInternalProxyContext,
    GRPCInternalProxyResponse,
)

if TYPE_CHECKING:
    from django_socio_grpc.services import Service


@dataclass
class GRPCRequestContainer:
    """
    This class is a simple container that allow us to pass some date throught the grpc -> servicer -> middleware -> service.
    To be able to work with django middleware if an attribute is not found (when getting or setting) on GRPCRequestContainer we look in the GRPCInternalProxyContext where we stock all the compatibility logic
    """

    grpc_request: Message
    context: GRPCInternalProxyContext
    action: str
    service: "Service"

    def __getattr__(self, attr):
        """
        See class documentation
        """
        return getattr(self.context, attr)

    def __setattr__(self, attr: str, value: Any) -> None:
        """
        See class documentation
        """
        if attr in self.__annotations__:
            return super().__setattr__(attr, value)
        else:
            setattr(self.context.grpc_context, attr, value)


@dataclass
class GRPCResponseContainer:
    """
    This class is a simple container that allow us to pass some date throught the service -> middleware -> servicer -> grpc.
    To be able to work with django middleware if an attribute is not found (when getting, setting or iteratinf) on GRPCResponseContainer we look in the GRPCInternalProxyResponse where we stock all the compatibility logic
    """

    response: GRPCInternalProxyResponse

    def __getattr__(self, attr):
        """
        See class documentation
        """
        return getattr(self.response, attr)

    def __aiter__(self):
        return self.response

    def __iter__(self):
        return self.response
