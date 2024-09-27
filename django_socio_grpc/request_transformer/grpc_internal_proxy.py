from dataclasses import dataclass
from typing import Optional

from django.utils.datastructures import (
    CaseInsensitiveMapping,
)
from google.protobuf.message import Message
from grpc.aio import ServicerContext

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

    grpc_response: Message
    # INFO - AM - 25/07/2024 - grpc context is used to pass response header to client
    grpc_context: ServicerContext
    # INFO - AM - 01/08/2024 - http_response is created in post_init signals. Don't need to pass it in the constructor if defautl behavior wanted.
    http_response: InternalHttpResponse | None = None
    # INFO - AM - 01/08/2024 - headers is created in post_init signals. Don't need to pass it in the constructor if defautl behavior wanted.
    headers: Optional["ResponseHeadersProxy"] = None

    def __post_init__(self):
        self.http_response = InternalHttpResponse()
        self.headers = ResponseHeadersProxy(self.grpc_context, self.http_response)

    def __getattr__(self, attr):
        """
        This private method is used to correctly distribute the attribute access between the proxy, th grpc_response and the http_response
        """
        if attr in self.__annotations__:
            return super().__getattribute__(attr)
        if hasattr(self.grpc_response, attr):
            return getattr(self.grpc_response, attr)
        return getattr(self.http_response, attr)

    def __delitem__(self, header):
        """
        Allow to treat GRPCInternalProxyResponse as a dict of headers as django.http.HttpResponse does
        """
        return self.headers.__delitem__(header)

    def __setitem__(self, key, value):
        """
        Allow to treat GRPCInternalProxyResponse as a dict of headers as django.http.HttpResponse does
        """
        return self.headers.__setitem__(key, value)

    def __getitem__(self, header):
        """
        Allow to treat GRPCInternalProxyResponse as a dict of headers as django.http.HttpResponse does
        """
        return self.headers.__getitem__(header)

    def has_header(self, header):
        """Case-insensitive check for a header."""
        return header in self.headers

    __contains__ = has_header

    def get(self, key, default=None):
        """
        Allow to treat GRPCInternalProxyResponse as a dict of headers as django.http.HttpResponse does
        """
        return self.headers.get(key, default)

    def items(self):
        """
        Allow to treat GRPCInternalProxyResponse as a dict of headers as django.http.HttpResponse does
        """
        return self.headers.items()

    def setdefault(self, key, value):
        """
        Allow to treat GRPCInternalProxyResponse as a dict of headers as django.http.HttpResponse does
        Set a header unless it has already been set.
        """
        self.headers.setdefault(key, value)

    def __getstate__(self):
        """
        Allow to serialize the object mainly for cache purpose
        """
        return {
            "grpc_response": self.grpc_response,
            "http_response": self.http_response,
            "response_metadata": dict(self.grpc_context.trailing_metadata()),
        }

    def __repr__(self):
        return f"GRPCInternalProxyResponse<{self.grpc_response.__repr__()}, {self.http_response.__repr__()}>"

    def __setstate__(self, state):
        """
        Allow to deserialize the object mainly for cache purpose.
        When used in cache, the grpc_context is not set. To be correctly use set_current_context method should be called
        """
        self.grpc_response = state["grpc_response"]
        self.http_response = state["http_response"]
        self.headers = ResponseHeadersProxy(
            None, self.http_response, metadata=state["response_metadata"]
        )
        self.grpc_context = None

    def set_current_context(self, grpc_context: ServicerContext):
        """
        This method is used to set the current context to the response object when fetched from cache
        It also enable the copy of the cache metdata
        """
        self.grpc_context = grpc_context
        self.headers.set_grpc_context(grpc_context)

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
    See https://github.com/django/django/blob/main/django/http/response.py#L32 for inspiration
    """

    grpc_context: ServicerContext | None
    http_response: InternalHttpResponse
    # INFO - AM - 31/07/2024 - Only used when restoring from cache. Do not use it directly.
    metadata: dict | None = None

    def __post_init__(self):
        if self.grpc_context is None and self.metadata is None:
            raise ValueError("grpc_context or metadata must be set for ResponseHeadersProxy")
        if self.grpc_context is not None:
            metadata_as_dict = dict(self.grpc_context.trailing_metadata())
        else:
            metadata_as_dict = self.metadata
        self.http_response.headers = metadata_as_dict
        super().__init__(data=metadata_as_dict)

    def set_grpc_context(self, grpc_context: ServicerContext):
        """
        When GRPCInternalProxyResponse is created from cache it doesn't have a grpc_context.
        This method is used to set it after the object is created and merge their current metadata with the one cached
        """
        self.grpc_context = grpc_context
        existing_metadata = dict(grpc_context.trailing_metadata())

        trailing_metadata_dict = {**existing_metadata, **self.http_response.headers}
        # INFO - AM - 01/08/2024 - We need to convert all the values to string if not bytes as grpc metadata only accept string and bytes
        # We also need to convert all the keys to lower case as grpc metadata expect lower metadata keys
        trailing_metadata = [
            (key.lower(), str(value) if not isinstance(value, bytes) else value)
            for key, value in trailing_metadata_dict.items()
        ]
        self.grpc_context.set_trailing_metadata(trailing_metadata)

    def setdefault(self, key, value):
        if key not in self:
            self[key] = value

    def __setitem__(self, key, value):
        if self.grpc_context:
            trailing_metadata = self.grpc_context.trailing_metadata()
            self.grpc_context.set_trailing_metadata(
                trailing_metadata + ((key.lower(), str(value)),)
            )
        self.http_response[key] = value
        self._store[key.lower()] = (key, value)

    def __delitem__(self, header):
        if self.grpc_context:
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
