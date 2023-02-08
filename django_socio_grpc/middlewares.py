""" https://docs.djangoproject.com/fr/4.1/topics/http/middleware
For now only the __call__ method of a middleware is supported

To use async middlewares, you need to use the correct decorator
Here we use the sync_and_async_middleware decorators to declare these
middlewares as sync and async compatible
"""

import asyncio
import logging

from asgiref.sync import sync_to_async
from django import db
from django.utils.decorators import sync_and_async_middleware

from django_socio_grpc.services.servicer_proxy import GRPCRequestContainer
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.utils import safe_async_response

logger = logging.getLogger("django_socio_grpc")


def _close_old_connections():
    for conn in db.connections.all():
        if conn.connection is None:
            continue
        if conn.get_autocommit():
            conn.close_if_unusable_or_obsolete()


@sync_and_async_middleware
def close_old_connections_middleware(get_response):
    if asyncio.iscoroutinefunction(get_response):

        async def middleware(request: GRPCRequestContainer):
            db.reset_queries()
            await sync_to_async(_close_old_connections)()
            try:
                # INFO - L.G. - 03/01/2023 - We need to use safe_async_response here
                # because get_response might return a generator
                return await safe_async_response(get_response, request)
            finally:
                await sync_to_async(_close_old_connections)()

    else:

        def middleware(request: GRPCRequestContainer):
            db.reset_queries()
            _close_old_connections()
            try:
                return get_response(request)
            finally:
                _close_old_connections()

    return middleware


def _log_requests(request: GRPCRequestContainer):
    if (
        f"{request.service.__class__.__name__}.{request.action}"
        not in grpc_settings.IGNORE_LOG_FOR_ACTION
    ):
        logger.info(
            f"Receive action {request.action} on service {request.service.__class__.__name__}"
        )


@sync_and_async_middleware
def log_requests_middleware(get_response):
    if asyncio.iscoroutinefunction(get_response):

        async def middleware(request: GRPCRequestContainer):
            _log_requests(request)
            return await safe_async_response(get_response, request)

    else:

        def middleware(request: GRPCRequestContainer):
            _log_requests(request)
            return get_response(request)

    return middleware
