import abc
import asyncio
import logging
from typing import TYPE_CHECKING, AsyncIterable, Awaitable, Callable, Optional, Type

import grpc
from asgiref.local import Local
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed
from django.core.handlers.base import BaseHandler
from django.utils.module_loading import import_string
from google.protobuf.message import Message
from rest_framework.exceptions import APIException

from django_socio_grpc.exceptions import (
    GRPCException,
    Unimplemented,
    get_exception_status_code_and_details,
)
from django_socio_grpc.request_transformer import (
    GRPCInternalProxyResponse,
    GRPCRequestContainer,
    GRPCResponseContainer,
)
from django_socio_grpc.request_transformer.grpc_internal_proxy import GRPCInternalProxyContext
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.utils import isgeneratorfunction, safe_async_response

if TYPE_CHECKING:
    from django_socio_grpc.services import Service

middleware_logger = logging.getLogger("django_socio_grpc.middlewares")
request_logger = logging.getLogger("django_socio_grpc.request")
exception_logger = logging.getLogger("django_socio_grpc.exceptions")


_ServicerCtx = Local()


def get_servicer_context():
    return _ServicerCtx


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
                        middleware_logger.debug(
                            "MiddlewareNotUsed(%r): %s", middleware_path, exc
                        )
                    else:
                        middleware_logger.debug("MiddlewareNotUsed: %r", middleware_path)
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
    def _get_response(self, request_container: GRPCRequestContainer):
        ...

    @abc.abstractmethod
    async def _get_response_async(self, request_container: GRPCRequestContainer):
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

    def _get_response(self, request_container: GRPCRequestContainer) -> GRPCResponseContainer:
        action = getattr(request_container.service, request_container.action)
        if asyncio.iscoroutinefunction(action):
            action = async_to_sync(action)
        try:
            request_container.service.before_action()
            response = action(request_container.grpc_request, request_container.context)
            socio_response = GRPCInternalProxyResponse(response)
            response_container = GRPCResponseContainer(socio_response)
            return response_container
        finally:
            request_container.service.after_action()

    async def _get_response_async(
        self, request_container: GRPCRequestContainer
    ) -> GRPCResponseContainer:
        def wrapped_action(request_container: GRPCRequestContainer):
            return getattr(request_container.service, request_container.action)(
                request_container.grpc_request, request_container.context
            )

        try:
            await request_container.service.before_action()
            response = await safe_async_response(wrapped_action, request_container)
            socio_response = GRPCInternalProxyResponse(response)
            response_container = GRPCResponseContainer(socio_response)
            return response_container
        finally:
            await request_container.service.after_action()

    def _get_async_stream_handler(self, action: str) -> Awaitable[Callable]:
        async def handler(request: Message, context) -> AsyncIterable[Message]:
            proxy_context = GRPCInternalProxyContext(context, request, action)
            service_instance = self.create_service(
                request=request, context=proxy_context, action=action
            )
            request_container = GRPCRequestContainer(
                request, proxy_context, action, service_instance
            )
            try:
                exc = None
                async for response in await safe_async_response(
                    self._middleware_chain, request_container
                ):
                    yield response.grpc_response
            except Exception as e:
                exc = e
                await self.async_process_exception(e, context)
            finally:
                self.log_response(exc, request_container)

        return handler

    def _get_async_handler(self, action: str) -> Awaitable[Callable]:
        async def handler(request: Message, context) -> Awaitable[Message]:
            proxy_context = GRPCInternalProxyContext(context, request, action)
            service_instance = self.create_service(
                request=request, context=proxy_context, action=action
            )
            request_container = GRPCRequestContainer(
                request, proxy_context, action, service_instance
            )
            try:
                exc = None
                response = await safe_async_response(self._middleware_chain, request_container)
                return response.grpc_response
            except Exception as e:
                exc = e
                await self.async_process_exception(e, context)
            finally:
                self.log_response(exc, request_container)

        return handler

    def _get_handler(self, action: str) -> Callable:
        def handler(request: Message, context) -> Message:
            proxy_context = GRPCInternalProxyContext(context, request, action)
            service_instance = self.create_service(
                request=request, context=proxy_context, action=action
            )
            request_container = GRPCRequestContainer(
                request, proxy_context, action, service_instance
            )
            try:
                exc = None
                response = self._middleware_chain(request_container)
                return response.grpc_response
            except Exception as e:
                exc = e
                self.process_exception(e, context)
            finally:
                self.log_response(exc, request_container)

        return handler

    def _get_stream_handler(self, action: str) -> Callable:
        def handler(request: Message, context) -> AsyncIterable[Message]:
            proxy_context = GRPCInternalProxyContext(context, request, action)
            service_instance = self.create_service(
                request=request, context=proxy_context, action=action
            )
            request_container = GRPCRequestContainer(
                request, proxy_context, action, service_instance
            )
            try:
                exc = None
                for response in self._middleware_chain(request_container):
                    yield response.grpc_response
            except Exception as e:
                exc = e
                self.process_exception(e, context)
            finally:
                self.log_response(exc, request_container)

        return handler

    def get_handler(self, action: str) -> Message:
        service_action = getattr(self.service_class, action)

        if grpc_settings.GRPC_ASYNC:
            if isgeneratorfunction(service_action):
                return self._get_async_stream_handler(action)
            return self._get_async_handler(action)

        if isgeneratorfunction(service_action):
            return self._get_stream_handler(action)
        return self._get_handler(action)

    def create_service(self, **kwargs):
        service = self.service_class(**self.initkwargs, **kwargs)
        servicer_ctx = get_servicer_context()
        servicer_ctx.service = service
        return service

    def __getattr__(self, action):
        if not hasattr(self.service_class, action):
            raise Unimplemented()

        return self.get_handler(action)

    def process_exception(self, exc: Exception, context: grpc.ServicerContext):
        status_code, details = get_exception_status_code_and_details(exc)
        context.abort(status_code, details)

    async def async_process_exception(self, exc: Exception, context: grpc.aio.ServicerContext):
        status_code, details = get_exception_status_code_and_details(exc)
        await context.abort(status_code, details)

    def log_exception(self, exception: Exception, message: str, extra={}):
        """
        Exception logging levels:
        - GRPCException: `exception.logging_level`
        - APIException: WARNING if `status_code` < 500 else ERROR
        - Other: ERROR
        """

        logging_level = "ERROR"
        if isinstance(exception, GRPCException):
            logging_level = exception.logging_level
        elif isinstance(exception, APIException) and exception.status_code < 500:
            logging_level = "WARNING"

        try:
            log_level = getattr(request_logger, logging_level.lower())
        except AttributeError:
            exception_logger.warning(
                f"Unsupported logging level {logging_level}. Defaulting to Warning"
            )
            log_level = request_logger.warning
        log_level(message, exc_info=exception, extra=extra)

    def log_response(
        self, exception: Optional[Exception], request_container: GRPCRequestContainer
    ):
        extra = {
            "request": request_container,
            "status_code": request_container.context.code(),
        }
        path = f"{self.service_class.get_service_name()}/{request_container.action}"

        if not exception:
            if grpc_settings.LOG_OK_RESPONSE or settings.DEBUG:
                message = f"OK : {path}"
                request_logger.info(message, extra=extra)
        else:
            message = f"{type(exception).__name__} : {path}"
            self.log_exception(exception, message, extra=extra)
