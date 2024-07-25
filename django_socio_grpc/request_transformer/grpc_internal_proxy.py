from dataclasses import dataclass

from google.protobuf.message import Message
from grpc.aio import ServicerContext
from grpc.aio._typing import ResponseType

from .socio_internal_request import InternalHttpRequest
from .socio_internal_response import InternalHttpResponse


@dataclass
class GRPCInternalProxyContext:
    """
    Proxy context, provide http1 proxy request object and grpc context object
    Used principally for request data based mechanisme, example: filtering, middleware, authentication
    """

    grpc_context: ServicerContext
    # INFO - AM - 14/02/2024 - grpc_request is used to get filter and pagination from the request. It is not acessible in GRPCInternalProxyContext.
    grpc_request: Message
    grpc_action: str
    service_class_name: str
    http_request: InternalHttpRequest = None

    def __post_init__(self):
        self.http_request = InternalHttpRequest(
            self, self.grpc_request, self.grpc_action, self.service_class_name
        )

    def __getattr__(self, attr):
        if hasattr(self.grpc_context, attr):
            return getattr(self.grpc_context, attr)
        return getattr(self.http_request, attr)


@dataclass
class GRPCInternalProxyResponse:
    """
    Proxy response, provide http1 response and grpc respone object
    Used principally to middleware. Not doing anything speciale for now but not crashing when using.
    Need to be improved if some specific behavior needed, for example injecting some data in the reponse metadata.
    """

    grpc_response: ResponseType
    # INFO - AM - 25/07/2024 - grpc context is used to pass response header to client
    grpc_context: ServicerContext
    http_response: InternalHttpResponse = None

    def __post_init__(self):
        self.http_response = InternalHttpResponse(self.grpc_context)
        self.__contains__ = self.http_response.has_header

    def __getattr__(self, attr):
        if attr == "headers":
            return self
        if hasattr(self.grpc_response, attr):
            return getattr(self.grpc_response, attr)
        return getattr(self.http_response, attr)

    def __setitem__(self, header, value):
        print("Setting header", header, value)
        trailing_metadata = self.grpc_context.trailing_metadata()
        self.grpc_context.set_trailing_metadata(trailing_metadata + [(header, value)])
        self.http_response[header] = value

    def __delitem__(self, header):
        new_metadata = [
            (k, v) for k, v in self.grpc_context.trailing_metadata() if k != header
        ]
        self.grpc_context.set_trailing_metadata(new_metadata)
        del self.http_response[header]

    def __getitem__(self, header):
        return self.http_response[header]

    def __getstate__(self):
        return {
            "grpc_response": self.grpc_response,
            "http_response": self.http_response,
        }

    def __repr__(self):
        return f"GRPCInternalProxyResponse<{self.grpc_response.__repr__()}>, {self.http_response.__repr__()}"

    def __setstate__(self, state):
        self.grpc_response = state["grpc_response"]
        self.http_response = state["http_response"]

    def __aiter__(self):
        return self

    async def __anext__(self):
        """
        Used to iterate over the proxy to the grpc_response as the http response can't be iterate over
        """
        next_item = await self.grpc_response.__anext__()
        return GRPCInternalProxyResponse(next_item, self.grpc_context)

    def __iter__(self):
        return self

    def __next__(self):
        """
        Used to iterate over the proxy to the grpc_response as the http response can't be iterate over
        """
        next_item = self.grpc_response.__next__()
        return GRPCInternalProxyResponse(next_item, self.grpc_context)
