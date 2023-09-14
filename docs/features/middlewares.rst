.. _middleware:

Middlewares
===========

Description
-----------

Middleware functions in Django allow you to process requests and responses globally before they reach the view or after they leave the view.
Middlewares in DSG are made to be compatible with Django ones for most cases, the difference is the argument being of type ``django_socio_grpc.request_transformer.GRPCRequestContainer``
For more information see (`here <https://docs.djangoproject.com/en/4.2/topics/http/middleware/>`_).

To use a middleware, you need to add it to the `GRPC_MIDDLEWARE` list in your :ref:`DSG Settings <Available Settings>`. The order of the middleware is important, as they will be executed in order.

Available Middlewares
-----

================================
close_old_connections_middleware
================================

- This middleware is responsible for closing old database connections at the beginning and end of a request/response cycle.
- It resets database queries and ensures that unused database connections are closed.


=======================
log_requests_middleware
=======================

- This middleware logs information about incoming gRPC requests.
- It logs the service action being called unless it's listed in the grpc_settings.IGNORE_LOG_FOR_ACTION setting.

=================
locale_middleware
=================

- This middleware sets the language for the current request based on the request context.
- It activates the translation engine with the detected language.

===============================
auth_without_session_middleware
===============================

- This middleware is used to replace the default Django Authentication Middleware when using authentication
  patterns other than session-based authentication (e.g., Token-based).
- It calls the perform_authentication method of the gRPC service to perform authentication.
- It should be placed before any other middleware that depends on the context.user attribute.


Each middleware function follows a similar pattern, where it performs its specific task and then passes the request/response further down the middleware stack using get_response. The choice between synchronous and asynchronous execution depends on whether get_response is synchronous or asynchronous. These middleware functions provide custom behavior for gRPC requests and responses in the Django application.

Example
-------

This is the source code for the ``locale_middleware`` middleware:

.. code-block:: python

    # This decorator declares the middleware as supporting
    # both synchronous and asynchronous requests.
    @sync_and_async_middleware
    # get_response is the next middleware (or the actual GRPCAction if last)
    def locale_middleware(get_response: Callable):
        # As it is supporting both synchronous and asynchronous requests,
        # it returns a sync or async function depending on the type of get_response.
        if asyncio.iscoroutinefunction(get_response):

            async def middleware(request: GRPCRequestContainer):
                language = get_language_from_request(request.context)
                translation.activate(language)
                # `django_socio_grpc.utils.utils.safe_async_response`
                # is a utility function that wraps the response in a coroutine.
                # The response could be a coroutine or an async generator
                # so we need to wrap it in a coroutine to be able to await it.
                return await safe_async_response(get_response, request)

        else:

            def middleware(request: GRPCRequestContainer):
                language = get_language_from_request(request.context)
                translation.activate(language)
                return get_response(request)

        return middleware
