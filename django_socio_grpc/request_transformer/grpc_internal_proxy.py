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
    http_request: InternalHttpRequest = None

    def __post_init__(self):
        self.http_request = InternalHttpRequest(self, self.grpc_request, self.grpc_action)

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
    http_response: InternalHttpResponse = None

    def __post_init__(self):
        self.http_response = InternalHttpResponse()

    def __getattr__(self, attr):
        if hasattr(self.grpc_response, attr):
            return getattr(self.grpc_response, attr)
        return getattr(self.http_response, attr)

    def __aiter__(self):
        return self

    async def __anext__(self):
        """
        Used to iterate over the proxy to the grpc_response as the http response can't be iterate over
        """
        next_item = await self.grpc_response.__anext__()
        return GRPCInternalProxyResponse(next_item)

    def __iter__(self):
        return self

    def __next__(self):
        """
        Used to iterate over the proxy to the grpc_response as the http response can't be iterate over
        """
        next_item = self.grpc_response.__next__()
        return GRPCInternalProxyResponse(next_item)
