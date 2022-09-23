import json

from django_socio_grpc.settings import grpc_settings


class SocioProxyHttpRequest:
    HEADERS_KEY = "HEADERS"
    MAP_HEADERS = {"AUTHORIZATION": "HTTP_AUTHORIZATION"}
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

        self.grpc_request_metadata = self.convert_metadata_to_dict(
            grpc_context.invocation_metadata()
        )
        self.headers = self.get_from_metadata(self.HEADERS_KEY)
        self.META = {
            self.MAP_HEADERS.get(key.upper()): value for key, value in self.headers.items()
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

    def get_from_metadata(self, metadata_key):
        metadata_key = grpc_settings.MAP_METADATA_KEYS.get(metadata_key, None)
        if not metadata_key:
            return self.grpc_request_metadata
        return json.loads(self.grpc_request_metadata.get(metadata_key, "{}"))

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


class GRPCSocioProxyContext:
    """Proxy context, provide http1 proxy request object
    and grpc context object"""

    def __init__(self, grpc_context, grpc_action):
        self.grpc_context = grpc_context
        self.proxy_http_request = SocioProxyHttpRequest(self, grpc_action)

    def __getattr__(self, attr):
        try:
            if hasattr(self.grpc_context, attr):
                return getattr(self.grpc_context, attr)
            if hasattr(self.proxy_http_request, attr):
                return getattr(self.proxy_http_request, attr)
        except AttributeError:
            return self.__getattribute__(attr)
