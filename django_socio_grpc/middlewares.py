import asyncio
import logging

from asgiref.sync import sync_to_async
from django import db
from django.utils.decorators import sync_and_async_middleware

from django_socio_grpc.servicer_proxy import GRPCRequestContainer
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.utils import safe_async_response

logger = logging.getLogger("django_socio_grpc")


@sync_and_async_middleware
def close_old_connections_middleware(get_response):
    if asyncio.iscoroutinefunction(get_response):

        async def middleware(request):
            db.reset_queries()
            await sync_to_async(_close_old_connections)()
            try:
                return await safe_async_response(get_response, request)
            finally:
                await sync_to_async(_close_old_connections)()

    else:

        def middleware(request):
            db.reset_queries()
            _close_old_connections()
            try:
                return get_response(request)
            finally:
                _close_old_connections()

    return middleware


@sync_and_async_middleware
def log_requests_middleware(get_response):
    if asyncio.iscoroutinefunction(get_response):

        async def middleware(request: GRPCRequestContainer):
            if (
                f"{request.proxy.service_class.__name__}.{request.action}"
                not in grpc_settings.IGNORE_LOG_FOR_ACTION
            ):
                logger.info(
                    f"Receive action {request.action} on service {request.proxy.service_class.__name__}"
                )
            return await safe_async_response(get_response, request)

    else:

        def middleware(request: GRPCRequestContainer):
            if (
                f"{request.proxy.service_class.__name__}.{request.action}"
                not in grpc_settings.IGNORE_LOG_FOR_ACTION
            ):
                logger.info(
                    f"Receive action {request.action} on service {request.proxy.service_class.__name__}"
                )
            return get_response(request)

    return middleware


def _close_old_connections():
    for conn in db.connections.all():
        if conn.connection is None:
            continue
        if conn.get_autocommit():
            conn.close_if_unusable_or_obsolete()
