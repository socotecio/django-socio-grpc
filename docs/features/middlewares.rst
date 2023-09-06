.. _middleware:

Middlewares
===========

Description
-----------

Middleware functions in Django allow you to process requests and responses globally before they reach the view or after they leave the view. These middleware functions are wrapped with the sync_and_async_middleware decorator, indicating that they are compatible with both synchronous and asynchronous code.
Middlewares in Django-Socio-GRPC are made to be almost compatible with django middlewares, the only difference is the argument being of type django_socio_grpc.request_transformer.GRPCRequestContainer
For more information see (`here <https://docs.djangoproject.com/en/4.2/topics/http/middleware/>`_).

Usage
-----

================================
close_old_connections_middleware
================================

- This middleware is responsible for closing old database connections at the beginning and end of a request/response cycle.
- It resets database queries and ensures that unused database connections are closed.
- It uses the _close_old_connections function to close connections.
- The middleware is asynchronous when get_response is an asynchronous function, and it uses safe_async_response to handle potential asynchronous responses.


=======================
log_requests_middleware
=======================

- This middleware logs information about incoming gRPC requests.
- It logs the service action being called unless it's listed in the grpc_settings.IGNORE_LOG_FOR_ACTION setting.
- It is asynchronous when get_response is an asynchronous function and uses safe_async_response to handle potential asynchronous responses

=================
locale_middleware
=================

- This middleware sets the language for the current request based on the request context.
- It activates the translation engine with the detected language.
- It is asynchronous when get_response is an asynchronous function and uses safe_async_response to handle potential asynchronous responses.

===============================
auth_without_session_middleware
===============================

- This middleware is used to replace the default Django Authentication Middleware when using authentication patterns other than session-based authentication (e.g., Token-based).
- It calls the perform_authentication method of the gRPC service to perform authentication.
- It should be placed before any other middleware that depends on the context.user attribute.
- The middleware is asynchronous when get_response is an asynchronous function, and it uses safe_async_response to handle potential asynchronous responses.


Each middleware function follows a similar pattern, where it performs its specific task and then passes the request/response further down the middleware stack using get_response. The choice between synchronous and asynchronous execution depends on whether get_response is synchronous or asynchronous. These middleware functions provide custom behavior for gRPC requests and responses in the Django application.

Example
-------
In your settings.py, you can include middlewares in GRPC_MIDDLEWARE section. More details here : :ref:`Available Settings <Available Settings>`.

.. code-block:: python

    GRPC_FRAMEWORK = {
        ...
        "GRPC_MIDDLEWARE": [
            "django_socio_grpc.middlewares.close_old_connections_middleware",
            "django_socio_grpc.middlewares.auth_without_session_middleware",
            "django_socio_grpc.middlewares.log_requests_middleware",
        ],
    }
