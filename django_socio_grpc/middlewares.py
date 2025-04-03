"""https://docs.djangoproject.com/en/5.0/topics/http/middleware
For now only the __call__ method of a middleware is supported

To use async middlewares, you need to use the correct decorator
Here we use the sync_and_async_middleware decorators to declare these
middlewares as sync and async compatible
"""

import asyncio
import logging
from collections.abc import Callable

from asgiref.sync import async_to_sync, sync_to_async
from django.utils import translation
from django.utils.decorators import sync_and_async_middleware
from django.utils.translation import get_language_from_request

from django_socio_grpc.services.servicer_proxy import GRPCRequestContainer
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.utils import safe_async_response

logger = logging.getLogger("django_socio_grpc.middlewares")


_HAS_LOGGED_OLD_CONNECTIONS_DEPRECATION = False


@sync_and_async_middleware
def close_old_connections_middleware(get_response: Callable):
    """
    Deprecated middleware to close old connections.
    """
    global _HAS_LOGGED_OLD_CONNECTIONS_DEPRECATION
    if not _HAS_LOGGED_OLD_CONNECTIONS_DEPRECATION:
        logger.warning(
            "The 'django._socio_grpc.close_old_connections' middleware is deprecated and obsolete, "
            "remove it from your GRPC_MIDDLEWARE setting."
        )
        _HAS_LOGGED_OLD_CONNECTIONS_DEPRECATION = True
    return get_response


def _log_requests(request: GRPCRequestContainer):
    if (
        f"{request.service.__class__.__name__}.{request.action}"
        not in grpc_settings.IGNORE_LOG_FOR_ACTION
    ):
        logger.info(
            f"Receive action {request.action} on service {request.service.__class__.__name__}",
        )


@sync_and_async_middleware
def log_requests_middleware(get_response: Callable):
    """
    Simple middleware to print wich request being call before starting the action code.
    Sync and Async supported.
    """
    if asyncio.iscoroutinefunction(get_response):

        async def middleware(request: GRPCRequestContainer):
            _log_requests(request)
            return await safe_async_response(get_response, request)

    else:

        def middleware(request: GRPCRequestContainer):
            _log_requests(request)
            return get_response(request)

    return middleware


@sync_and_async_middleware
def locale_middleware(get_response: Callable):
    """
    Middleware to activate i18n language in django.
    It will look for an Accept-Language formated metadata in the headers key.
    metadata = ('headers', ('accept-language', 'fr-CH, fr;q=0.9, en;q=0.8, de;'))
    """
    if asyncio.iscoroutinefunction(get_response):

        async def middleware(request: GRPCRequestContainer):
            language = get_language_from_request(request.context)
            translation.activate(language)
            return await safe_async_response(get_response, request)

    else:

        def middleware(request: GRPCRequestContainer):
            language = get_language_from_request(request.context)
            translation.activate(language)
            return get_response(request)

    return middleware


@sync_and_async_middleware
def auth_without_session_middleware(get_response: Callable):
    """
    This middleware is here to replace Django default Authentication Middleware as it look for the user session created by the login django method.
    This middleware is to use when using other Authenifciation pattern such as Token one.

    This middleware call the perform_authentication of the service. It should be placed before any other middleware that need context.user.
    If this middleware is not installed the authentication will still perform but after the execution of all the middleware.
    """
    if asyncio.iscoroutinefunction(get_response):

        async def middleware(request: GRPCRequestContainer):
            if asyncio.iscoroutinefunction(request.service.perform_authentication):
                await request.service.perform_authentication()
            else:
                await sync_to_async(request.service.perform_authentication)()
            return await safe_async_response(get_response, request)

    else:

        def middleware(request: GRPCRequestContainer):
            if asyncio.iscoroutinefunction(request.service.perform_authentication):
                async_to_sync(request.service.perform_authentication)()
            else:
                request.service.perform_authentication()
            return get_response(request)

    return middleware
