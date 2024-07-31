import asyncio
import functools
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, List, Type

from asgiref.sync import async_to_sync, sync_to_async
from grpc.aio._typing import RequestType

import django
from django.core.cache import cache as default_cache
from django.core.cache import caches
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_socio_grpc.protobuf.generation_plugin import (
    BaseGenerationPlugin,
    ListGenerationPlugin,
)
from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.request_transformer import (
    GRPCInternalProxyResponse,
)
from django_socio_grpc.settings import grpc_settings

from .grpc_actions.actions import GRPCAction

if TYPE_CHECKING:
    from django_socio_grpc.request_transformer.grpc_internal_proxy import (
        GRPCInternalProxyContext,
    )
    from django_socio_grpc.services import Service

logger = logging.getLogger("django_socio_grpc.generation")


def _maintain_compat(use_request_list, use_response_list, use_generation_plugins):
    """
    Transform old arguments to the correct plugins
    """
    internal_plugins = [] if use_generation_plugins is None else use_generation_plugins
    warning_message = "You are using {0} argument in grpc_action. This argument is deprecated and has been remplaced by a specific GenerationPlugin. Please update following the documentation: https://django-socio-grpc.readthedocs.io/en/stable/features/proto-generation.html#proto-generation-plugins"
    if use_request_list or use_response_list:
        log_text = "use_request_list" if use_request_list else "use_response_list"
        if use_request_list and use_response_list:
            log_text = "use_request_list and use_response_list"
        logger.warning(warning_message.format(log_text))
        internal_plugins.insert(
            0,
            ListGenerationPlugin(request=use_request_list, response=use_response_list),
        )

    return internal_plugins


def grpc_action(
    request=None,
    response=None,
    request_name=None,
    response_name=None,
    request_stream=False,
    response_stream=False,
    use_request_list=False,
    use_response_list=False,
    message_name_constructor_class: type[MessageNameConstructor] = None,
    use_generation_plugins: list["BaseGenerationPlugin"] = None,
):
    """
    Easily register a grpc action into the registry to generate it into the proto file.

    :param request: Format of the request. Can be a list of dict, a proto serilizer class or a string. See doc for more information.
    :param response: Format of the response. Can be a list of dict, a proto serilizer class or a string. See doc for more information.
    :param request_name: Name of the request. By default it's generated according to service name and function name.
    :param response_name: Name of the response. By default it's generated according to service name and function name.
    :param request_stream: If true the request message is marqued as stream. Default to false
    :param response_stream: If true the response message is marqued as stream. Default to false
    :param use_request_list: If true the response message is encapsuled in a list message. Default to false
    :param use_response_list: If true the response message is encapsuled in a list message. Default to false
    :param message_name_constructor_class: The class used to generate the name of the model. Inherit from MessageNameConstructor and chnage logic to have highly customizable name generation.
    :param use_generation_plugins: List of generation plugin to use to customize the message.
    """

    # INFO - AM - 03/12/2024 - transform old arguments to the correct plugins.
    use_generation_plugins = _maintain_compat(
        use_request_list, use_response_list, use_generation_plugins
    )

    def wrapper(function):
        return GRPCAction(
            function,
            request,
            response,
            request_name,
            response_name,
            request_stream,
            response_stream,
            message_name_constructor_class=message_name_constructor_class
            or grpc_settings.DEFAULT_MESSAGE_NAME_CONSTRUCTOR,
            use_generation_plugins=use_generation_plugins
            or grpc_settings.DEFAULT_GENERATION_PLUGINS.copy(),
        )

    return wrapper


def http_to_grpc(decorator_to_wrap, request_setter=None, response_setter=None):
    """
    Allow to use Django decorator on grpc endpoint.
    As the working behavior will depend on the grpc support and/or DSG support of the feature it may not work as expected.
    If it's not working as expected, first look at the documentation if the decorators is not listed as one of the unsupported decorator.
    If not, please open an issue and we will look if possible to support it.
    """

    def decorator(func, *args, **kwargs):
        if asyncio.iscoroutinefunction(func):

            async def _simulate_function(service_instance, context):
                request = context.grpc_request
                endpoint_result = await func(service_instance, request, context)
                response_proxy = GRPCInternalProxyResponse(endpoint_result, context)
                if response_setter:
                    for key, value in response_setter.items():
                        setattr(response_proxy, key, value)
                return response_proxy

            @functools.wraps(func)
            async def _view_wrapper(
                service_instance: "Service",
                request: RequestType,
                context: "GRPCInternalProxyContext",
            ):
                if request_setter:
                    for key, value in request_setter.items():
                        setattr(context, key, value)
                # INFO - AM - 30/07/2024 - Before django 5, django decorator didn't support async function. We need to wrap it in a sync function.
                if int(django.__version__[0]) < 5:
                    response_proxy = await sync_to_async(
                        decorator_to_wrap(async_to_sync(_simulate_function))
                    )(service_instance, context)
                else:
                    response_proxy = await decorator_to_wrap(_simulate_function)(
                        service_instance, context
                    )
                # INFO - AM - 30/07/2024 - Remember to put the grpc context in case the response come from cache
                if not response_proxy.grpc_context:
                    response_proxy.set_current_context(context.grpc_context)
                return response_proxy.grpc_response

        else:

            def _simulate_function(service_instance, request, context):
                endpoint_result = func(service_instance, request, context)
                response_proxy = GRPCInternalProxyResponse(endpoint_result, context)
                if response_setter:
                    for key, value in response_setter.items():
                        setattr(response_proxy, key, value)
                return response_proxy

            @functools.wraps(func)
            def _view_wrapper(
                service_instance: "Service",
                request: RequestType,
                context: "GRPCInternalProxyContext",
            ):
                response_proxy = decorator_to_wrap(_simulate_function)(
                    service_instance, request, context
                )
                return response_proxy.grpc_response

        return _view_wrapper

    return decorator


def vary_on_metadata(*headers):
    """
    Same as https://github.com/django/django/blob/0e94f292cda632153f2b3d9a9037eb0141ae9c2e/django/views/decorators/vary.py#L8
    but need to wrap the response in a GRPCInternalProxyResponse.
    A view decorator that adds the specified metadatas to the Vary metadata of the
    response. Usage:

        @vary_on_metadata('Cookie', 'Accept-language')
        def index(request):
            ...

    Note that the metadata names are not case-sensitive.
    """
    return http_to_grpc(vary_on_headers(*headers))


@functools.wraps(cache_page)
def cache_endpoint(*args, **kwargs):
    return http_to_grpc(
        method_decorator(cache_page(*args, **kwargs), name="List"),
        request_setter={"method": "GET"},
    )


def cache_endpoint_with_cache_deleter(
    timeout, key_prefix, senders, cache=None, invalidator_signals=None
):
    """
    This decorator allow to cache the endpoint with a cache deleter.
    The cache deleter will delete the cache when a signal is triggered.
    This is useful when you want to delete the cache when a model is updated or deleted.
    :param timeout: The timeout of the cache
    :param key_prefix: The key prefix of the cache
    :param cache: The cache alias to use. If None, it will use the default cache. It is named cache and not cache_alias to keep compatibility with Django cache_page decorator
    :param senders: The senders to listen to the signal
    :param invalidator_signals: The signals to listen to delete the cache
    """
    if not key_prefix:
        logger.warning(
            "You are using cache_endpoint_with_cache_deleter without key_prefix. It's highly recommended to use it named as your service to avoid deleting all the cache without prefix when data is updated in back."
        )
    if (
        cache is None
        and not hasattr(default_cache, "delete_pattern")
        and not grpc_settings.ENABLE_CACHE_WARNING_ON_DELETER
    ):
        logger.warning(
            "You are using cache_endpoint_with_cache_deleter with the default cache engine that is not a redis cache engine."
            "Only Redis cache engine support cache pattern deletion."
            "You still continue to use it but it will delete all the endpoint cache when signal will trigger."
            "Please use a specific cache config per service or use redis cache engine to avoid this behavior."
            "If this is the expected behavior, you can disable this warning by setting ENABLE_CACHE_WARNING_ON_DELETER to False in your grpc settings."
        )
    if invalidator_signals is None:
        invalidator_signals = (post_save, post_delete)
    if senders is not None:
        if not isinstance(senders, Iterable):
            senders = [senders]

        @receiver(invalidator_signals, weak=False)
        def invalidate_cache(*args, **kwargs):
            if kwargs.get("sender") in senders:
                cache_instance = caches[cache] if cache else default_cache
                if hasattr(cache, "delete_pattern"):
                    cache_instance.delete_pattern(
                        f"views.decorators.cache.cache_header.{key_prefix}.*"
                    )
                    cache_instance.delete_pattern(
                        f"views.decorators.cache.cache_page.{key_prefix}.*"
                    )
                else:
                    cache_instance.clear()
    else:
        logger.warning(
            "You are using cache_endpoint_with_cache_deleter without senders. If you don't need the auto deleter just use cache_endpoint decorator."
        )

    return http_to_grpc(
        method_decorator(cache_page(timeout, key_prefix=key_prefix, cache=cache), name="List"),
        request_setter={"method": "GET"},
    )
