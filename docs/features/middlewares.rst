.. _middlewares:

Middlewares
===========

Description
-----------

Middleware functions in **Django** allow you to process requests and responses globally before they reach the view or after they leave the view.
Middlewares in DSG are made to be compatible with **Django** ones for most cases, the difference is the argument being of type :func:`django_socio_grpc.request_transformer.GRPCRequestContainer`
For more information see `Django documentation <https://docs.djangoproject.com/en/5.0/topics/http/middleware/>`_.

To use a middleware, you need to add it to the :ref:`GRPC_MIDDLEWARE<settings-grpc-middleware>` list in your :ref:`DSG Settings <Available Settings>`. The order of the middleware is important, as they will be executed in order.

Available Middlewares
---------------------

.. _middlewares-log-requests-middleware:

=======================================================================================
:func:`log_requests_middleware <django_socio_grpc.middlewares.log_requests_middleware>`
=======================================================================================

- This middleware logs information about incoming gRPC requests.
- It logs the service action being called unless it's listed in the :ref:`grpc_settings.IGNORE_LOG_FOR_ACTION<settings-ignore-log-for-action>` setting.

===========================================================================
:func:`locale_middleware <django_socio_grpc.middlewares.locale_middleware>`
===========================================================================

- This middleware sets the language for the current request based on the request context.
- It is used to replace `Django local middleware <https://docs.djangoproject.com/fr/5.0/ref/middleware/#django.middleware.locale.LocaleMiddleware>`_
- It activates the translation engine with the detected language.

=======================================================================================================
:func:`auth_without_session_middleware <django_socio_grpc.middlewares.auth_without_session_middleware>`
=======================================================================================================

- This middleware is used to replace the default `Django Authentication Middleware <https://docs.djangoproject.com/en/5.0/ref/middleware/#django.contrib.auth.middleware.AuthenticationMiddleware>`_ when using authentication
  patterns other than session-based authentication (e.g., Token-based).
- It calls the :func:`perform_authentication<django_socio_grpc.services.base_service.Service.perform_authentication>` method of the gRPC service to perform authentication.
- It should be placed **before any other middleware** that depends on the ``context.user`` attribute.


Each middleware function follows a similar pattern, where it performs its specific task and then passes the request/response further down the middleware stack using get_response. The choice between synchronous and asynchronous execution depends on whether get_response is synchronous or asynchronous. These middleware functions provide custom behavior for gRPC requests and responses in the Django application.

Example
-------

The following example already exist in DSG but it here to help you understand how to create your own.
It's recommended to create them in a created ``my_app.middlewares.py`` file.
Then you can use them with the :ref:`GRPC_MIDDLEWARE<settings-grpc-middleware>` settings.

Source code for the :func:`locale_middleware <django_socio_grpc.middlewares.locale_middleware>` middleware:

.. code-block:: python

    import asyncio
    from typing import Callable
    from django.utils import translation
    from django.utils.decorators import sync_and_async_middleware
    from django_socio_grpc.services.servicer_proxy import GRPCRequestContainer
    from django_socio_grpc.utils.utils import safe_async_response

    # This decorator declares the middleware as supporting
    # both synchronous and asynchronous requests.
    @sync_and_async_middleware
    # get_response is the next middleware (or the actual GRPCAction if last)
    def locale_middleware(get_response: Callable):
        # As it is supporting both synchronous and asynchronous requests,
        # it returns a sync or async function depending on the type of get_response.
        if asyncio.iscoroutinefunction(get_response):

            async def middleware(request: GRPCRequestContainer):
                language = translation.get_language_from_request(request.context)
                translation.activate(language)
                # `django_socio_grpc.utils.utils.safe_async_response`
                # is a utility function that wraps the response in a coroutine.
                # The response could be a coroutine or an async generator
                # so we need to wrap it in a coroutine to be able to await it.
                return await safe_async_response(get_response, request)

        else:

            def middleware(request: GRPCRequestContainer):
                language = translation.get_language_from_request(request.context)
                translation.activate(language)
                return get_response(request)

        return middleware
