"""
Settings for gRPC framework are all namespaced in the GRPC_FRAMEWORK setting.
For example your project's `settings.py` file might look like this:

GRPC_FRAMEWORK = {
    "ROOT_HANDLERS_HOOK": "path.to.your.handler.function"
    ...
}

To see all options see documentation: https://django-socio-grpc.readthedocs.io/en/stable/

This module provides the `grpc_setting` object, that is used to access
gRPC framework settings, checking for user settings first, then falling
back to the defaults.
"""
from enum import Enum

from django.conf import settings
from django.core.signals import setting_changed
from django.utils.module_loading import import_string

__all__ = ["grpc_settings"]


# TODO - AM - 20/02/2024 - replace (str, Enum) by (StrEnum) when python requirements > 3.11. https://docs.python.org/fr/3/library/enum.html#enum.StrEnum
class FilterAndPaginationBehaviorOptions(str, Enum):
    """
    FilterAndPaginationBehaviorOptions is an StrEnum that present the congiguration possibilities for PAGINATION_BEHAVIOR and FILTER_BEHAVIOR.

    The mains differences between metadata and request are:
    - Metadata are not specified in the proto file so adding or removing a filter in a new version is not documented and may cause breaking changes.
    - Requests allows helping developpers understand which endpoint accept filtering and automatically document it
    - Requests are serialized so it can improve performance when filtering large amount of data
    """

    METADATA_STRICT = "METADATA_STRICT"
    """
    Only allow the element choosen against metadata. This is the default behavior as it's the legacy way of pagination. This will change for 1.0.0. This mode doesn't add additional fields into the messages.
    """

    REQUEST_STRUCT_STRICT = "REQUEST_STRUCT_STRICT"
    """
    Only allow to use the element choosen against request field (``_filters`` or ``_pagination``). This mode add the specifis key (``_filters`` or ``_pagination``) in every message except if service specifically disable it.
    """

    METADATA_AND_REQUEST_STRUCT = "METADATA_AND_REQUEST_STRUCT"
    """
    Allow pagination against metadata and request field (``_filters`` or ``_pagination``). This mode add the specific key (``_filters`` or ``_pagination``) in every message except if service specifically disable it. If filter is present in both metadata and request field, the one in request field have priority. You should only use this mode when transitionning from metadata to request as having both is not recommended and could bring clarity issues
    """

    # More complicated and will be implented late 2024: https://github.com/socotecio/django-socio-grpc/issues/247
    # FILTER_MESSAGE_STRICT = "METADATA_STRICT"
    # METADATA_AND_FILTER_MESSAGE = "METADATA_AND_FILTER_MESSAGE"


DEFAULTS = {
    # Root grpc handlers hook configuration
    "ROOT_HANDLERS_HOOK": None,
    # gRPC server configuration. ex: [Interceptor1(), Interceptor2()]
    "SERVER_INTERCEPTORS": None,
    # gRPC server options. See https://grpc.github.io/grpc/python/grpc_asyncio.html#create-server, https://github.com/grpc/grpc/blob/v1.46.x/include/grpc/impl/codegen/grpc_types.h
    "SERVER_OPTIONS": None,
    # Default servicer authentication classes
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    # Default filter class. ex: ['django_filters.rest_framework.DjangoFilterBackend'],
    "DEFAULT_FILTER_BACKENDS": [],
    # default pagination class. ex: 'rest_framework.pagination.Pagenumberpagination'
    "DEFAULT_PAGINATION_CLASS": None,
    # Default permission classes
    "DEFAULT_PERMISSION_CLASSES": [],
    # gRPC running mode
    "GRPC_ASYNC": False,
    # Default grpc channel port
    "GRPC_CHANNEL_PORT": 50051,
    # Separate request and response message for model to activate read_only, write_only property of serilizer
    "SEPARATE_READ_WRITE_MODEL": True,
    # List of all middleware classes to be used for gRPC framework
    "GRPC_MIDDLEWARE": [
        "django_socio_grpc.middlewares.log_requests_middleware",
        "django_socio_grpc.middlewares.close_old_connections_middleware",
    ],
    # Root GRPC folder for external grpc handlers
    "ROOT_GRPC_FOLDER": "grpc_folder",
    # Default places where to search headers, pagination and filter data
    "MAP_METADATA_KEYS": {
        "HEADERS": "HEADERS",
        "PAGINATION": "PAGINATION",
        "FILTERS": "FILTERS",
    },
    # [DEPRECATED]. See https://django-socio-grpc.readthedocs.io/en/latest/how-to/add-extra-context-to-logging.html. Get extra data from service when using log middleware or processing exception in django-socio-grpc
    "LOG_EXTRA_CONTEXT_FUNCTION": "django_socio_grpc.log.default_get_log_extra_context",
    # Log requests even for response OK
    "LOG_OK_RESPONSE": False,
    # List service action that we do not want to be logged (health check for example) to avoid log flooding. ex: ['Service1.Action1', 'Service1.Action1']
    "IGNORE_LOG_FOR_ACTION": [],
    # An iterable containing pairs path for server certificate. See https://grpc.github.io/grpc/python/grpc.html#create-server-credentials and https://github.com/grpc/grpc/tree/master/examples/python/auth.
    # Exemple of usage: PRIVATE_KEY_CERTIFICATE_CHAIN_PAIRS_PATH: [("server-key.pem", "server.pem")]
    "PRIVATE_KEY_CERTIFICATE_CHAIN_PAIRS_PATH": [],
    # Path to the root certificate pem file. See https://grpc.github.io/grpc/python/grpc.html#grpc.ServerCredentials
    "ROOT_CERTIFICATES_PATH": None,
    # Set the ssl_server_credentials require_client_auth attribute
    "REQUIRE_CLIENT_AUTH": False,
    # Prefered filter mode capability. See FilterAndPaginationBehaviorOptions for options
    # /!\ for 1.O.0 the default behavior will change from METADATA_STRICT to METADATA_AND_FILTER_MESSAGE
    "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.METADATA_STRICT,
    # Prefered pagination mode capability. See FilterAndPaginationBehaviorOptions for options
    # /!\ for 1.O.0 the default behavior will change from METADATA_STRICT to METADATA_AND_FILTER_MESSAGE
    "PAGINATION_BEHAVIOR": FilterAndPaginationBehaviorOptions.METADATA_STRICT,
    # Variable that indicate the class used to generate the name of the proto messages
    "DEFAULT_MESSAGE_NAME_CONSTRUCTOR": "django_socio_grpc.protobuf.message_name_constructor.DefaultMessageNameConstructor",
    # Variable that indicate the plugins used in proto generation by default
    "DEFAULT_GENERATION_PLUGINS": [],
}


# List of settings that may be in string import notation.
IMPORT_STRINGS = [
    "ROOT_HANDLERS_HOOK",
    "DEFAULT_AUTHENTICATION_CLASSES",
    "DEFAULT_PERMISSION_CLASSES",
    "DEFAULT_PAGINATION_CLASS",
    "DEFAULT_FILTER_BACKENDS",
    "LOG_EXTRA_CONTEXT_FUNCTION",
    "DEFAULT_MESSAGE_NAME_CONSTRUCTOR",
]


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        # We need the ROOT_URLCONF so we do this lazily
        if setting_name == "ROOT_HANDLERS_HOOK":
            return import_from_string(
                "%s.grpc_handlers" % settings.ROOT_URLCONF,
                setting_name,
            )
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        raise ImportError(
            "Could not import '%s' for GRPC setting '%s'. %s: %s."
            % (val, setting_name, e.__class__.__name__, e)
        )


class GRPCSettings:
    """
    A settings object that allows gRPC Framework settings to be accessed as
    properties. For example:

        from django_socio_grpc.settings import grpc_settings
        print(grpc_settings.ROOT_HANDLERS_HOOK)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """

    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "GRPC_FRAMEWORK", {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid gRPC setting: '%s'" % attr)
        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


grpc_settings = GRPCSettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_grpc_settings(*args, **kwargs):
    setting = kwargs["setting"]
    if setting == "GRPC_FRAMEWORK" or setting == "ROOT_URLCONF":
        grpc_settings.reload()


setting_changed.connect(reload_grpc_settings)
