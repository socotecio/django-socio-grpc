import json
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import escape_uri_path, iri_to_uri
from google.protobuf.message import Message

from django_socio_grpc.protobuf.json_format import message_to_dict
from django_socio_grpc.settings import FilterAndPaginationBehaviorOptions, grpc_settings

if TYPE_CHECKING:
    from django_socio_grpc.request_transformer.grpc_internal_proxy import (
        GRPCInternalProxyContext,
    )


class InternalHttpRequest:
    """
    Class mocking django.http.HttpRequest to make some django behavior like middleware, filtering, authentication, ... still work.
    TODO - AM - Inherit this directly from django.http.HttpRequest ?
    """

    HEADERS_KEY = "HEADERS"
    MAP_HEADERS = {
        "AUTHORIZATION": "HTTP_AUTHORIZATION",
        "ACCEPT-LANGUAGE": "HTTP_ACCEPT_LANGUAGE",
    }
    FILTERS_KEY = "FILTERS"
    PAGINATION_KEY = "PAGINATION"
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
        self, grpc_context: "GRPCInternalProxyContext", grpc_request: Message, grpc_action: str
    ):
        """
        grpc_context is used to get all the headers and other informations
        grpc_request is only used for filter and pagination from the request if setted by FILTER_BEHAVIOR or PAGINATION_BEHAVIOR settings.
        grpc_action is used to populate InternalHttpRequest.method
        """
        self.user = None
        self.auth = None

        self.grpc_request_metadata = self.convert_metadata_to_dict(
            grpc_context.invocation_metadata()
        )
        self.headers = self.get_from_metadata(self.HEADERS_KEY)
        self.META = {
            self.MAP_HEADERS.get(key.upper(), key.upper()): value
            for key, value in self.headers.items()
        }

        # INFO - A.D.B - 04/01/2021 - Not implemented for now
        self.POST = {}
        self.COOKIES = {}
        self.FILES = {}

        #  Grpc action to http method name
        self.method = self.grpc_action_to_http_method_name(grpc_action)

        # Computed params | grpc_request is passed as argument and not class element because we don't want developer to access to the request from the context proxy
        self.query_params = self.get_query_params(grpc_request)
        # INFO - AM - 10/02/2021 - Only implementing GET because it's easier as we have metadata here. For post we will have to pass the request and transform it to python dict.
        # It's possible but it will be slow the all thing so we hava to param this behavior with settings.
        # So we are waiting for the need to implement it
        self.GET = self.query_params

        # TODO - AM - 26/04/2023 - Find a way to populate this from context or request ? It is really needed ?
        self.path = ""
        self.path_info = ""

    def get_from_metadata(self, metadata_key):
        metadata_key = grpc_settings.MAP_METADATA_KEYS.get(metadata_key, None)
        if not metadata_key:
            return self.grpc_request_metadata
        user_custom_headers = self.grpc_request_metadata.pop(metadata_key, "{}")
        return {
            **self.grpc_request_metadata,
            **json.loads(user_custom_headers),
        }

    def get_from_request_struct(self, grpc_request, struct_field_name):
        # INFO - AM - 14/02/2024 - Need to check both if the request have a _filters key and if this optional _filters is filled
        if hasattr(grpc_request, struct_field_name) and grpc_request.HasField(
            struct_field_name
        ):
            return message_to_dict(getattr(grpc_request, struct_field_name))

        return {}

    def convert_metadata_to_dict(self, invocation_metadata):
        grpc_request_metadata = {}
        for key, value in dict(invocation_metadata).items():
            grpc_request_metadata[key.upper()] = value
        return grpc_request_metadata

    def get_query_params(self, grpc_request: Message):
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
                **self.get_from_metadata(self.FILTERS_KEY),
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
                **self.get_from_metadata(self.PAGINATION_KEY),
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

    def build_absolute_uri(self):
        return "NYI"

    def grpc_action_to_http_method_name(self, grpc_action):
        return self.METHOD_MAP.get(grpc_action, None)

    def get_full_path(self, force_append_slash=False):
        return self._get_full_path(self.path, force_append_slash)

    def _get_full_path(self, path, force_append_slash):
        # RFC 3986 requires query string arguments to be in the ASCII range.
        # Rather than crash if this doesn't happen, we encode defensively.
        return "{}{}{}".format(
            escape_uri_path(path),
            "/" if force_append_slash and not path.endswith("/") else "",
            (
                ("?" + iri_to_uri(self.META.get("QUERY_STRING", "")))
                if self.META.get("QUERY_STRING", "")
                else ""
            ),
        )

    def _get_scheme(self):
        """
        Hook for subclasses like WSGIRequest to implement. Return 'http' by
        default.
        """
        return "http"

    @property
    def scheme(self):
        if settings.SECURE_PROXY_SSL_HEADER:
            try:
                header, secure_value = settings.SECURE_PROXY_SSL_HEADER
            except ValueError:
                raise ImproperlyConfigured(
                    "The SECURE_PROXY_SSL_HEADER setting must be a tuple containing "
                    "two values."
                )
            header_value = self.META.get(header)
            if header_value is not None:
                header_value, *_ = header_value.split(",", 1)
                return "https" if header_value.strip() == secure_value else "http"
        return self._get_scheme()

    def is_secure(self):
        return self.scheme == "https"
