import json

from django_socio_grpc.settings import grpc_settings
from django.utils.encoding import escape_uri_path, iri_to_uri
from django.conf import settings


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

    #  Map http method to use DjangoModelPermission
    METHOD_MAP = {
        "List": "GET",
        "Retrieve": "GET",
        "Create": "POST",
        "Update": "PUT",
        "PartialUpdate": "PATCH",
        "Destroy": "DELETE",
    }

    def __init__(self, grpc_context, grpc_action):
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

        # Computed params
        self.query_params = self.get_query_params()
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

    def convert_metadata_to_dict(self, invocation_metadata):
        grpc_request_metadata = {}
        for key, value in dict(invocation_metadata).items():
            grpc_request_metadata[key.upper()] = value
        return grpc_request_metadata

    def get_query_params(self):
        return {
            **self.get_from_metadata(self.FILTERS_KEY),
            **self.get_from_metadata(self.PAGINATION_KEY),
        }

    def build_absolute_uri(self):
        return "NYI"

    def grpc_action_to_http_method_name(self, grpc_action):
        return self.METHOD_MAP.get(grpc_action, None)

    def get_full_path(self, force_append_slash=False):
        return self._get_full_path(self.path, force_append_slash)

    def _get_full_path(self, path, force_append_slash):
        # RFC 3986 requires query string arguments to be in the ASCII range.
        # Rather than crash if this doesn't happen, we encode defensively.
        return "%s%s%s" % (
            escape_uri_path(path),
            "/" if force_append_slash and not path.endswith("/") else "",
            ("?" + iri_to_uri(self.META.get("QUERY_STRING", "")))
            if self.META.get("QUERY_STRING", "")
            else "",
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

