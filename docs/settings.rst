Settings
=============

Available Settings
------------------
.. _Available Settings:

These are the default settings for Django Socio GRPC, with explanations provided below.
These settings should be defined under the ``GRPC_FRAMEWORK`` variable in django settings.
See the documentation on django settings if your not familiar with it: `Django settings documentation <https://docs.djangoproject.com/en/4.2/topics/settings/>`_.

.. code-block:: python

  GRPC_FRAMEWORK = {
    "ROOT_HANDLERS_HOOK": None,
    "SERVER_INTERCEPTORS": None,
    "SERVER_OPTIONS": None,
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_FILTER_BACKENDS": [],
    "DEFAULT_PAGINATION_CLASS": None,
    "DEFAULT_PERMISSION_CLASSES": [],
    "GRPC_ASYNC": False,
    "GRPC_CHANNEL_PORT": 50051,
    "SEPARATE_READ_WRITE_MODEL": True,
    "GRPC_MIDDLEWARE": [
      "django_socio_grpc.middlewares.log_requests_middleware",
      "django_socio_grpc.middlewares.close_old_connections_middleware",
    ],
    "ROOT_GRPC_FOLDER": "grpc_folder",
    "MAP_METADATA_KEYS": {
      "HEADERS": "HEADERS",
      "PAGINATION": "PAGINATION",
      "FILTERS": "FILTERS",
    },
  }


ROOT_HANDLERS_HOOK
^^^^^^^^^^^^^^^^^^

This setting points to the `grpc_handlers` function within a specified module, responsible for registering all gRPC handlers for the project's applications. Each application has its own handler, which in turn registers the gRPC services it employs. As a result, incoming gRPC requests or events trigger the appropriate service using the handlers' map. This function runs just before the start of the server, making it useful for any other kind of initialization

See Register services section in the Getting Started documentation to see an example of grpc_handlers method.

For a project named "my_project" with the `grpc_handlers` function inside `my_project/handlers.py`, the configuration would be:

.. code-block:: python

  "ROOT_HANDLERS_HOOK": "my_project.handlers.grpc_handlers"

SERVER_INTERCEPTORS
^^^^^^^^^^^^^^^^^^^
This setting specifies a list of gRPC server interceptors. Interceptors allow you to run custom code before or after a gRPC method gets executed. Common uses for interceptors include logging, authentication, and request/response transformations.

Example:

Consider you have two interceptors, LoggingInterceptor and AuthenticationInterceptor. These interceptors would be added to the SERVER_INTERCEPTORS setting as:

.. code-block:: python

  "SERVER_INTERCEPTORS": [LoggingInterceptor(), AuthenticationInterceptor()],

With this configuration, every gRPC method invocation will first pass through the LoggingInterceptor and then the AuthenticationInterceptor before the actual gRPC method is executed.

See the ServerInterceptor documentation for Python : `sync <https://grpc.github.io/grpc/python/grpc.html#grpc.ServerInterceptor>_` and `async <https://grpc.github.io/grpc/python/grpc_asyncio.html#grpc.aio.ServerInterceptor>_`.

SERVER_OPTIONS
^^^^^^^^^^^^^^

This setting defines a list of key-value pairs specifying options for the gRPC server. These options help configure server behavior, such as setting limits on the size of incoming or outgoing messages.

Example:

If you want to set the maximum size for sending and receiving messages to 100MB, you can configure the SERVER_OPTIONS as:

.. code-block:: python

  "SERVER_OPTIONS": [
    ("grpc.max_send_message_length", 100 * 1024 * 1024),
    ("grpc.max_receive_message_length", 100 * 1024 * 1024),
  ],

The above configuration allows the gRPC server to send and receive messages up to a size of 100MB.

For more options, see the `documentation <https://grpc.github.io/grpc/core/group__grpc__arg__keys.html>`_.


DEFAULT_AUTHENTICATION_CLASSES
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Defines the list of authentication classes the gRPC server uses to validate incoming requests. Requests are authenticated based on the methods provided by these classes, in the order they are listed.

Example:

If you want to set the maximum size for sending and receiving messages to 100MB, you can configure the DEFAULT_AUTHENTICATION_CLASSES as:

.. code-block:: python

  "DEFAULT_AUTHENTICATION_CLASSES": [
    "your_project.auth.JWTAuthentication"
  ]

For more details, see the `DRF documentation as DSG use the same system <https://www.django-rest-framework.org/api-guide/authentication/#setting-the-authentication-scheme>`_.

DEFAULT_FILTER_BACKENDS
^^^^^^^^^^^^^^^^^^^^^^^

This setting designates the default filtering backends that gRPC services should use. Filtering backends allow requests to be filtered based on query parameters.

For instance, to use django-filter backend (`doc <https://django-filter.readthedocs.io/en/stable/>`_):

.. code-block:: python

  "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"]


DEFAULT_PAGINATION_CLASS
^^^^^^^^^^^^^^^^^^^^^^^^

Defines the default pagination class for gRPC services. This class will be used to paginate large datasets in the response.

Example configuration to use the `StandardResultsSetPagination` class:

.. code-block:: python

  "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsSetPagination"

For more details, see the `DRF documentation as DSG use the same system <https://www.django-rest-framework.org/api-guide/pagination/>`_.


DEFAULT_PERMISSION_CLASSES
^^^^^^^^^^^^^^^^^^^^^^^^^^

This setting defines the list of default authentication classes that will be used for gRPC services. Each class specified in this list will be responsible for verifying the identity of the user making the request.

For a hypothetical project that uses JWT for authentication:

.. code-block:: python

  "DEFAULT_PERMISSION_CLASSES": [
      "your_project.permissions.IsAuthenticated",
      "your_project.permissions.HasServiceAccess",
  ]

For more details, see the `DRF documentation as DSG use the same system <https://www.django-rest-framework.org/api-guide/permissions/>`_.


GRPC_ASYNC
^^^^^^^^^^

This setting determines the running mode of the gRPC server. If set to `True`, the server will operate in asynchronous mode. When in asynchronous mode, the server is capable of handling multiple concurrent requests using Python's `asyncio`.

This setting is overriden to True when running the app with ``grpcrunaioserver``.

Please consider to always use async as it may become the only accepted behavior in DSG 1.0.

.. code-block:: python

  "GRPC_ASYNC": False

GRPC_CHANNEL_PORT
^^^^^^^^^^^^^^^^^

This is the default port on which the gRPC server will listen for incoming requests. You can change this if your server needs to listen on a different port.

.. code-block:: python

  "GRPC_CHANNEL_PORT": 50051


SEPARATE_READ_WRITE_MODEL
^^^^^^^^^^^^^^^^^^^^^^^^^

The `SEPARATE_READ_WRITE_MODEL` setting determines whether to use separate request and response messages for a model, primarily to activate the `read_only` and `write_only` properties of a serializer. This ensures more granular control over serialized data, where some fields can be made read-only or write-only.

By enabling this option (set to `True`), it ensures that specific fields in a model can be set to be write-only during a write operation and will not be exposed during a read operation, and vice versa for read-only fields. This is particularly useful when certain data should be kept private or when different sets of data should be exposed for reading vs. writing.

For instance, if you have fields in your model that should only be updated but never retrieved in a response, you can mark them as `write_only`. Similarly, fields that should be displayed but never modified can be marked as `read_only`.

Please consider to always use async as it may become the only accepted behavior in DSG 1.0.

.. code-block:: python

  "SEPARATE_READ_WRITE_MODEL": True


GRPC_MIDDLEWARE
^^^^^^^^^^^^^^^

This setting defines a list of middleware classes specifically tailored for the gRPC framework. Middleware in gRPC can be seen as a series of processing units that handle both incoming requests and outgoing responses. They can be used for various tasks like logging, authentication, data enrichment, and more.

Middlewares are processed in the order they are defined. Each middleware should adhere to the gRPC middleware structure, having methods to process requests and responses.
More details about :ref:`middlewares<middleware>`.

The difference with a gRPC Interceptor is that the middlewares occur at the Django level, meaning the request has already been wrapped into a Django-like request. Interceptors handle pure gRPC calls.

For instance, you could have a generic logging middleware that logs every gRPC request and a middleware to handle connection issues:

.. code-block:: python

  "GRPC_MIDDLEWARE": [
      "your_project.middlewares.GenericLoggingMiddleware",
      "your_project.middlewares.ConnectionHandlingMiddleware",
  ]

ROOT_GRPC_FOLDER
^^^^^^^^^^^^^^^^

This setting specifies the root directory name where all the
generated proto files of external services are outputted.
More details about
:ref:`how to define proto and service in a shared library<define-proto-and-service-in-a-shared-library>`.

.. code-block:: python

  "ROOT_GRPC_FOLDER": "my_root_grpc_folder"

MAP_METADATA_KEYS
^^^^^^^^^^^^^^^^^

This setting defines where the framework should look within the metadata for
specific pieces of information like headers, pagination data, and filters.
Essentially, it provides mapping keys that indicate where to extract certain types of metadata.

For a standard configuration, you might have:

.. code-block:: python

  "MAP_METADATA_KEYS": {
      "HEADERS": "HEADERS",
      "PAGINATION": "PAGINATION",
      "FILTERS": "FILTERS",
  }

This means that when the framework encounters metadata, it knows to look for a ``HEADERS``
key to retrieve headers, a ``PAGINATION`` key to fetch pagination data, and a ``FILTERS`` key
for filtering details.

LOG_OK_RESPONSE
^^^^^^^^^^^^^^^

This setting enables the logging of requests that return an OK.
Default is False. Being in DEBUG mode enables it.

.. code-block:: python

  "LOG_OK_RESPONSE": True
