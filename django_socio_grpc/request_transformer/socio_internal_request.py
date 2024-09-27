import json
import logging
import urllib.parse
from typing import TYPE_CHECKING

from django.http.request import HttpHeaders, HttpRequest
from django.utils.datastructures import (
    CaseInsensitiveMapping,
)
from django.utils.functional import cached_property
from google.protobuf.message import Message

from django_socio_grpc.protobuf.json_format import message_to_dict
from django_socio_grpc.settings import FilterAndPaginationBehaviorOptions, grpc_settings

if TYPE_CHECKING:
    from django_socio_grpc.request_transformer.grpc_internal_proxy import (
        GRPCInternalProxyContext,
    )


logger = logging.getLogger(__name__)


class InternalHttpRequest(HttpRequest):
    """
    Class mocking django.http.HttpRequest to make some django behavior like middleware, filtering, authentication, ... still work.
    """

    HEADERS_KEY = "headers"
    FILTERS_KEY = "filters"
    PAGINATION_KEY = "pagination"
    FILTERS_KEY_IN_REQUEST = "_filters"
    PAGINATION_KEY_IN_REQUEST = "_pagination"

    #  Map http method to use DjangoModelPermission
    METHOD_MAP = {
        "List": "GET",
        "Retrieve": "GET",
        "Create": "POST",
        "Update": "PUT",
        "PartialUpdate": "PATCH",
        "Destroy": "DELETE",
    }

    def __init__(
        self,
        grpc_context: "GRPCInternalProxyContext",
        grpc_request: Message,
        grpc_action: str,
        service_class_name: str,
    ):
        """
        grpc_context is used to get all the headers and other informations
        grpc_request is only used for filter and pagination from the request if setted by FILTER_BEHAVIOR or PAGINATION_BEHAVIOR settings.
        grpc_action is used to populate InternalHttpRequest.method
        """
        self.user = None
        self.auth = None

        # INFO - AM - 23/07/2024 - We need to pass the service class name to be able to construct the request path to use cache for example
        self.service_class_name = service_class_name

        self.grpc_request_metadata = self.convert_metadata_to_dict(
            grpc_context.invocation_metadata()
        )
        meta_from_metadata = self.get_from_metadata(self.HEADERS_KEY)
        self.META = RequestMeta(meta_from_metadata.items())

        # INFO - A.D.B - 04/01/2021 - Not implemented for now
        self.POST = {}
        self.COOKIES = {}
        self.FILES = {}

        #  Grpc action to http method name
        self.method = self.grpc_action_to_http_method_name(grpc_action)

        # Computed params | grpc_request is passed as argument and not class element because we don't want developer to access to the request from the context proxy
        self.query_params = self.get_query_params(grpc_request)

        # INFO - AM - 23/07/2024 - Allow to use cache system based on filter and pagination metadata or request fields
        # See https://github.com/django/django/blob/main/django/http/request.py#L175
        self.META["QUERY_STRING"] = urllib.parse.urlencode(self.query_params, doseq=True)

        # INFO - AM - 25/07/2024 - We need to set the server name to be able to use the cache system.
        # In Django if there is no HTTP_X_FORWARDED_HOST or HTTP_HOST, it will use the SERVER_NAME set by the ASGI handler
        # As we do not use an ASGI server and grpc does not seem to support an access to the server name we default it to unknown if not specified directly into the metadata
        # If requirements change in futur it will be easily possible to use the ip address or a setting to set it
        # See https://github.com/django/django/blob/0e94f292cda632153f2b3d9a9037eb0141ae9c2e/django/http/request.py#L113
        # And https://github.com/django/django/blob/0e94f292cda632153f2b3d9a9037eb0141ae9c2e/django/core/handlers/asgi.py#L80
        if "SERVER_NAME" not in self.META:
            self.META["SERVER_NAME"] = "unknown"
        if "SERVER_PORT" not in self.META:
            self.META["SERVER_PORT"] = grpc_settings.GRPC_CHANNEL_PORT

        # INFO - AM - 10/02/2021 - Only implementing GET because it's easier as we have metadata here. For post we will have to pass the request and transform it to python dict.
        # It's possible but it will be slow the all thing so we hava to param this behavior with settings.
        # So we are waiting for the need to implement it
        self.GET = self.query_params

        self.path = f"{self.service_class_name}/{grpc_action}"
        self.path_info = grpc_action

        self.resolver_match = None
        self.content_type = None
        self.content_params = None

    @cached_property
    def headers(self):
        # INFO - AM - 26/07/2024 - As grpc not follow the HTTP headers from env specification, we manually match it
        # Maybe this should be restricted to only know HTTP headers ?
        add_http_to_metadata = {f"HTTP_{key}": value for key, value in self.META.items()}
        return HttpHeaders(add_http_to_metadata)

    def get_from_metadata(self, metadata_key: str) -> dict[str, str | bytes]:
        """
        Allow to:
        - Customise the metadata key used for pagination, filter and headers
        - override default metadata with some passed in HEADERS metadata key to have custom advanced behavior
        """
        metadata_key = grpc_settings.MAP_METADATA_KEYS.get(metadata_key.lower(), None)
        if not metadata_key:
            return self.grpc_request_metadata
        user_custom_headers = self.grpc_request_metadata.pop(metadata_key.lower(), "{}")
        return {
            **self.grpc_request_metadata,
            **json.loads(user_custom_headers),
        }

    def parse_specific_key_from_metadata(self, metadata_key: str) -> dict[str, str | bytes]:
        """
        Allow to Customise the metadata key used for pagination, filter and headers
        """
        metadata_key = grpc_settings.MAP_METADATA_KEYS.get(metadata_key.lower(), None)
        return json.loads(self.grpc_request_metadata.get(metadata_key.lower(), "{}"))

    def get_from_request_struct(self, grpc_request: Message, struct_field_name: str) -> dict:
        # INFO - AM - 14/02/2024 - Need to check both if the request have a _filters key and if this optional _filters is filled
        if hasattr(grpc_request, struct_field_name) and grpc_request.HasField(
            struct_field_name
        ):
            return message_to_dict(getattr(grpc_request, struct_field_name))

        return {}

    def convert_metadata_to_dict(self, invocation_metadata: tuple) -> dict[str, str | bytes]:
        grpc_request_metadata = {}
        for key, value in dict(invocation_metadata).items():
            grpc_request_metadata[key.lower()] = value
        return grpc_request_metadata

    def get_query_params(self, grpc_request: Message) -> dict[str, str]:
        """
        Method that transform specific metadata and/or request fields (depending on FILTER_BEHAVIOR and PAGINATION_BEHAVIOR settings)
        into a dict as if it was some query params passed in simple HTTP/1 calls
        """
        query_params = {}
        if grpc_settings.FILTER_BEHAVIOR in [
            FilterAndPaginationBehaviorOptions.METADATA_AND_REQUEST_STRUCT,
            FilterAndPaginationBehaviorOptions.METADATA_STRICT,
        ]:
            query_params = {
                **query_params,
                **self.parse_specific_key_from_metadata(self.FILTERS_KEY),
            }

        if grpc_settings.FILTER_BEHAVIOR in [
            FilterAndPaginationBehaviorOptions.METADATA_AND_REQUEST_STRUCT,
            FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
        ]:
            query_params = {
                **query_params,
                **self.get_from_request_struct(grpc_request, self.FILTERS_KEY_IN_REQUEST),
            }

        if grpc_settings.PAGINATION_BEHAVIOR in [
            FilterAndPaginationBehaviorOptions.METADATA_AND_REQUEST_STRUCT,
            FilterAndPaginationBehaviorOptions.METADATA_STRICT,
        ]:
            query_params = {
                **query_params,
                **self.parse_specific_key_from_metadata(self.PAGINATION_KEY),
            }

        if grpc_settings.PAGINATION_BEHAVIOR in [
            FilterAndPaginationBehaviorOptions.METADATA_AND_REQUEST_STRUCT,
            FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
        ]:
            query_params = {
                **query_params,
                **self.get_from_request_struct(grpc_request, self.PAGINATION_KEY_IN_REQUEST),
            }

        return query_params

    def grpc_action_to_http_method_name(self, grpc_action: str) -> str:
        """
        Allow to match known grpc action to method type. In the futur we may need/want to use a specific decorator that inject the correct mapping into the grpc context and parse it

        Example:
        - List -> GET
        - Update -> PUT
        """
        return self.METHOD_MAP.get(grpc_action, "POST")


class RequestMeta(CaseInsensitiveMapping):
    """
    Class allowing specific automatic transformation/matching behavior between HTTP headers format expected by django and gRPC metadata format
    """

    HTTP_PREFIX = HttpHeaders.HTTP_PREFIX  # = HTTP_

    def __getitem__(self, key):
        """
        As HTTP headers are prefixed by HTTP_ by proxy server or CGI, Django store and retrieve headers with HTTP_ prefix
        As there is no same rule/restriction in gRPC, we need to check if the key is in the dict without HTTP_ prefix if not existing with
        """
        # INFO - AM - 27/07/2024 - First we detect that the key is not existing and that it's a HTTP header
        if key.lower() not in self._store and key.startswith(self.HTTP_PREFIX):
            key = key[len(self.HTTP_PREFIX) :]
            # INFO - AM - 27/07/2024 - Then we check if maybe the key exist but with hypen instead of underscore
            if key.lower() not in self._store and key.replace("_", "-").lower() in self._store:
                key = key.replace("_", "-")
        return super().__getitem__(key=key)

    def __setitem__(self, key, value):
        """See: https://github.com/django/django/blob/main/django/utils/datastructures.py#L305"""
        self._store[key.lower()] = (key, value)
