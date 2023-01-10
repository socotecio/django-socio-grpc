import abc
import asyncio
import logging
import sys
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Type

import grpc
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed
from django.core.handlers.base import BaseHandler
from django.utils.module_loading import import_string
from google.protobuf.message import Message

from django_socio_grpc.exceptions import GRPCException, Unimplemented
from django_socio_grpc.log import GRPCHandler
from django_socio_grpc.request_transformer.grpc_socio_proxy_context import (
    GRPCSocioProxyContext,
)
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.utils import isgeneratorfunction, safe_async_response

if TYPE_CHECKING:
    from django_socio_grpc.services import Service

logger = logging.getLogger("django_socio_grpc")


@dataclass
class GRPCRequestContainer:
    message: Message
    context: GRPCSocioProxyContext
    action: str
    service: "Service"


class MiddlewareCapable(metaclass=abc.ABCMeta):
    """
    Allows to define middlewares that can be used in sync and async mode.
    Most of the code is taken from django.core.handlers.base.BaseHandler
    https://github.com/django/django/blob/main/django/core/handlers/base.py
    """

    _middleware_chain = None

    adapt_method_mode = BaseHandler.adapt_method_mode

    def load_middleware(self, is_async=False):
        """
        Populate middleware lists from settings.GRPC_MIDDLEWARE.
        """

        handler = self._get_response_async if is_async else self._get_response
        handler_is_async = is_async
        for middleware_path in reversed(grpc_settings.GRPC_MIDDLEWARE):
            middleware = import_string(middleware_path)
            middleware_can_sync = getattr(middleware, "sync_capable", True)
            middleware_can_async = getattr(middleware, "async_capable", False)
            if not middleware_can_sync and not middleware_can_async:
                raise RuntimeError(
                    "Middleware %s must have at least one of "
                    "sync_capable/async_capable set to True." % middleware_path
                )
            elif not handler_is_async and middleware_can_sync:
                middleware_is_async = False
            else:
                middleware_is_async = middleware_can_async
            try:
                # Adapt handler, if needed.
                adapted_handler = self.adapt_method_mode(
                    middleware_is_async,
                    handler,
                    handler_is_async,
                    debug=settings.DEBUG,
                    name="middleware %s" % middleware_path,
                )
                mw_instance = middleware(adapted_handler)
            except MiddlewareNotUsed as exc:
                if settings.DEBUG:
                    if str(exc):
                        logger.debug("MiddlewareNotUsed(%r): %s", middleware_path, exc)
                    else:
                        logger.debug("MiddlewareNotUsed: %r", middleware_path)
                continue
            else:
                handler = adapted_handler

            if mw_instance is None:
                raise ImproperlyConfigured(
                    "Middleware factory %s returned None." % middleware_path
                )

            handler = mw_instance
            handler_is_async = middleware_is_async

        # Adapt the top of the stack, if needed.
        handler = self.adapt_method_mode(is_async, handler, handler_is_async)
        # We only assign to this when initialization is complete as it is used
        # as a flag for initialization being complete.
        self._middleware_chain = handler

    @abc.abstractmethod
    def _get_response(self, request: GRPCRequestContainer):
        ...

    @abc.abstractmethod
    async def _get_response_async(self, request: GRPCRequestContainer):
        ...


class ServicerProxy(MiddlewareCapable):

    """
    gRPC call
        ↓
    `ServicerProxy.__getattr__(action)`
        ↓
    `ServicerProxy.get_handler(action)`
        ↓
    `ServicerProxy.[correct handler]` (sync or async and stream or not)
        ↓
    `return _middleware_chain` (from setting GRPC_MIDDLEWARE)
        ↓... middleware 1
            ↓... middleware 2
                ↓... middleware n
                    ↓ `ServicerProxy._get_response` (sync or async)
                ...
            ...
        ...

    """

    def __init__(self, service_class: Type["Service"], **initkwargs):
        self.service_class = service_class
        self.initkwargs = initkwargs

        self.load_middleware(is_async=grpc_settings.GRPC_ASYNC)

    def _get_response(self, request: GRPCRequestContainer):
        action = getattr(request.service, request.action)
        if asyncio.iscoroutinefunction(action):
            action = async_to_sync(action)
        try:
            request.service.before_action()
            return action(request.message, request.context)
        except Exception as e:
            self.process_exception(e, request)
        finally:
            request.service.after_action()

    async def _get_response_async(self, request: GRPCRequestContainer):
        def wrapped_action(request: GRPCRequestContainer):
            return getattr(request.service, request.action)(request.message, request.context)

        try:
            await request.service.before_action()
            return await safe_async_response(
                wrapped_action,
                request,
                self.async_process_exception,
            )
        finally:
            await request.service.after_action()

    def _get_async_stream_handler(self, action: str):
        async def handler(request: Message, context):
            proxy_context = GRPCSocioProxyContext(context, action)
            service_instance = self.create_service(
                request=request, context=proxy_context, action=action
            )
            request = GRPCRequestContainer(request, proxy_context, action, service_instance)
            async for response in await safe_async_response(
                self._middleware_chain, request, self.async_process_exception
            ):
                yield response

        return handler

    def _get_async_handler(self, action: str):
        async def handler(request: Message, context):
            proxy_context = GRPCSocioProxyContext(context, action)
            service_instance = self.create_service(
                request=request, context=proxy_context, action=action
            )
            request = GRPCRequestContainer(request, proxy_context, action, service_instance)
            return await safe_async_response(
                self._middleware_chain, request, self.async_process_exception
            )

        return handler

    def _get_handler(self, action: str):
        def handler(request: Message, context):
            proxy_context = GRPCSocioProxyContext(context, action)
            service_instance = self.create_service(
                request=request, context=proxy_context, action=action
            )
            request = GRPCRequestContainer(request, proxy_context, action, service_instance)
            try:
                return self._middleware_chain(request)
            except Exception as e:
                self.process_exception(e, request)

        return handler

    def _get_stream_handler(self, action: str):
        def handler(request: Message, context):
            proxy_context = GRPCSocioProxyContext(context, action)
            service_instance = self.create_service(
                request=request, context=proxy_context, action=action
            )
            request = GRPCRequestContainer(request, proxy_context, action, service_instance)
            try:
                yield from self._middleware_chain(request)
            except Exception as e:
                self.process_exception(e, request)

        return handler

    def get_handler(self, action: str):
        service_action = getattr(self.service_class, action)

        if grpc_settings.GRPC_ASYNC:
            if isgeneratorfunction(service_action):
                return self._get_async_stream_handler(action)
            return self._get_async_handler(action)

        if isgeneratorfunction(service_action):
            return self._get_stream_handler(action)
        return self._get_handler(action)

    def create_service(self, **kwargs):
        return self.service_class(**self.initkwargs, **kwargs)

    def __getattr__(self, action):
        if not hasattr(self.service_class, action):
            raise Unimplemented()

        return self.get_handler(action)

    def process_exception(self, exc, request: GRPCRequestContainer):
        if isinstance(exc, GRPCException):
            logger.error(exc)
            request.context.abort(exc.status_code, exc.get_full_details())
        elif isinstance(exc, grpc.RpcError):
            raise exc
        else:
            etype, value, tb = sys.exc_info()
            formatted_exception = traceback.format_exception(etype, value, tb)
            # No need to send it to µservices logging because we did it as exception with log_unhandled_exception
            logger.error("".join(formatted_exception), extra={"emit_to_server": False})
            grpc_handler = GRPCHandler()
            grpc_handler.log_unhandled_exception(etype, value, tb)
            request.context.abort(grpc.StatusCode.UNKNOWN, str(exc))

    async def async_process_exception(self, exc, request: GRPCRequestContainer):
        if isinstance(exc, GRPCException):
            logger.error(exc)
            await request.context.abort(exc.status_code, exc.get_full_details())
        elif isinstance(exc, grpc.RpcError):
            raise exc
        else:
            etype, value, tb = sys.exc_info()
            formatted_exception = traceback.format_exception(etype, value, tb)
            # No need to send it to µservices logging because we did it as exception with log_unhandled_exception
            logger.error("".join(formatted_exception), extra={"emit_to_server": False})
            grpc_handler = GRPCHandler()
            grpc_handler.log_unhandled_exception(etype, value, tb)
            await request.context.abort(grpc.StatusCode.UNKNOWN, str(exc))
