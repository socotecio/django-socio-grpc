from dataclasses import dataclass
from typing import Optional

from google.protobuf.message import Message
from grpc.aio import ServicerContext
from grpc.aio._typing import ResponseType

from django.utils.datastructures import (
    CaseInsensitiveMapping,
)

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
    http_response: Optional[InternalHttpResponse] = None
    _cached_metadata: Optional[list] = None
    headers: Optional["ResponseHeadersProxy"] = None

    def __post_init__(self):
        self.http_response = InternalHttpResponse()
        self.headers = ResponseHeadersProxy(self.grpc_context, self.http_response)

    def __getattr__(self, attr):
        if attr == "headers":
            return super().__getattribute__(attr)
        if hasattr(self.grpc_response, attr):
            return getattr(self.grpc_response, attr)
        return getattr(self.http_response, attr)

    def __delitem__(self, header):
        return self.headers.__delitem__(header)

    def __setitem__(self, key, value):
        return self.headers.__setitem__(key, value)

    def __getitem__(self, header):
        return self.headers.__getitem__(header)

    def has_header(self, header):
        """Case-insensitive check for a header."""
        return header in self.headers

    __contains__ = has_header

    def get(self, key, default=None):
        return self.headers.get(key, default)

    def items(self):
        return self.headers.items()

    def setdefault(self, key, value):
        """Set a header unless it has already been set."""
        self.headers.setdefault(key, value)

    def __getstate__(self):
        return {
            "grpc_response": self.grpc_response,
            "http_response": self.http_response,
            "response_metadata": dict(self.grpc_context.trailing_metadata()),
        }

    def __repr__(self):
        return f"GRPCInternalProxyResponse<{self.grpc_response.__repr__()}, {self.http_response.__repr__()}>"

    def __setstate__(self, state):
        self.grpc_response = state["grpc_response"]
        self.http_response = state["http_response"]
        self._cached_metadata = [
            (key, value) for key, value in state["response_metadata"].items()
        ]

    def set_current_context(self, grpc_context):
        """
        This method is used to set the current context to the response object when fetched from cache
        It also enable the copy of the cache metdata
        """
        self.grpc_context = grpc_context
        self.grpc_context.set_trailing_metadata(self._cached_metadata)
        self.headers = ResponseHeadersProxy(self.grpc_context, self.http_response)

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


@dataclass
class ResponseHeadersProxy(CaseInsensitiveMapping):
    """
    Class that allow us to write headers both in grpc metadata and http response to keep compatibility with django system
    """

    grpc_context: ServicerContext
    http_response: InternalHttpResponse

    def __post_init__(self):
        # INFO - AM - 27/07/2024 - Start with empty headers when creation a response
        metadata_as_dict = dict(self.grpc_context.trailing_metadata())
        self.http_response.headers = metadata_as_dict
        super().__init__(data=metadata_as_dict)

    def setdefault(self, key, value):
        if key not in self:
            self[key] = value

    def __setitem__(self, key, value):
        trailing_metadata = self.grpc_context.trailing_metadata()
        self.grpc_context.set_trailing_metadata(trailing_metadata + ((key.lower(), value),))
        self.http_response[key] = value
        self._store[key.lower()] = (key, value)

    def __delitem__(self, header):
        new_metadata = [
            (k, v)
            for k, v in self.grpc_context.trailing_metadata()
            if k.lower() != header.lower()
        ]
        self.grpc_context.set_trailing_metadata(new_metadata)
        del self.http_response[header]
        super().__delitem__(header)

    def __repr__(self):
        return super().__repr__()
