import asyncio
import functools
import logging
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING

import django
from asgiref.sync import async_to_sync, sync_to_async
from django.core.cache import cache as default_cache
from django.core.cache import caches
from django.db.models import Model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from google.protobuf.message import Message

from django_socio_grpc.protobuf.generation_plugin import (
    BaseGenerationPlugin,
    ListGenerationPlugin,
)
from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.request_transformer import (
    GRPCInternalProxyResponse,
)
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.signals import grpc_action_register
from django_socio_grpc.utils.utils import isgeneratorfunction

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
    override_default_generation_plugins: bool = False,
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

    if not override_default_generation_plugins:
        use_generation_plugins = (
            grpc_settings.DEFAULT_GENERATION_PLUGINS + use_generation_plugins
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
            use_generation_plugins=use_generation_plugins,
        )

    return wrapper


def http_to_grpc(
    decorator_to_wrap: Callable,
    request_setter: dict = None,
    response_setter: dict = None,
    support_async: bool = False,
) -> Callable:
    """
    Allow to use Django decorators on grpc endpoint.
    As the working behavior will depend on the grpc support and/or DSG support of the feature it may not work as expected.
    If it's not working as expected, first look at the documentation if the decorators is not listed as one of the unsupported decorator.
    If not, please open an issue and we will look if possible to support it.

    :param decorator_to_wrap: The decorator to wrap. It can be a method or a function decorator.
    :param request_setter: A dict of attribute to set on the request object before calling the HTTP decorator.
    :param response_setter: A dict of attribute to set on the response object before returning it to the HTTP decorator.
    :param support_async: If the decorator to wrap is async or not. If not, it will be wrapped in a sync function. Refer to https://docs.djangoproject.com/en/5.0/topics/async/#decorators
    """

    def decorator(func: GRPCAction | Callable, *args, **kwargs) -> Callable:
        # INFO - AM - 21/08/2024 - Depending of the decorator order we may have a GRPCAction or a function so we need to get the actual function
        grpc_action_method = func.function if isinstance(func, GRPCAction) else func
        if isgeneratorfunction(grpc_action_method):
            raise ValueError(
                "You are using http_to_grpc decorator or an other decorator that use http_to_grpc on a gRPC stream endpoint. This is not supported and will not work as expected. If you meet a specific use case that you think is still relevant on a stream endpoint, please open an issue."
            )

        if asyncio.iscoroutinefunction(grpc_action_method):

            async def _simulate_function(
                service_instance: "Service", context: "GRPCInternalProxyContext"
            ) -> "GRPCInternalProxyResponse":
                """
                This async method is a wrapper to pass to the Django/HTTP1 decorator a method that only
                take an object that can proxy a django.http.request as param
                and return an object that can proxy a django.http.response.
                """
                # INFO - AM - 01/08/2024 - As a django decorator take only one request argument and grpc 2 we are passing an instance of GRPCInternalProxyContext so we can get the context back from the request and make the actual call
                request = context.grpc_request
                # INFO - AM - 01/08/2024 - Call the actual grpc endpoint
                endpoint_result = await func(service_instance, request, context)
                # INFO - AM - 01/08/2024 - Transform the grpc Response to a proxyfied one to let the http decorator work
                response_proxy = GRPCInternalProxyResponse(endpoint_result, context)
                # INFO - AM - 01/08/2024 - This allow developer to customize some response behavior
                if response_setter:
                    for key, value in response_setter.items():
                        setattr(response_proxy, key, value)
                return response_proxy

            @functools.wraps(grpc_action_method)
            async def _view_wrapper(
                service_instance: "Service",
                request: Message,
                context: "GRPCInternalProxyContext",
            ) -> Message:
                # INFO - AM - 01/08/2024 - This allow developer to customize some request behavior. For exemple all grpc request are POST but the cache behavior need GET request so we transform that here.
                if request_setter:
                    for key, value in request_setter.items():
                        setattr(context, key, value)
                # INFO - AM - 30/07/2024 - Before django 5, all django decorator didn't support async function.
                # Since django 5 some decorator accept it but not all.
                # We need to wrap them in a sync function.
                if django.VERSION < (5, 0, 0) or not support_async:
                    response_proxy = await sync_to_async(
                        decorator_to_wrap(async_to_sync(_simulate_function))
                    )(service_instance, context)
                else:
                    # INFO - AM - 01/08/2024 - Give the HTTP decorator a wrapper around the endpoint that match what a django endpoint should expect as param and return type
                    response_proxy = await decorator_to_wrap(_simulate_function)(
                        service_instance, context
                    )
                # INFO - AM - 30/07/2024 - Remember to put the grpc context in case the response come from cache
                if not response_proxy.grpc_context:
                    response_proxy.set_current_context(context.grpc_context)
                return response_proxy.grpc_response

        else:

            def _simulate_function(
                service_instance: "Service", context: "GRPCInternalProxyContext"
            ) -> "GRPCInternalProxyResponse":
                """
                This sync method is a wrapper to pass to the Django/HTTP1 decorator a method that only
                take an object that can proxy a django.http.request as param
                and return an object that can proxy a django.http.response.
                """
                # INFO - AM - 01/08/2024 - As a django decorator take only one request argument and grpc 2 we are passing an instance of GRPCInternalProxyContext so we can get the context back from the request and make the actual call
                request = context.grpc_request
                # INFO - AM - 01/08/2024 - Call the actual grpc endpoint
                endpoint_result = func(service_instance, request, context)
                # INFO - AM - 01/08/2024 - Transform the grpc Response to a proxyfied one to let the http decorator work
                response_proxy = GRPCInternalProxyResponse(endpoint_result, context)
                # INFO - AM - 01/08/2024 - This allow developer to customize some response behavior
                if response_setter:
                    for key, value in response_setter.items():
                        setattr(response_proxy, key, value)
                return response_proxy

            @functools.wraps(grpc_action_method)
            def _view_wrapper(
                service_instance: "Service",
                request: Message,
                context: "GRPCInternalProxyContext",
            ) -> Message:
                # INFO - AM - 01/08/2024 - This allow developer to customize some request behavior. For exemple all grpc request are POST but the cache behavior need GET request so we transform that here.
                if request_setter:
                    for key, value in request_setter.items():
                        setattr(context, key, value)
                # INFO - AM - 01/08/2024 - Give the HTTP decorator a wrapper around the endpoint that match what a django endpoint should expect as param and return type
                response_proxy = decorator_to_wrap(_simulate_function)(
                    service_instance, request, context
                )
                # INFO - AM - 30/07/2024 - Remember to put the grpc context in case the response come from cache
                if not response_proxy.grpc_context:
                    response_proxy.set_current_context(context.grpc_context)
                return response_proxy.grpc_response

        # INFO - AM - 21/08/2024 - If the http_to_grpc is called on top of the grpc decorator we need to return a  copy of GRPCAction to let DSG working normally as it expect a GRPCAction
        return (
            func.clone(function=_view_wrapper)
            if isinstance(func, GRPCAction)
            else _view_wrapper
        )

    return decorator


def vary_on_metadata(*headers) -> Callable:
    """
    Same as https://docs.djangoproject.com/fr/5.0/topics/http/decorators/#django.views.decorators.vary.vary_on_headers
    but need to wrap the response in a GRPCInternalProxyResponse.
    A view decorator that adds the specified metadatas to the Vary metadata of the
    response. Usage:

        @vary_on_metadata('Cookie', 'Accept-language')
        def index(request):
            ...

    Note that the metadata names are not case-sensitive.
    """
    return http_to_grpc(vary_on_headers(*headers), support_async=True)


@functools.wraps(cache_page)
def cache_endpoint(*args, **kwargs):
    """
    A decorator for caching gRPC endpoints using Django's cache_page functionality.
    This decorator adapts Django's cache_page for use with gRPC endpoints. It performs the following steps:
    1. Converts cache_page to a method decorator, see:
        https://docs.djangoproject.com/en/5.0/topics/class-based-views/intro/#decorating-the-class
    2. Transforms the method decorator to be gRPC-compatible.
    3. Forces the request method to be GET.

    Do not use this decorator on Create, Update, or Delete endpoints, as it will cache the response and return the same result to all users, potentially leading to data inconsistencies.
    """
    return http_to_grpc(
        method_decorator(cache_page(*args, **kwargs)),
        request_setter={"method": "GET"},
        support_async=False,
    )


def cache_endpoint_with_deleter(
    timeout: int,
    key_prefix: str = "",
    senders: Iterable[Model] | None = None,
    cache: str = None,
    invalidator_signals: Iterable[Callable] = None,
):
    """
    This decorator does all the same as cache_endpoint but with the addition of a cache deleter.
    The cache deleter will delete the cache when a signal is triggered.
    This is useful when you want to delete the cache when a model is updated or deleted.
    Be warned that this can add little overhead at server start as it will listen to signals.

    :param timeout: The timeout of the cache
    :param key_prefix: The key prefix of the cache
    :param cache: The cache alias to use. If None, it will use the default cache. It is named cache and not cache_alias to keep compatibility with Django cache_page decorator
    :param senders: The senders to listen to the signal
    :param invalidator_signals: The django signals to listen to delete the cache
    """
    if cache is None and not hasattr(default_cache, "delete_pattern"):
        cache_deleter_logger = logging.getLogger(__name__)
        cache_deleter_logger.warning(
            "You are using cache_endpoint_with_deleter with the default cache engine that is not a redis cache engine."
            "Only Redis cache engine support cache pattern deletion."
            "You still continue to use it but it will delete all the endpoint cache when signal will trigger."
            "Please use a specific cache config per service or use redis cache engine to avoid this behavior."
            "If this is the expected behavior, you can disable this warning by muting django_socio_grpc.cache_deleter logger in your logging settings."
        )

    if invalidator_signals is None:
        invalidator_signals = (post_save, post_delete)

    def decorator(func: Callable, *args, **kwargs):
        # INFO - AM - 21/08/2024 - We connect to the grpc action set signal to have access to the owner of the function and the name of the function as we used a decorated with parameter we don't have access to the service class to get default senders and model to use
        @receiver(grpc_action_register, weak=False)
        def register_invalidate_cache_signal(sender, owner, name, **kwargs):
            # INFO - AM - 21/08/2024 - The decorator can be put before or after the grpc_action decorator so we need to check if the function is a grpc action or not
            func_qual_name = (
                func.function.__qualname__
                if isinstance(func, GRPCAction)
                else func.__qualname__
            )

            # INFO - AM - 05/09/2024 - the func_qual_name is the name of the service_name.function_name of the method we decorate. But in an inheritance context the service_name is the parent name not the owner name.
            # So to be able to known if the function currently being registered is the one that is decorated with the cache deleter we need to check if the function is in the owner mro
            func_registered_is_func_decorated = any(
                [f"{mro_class.__name__}.{name}" == func_qual_name for mro_class in owner.mro()]
            )

            # INFO - AM - 05/09/2024 - We verify that the function registered is the one we wen to use the cache with deleter and it's exist the owner registry.
            if not func_registered_is_func_decorated:
                return

            # INFO - AM - 22/08/2024 - Set the default value for key_prefix, senders, invalidator_signals is not set
            # INFO - AM - 05/09/2024 - We need a _key_prefix to avoid having only one key for all inherited model
            _key_prefix = key_prefix
            if not _key_prefix:
                _key_prefix = f"{owner.__name__}-{name}"

            # INFO - AM - 05/09/2024 - It's safe to assign directly senders to locale_senders as we assign a value only if None and None is passed by value and not reference so no risk of assigning the same senders to all inherites class
            locale_senders = senders
            if locale_senders is None and hasattr(owner, "queryset"):
                locale_senders = owner.queryset.model

            # INFO - AM - 22/08/2024 - If no sender are specified and the service do not have a queryset we can't use the cache deleter. There is a warning displayed to the user
            if locale_senders is not None:
                if not isinstance(locale_senders, Iterable):
                    locale_senders = [locale_senders]

                # INFO - AM - 21/08/2024 - Once we have all the value we need we can connect the Model signals to the cache deleter
                @receiver(invalidator_signals, weak=False)
                def invalidate_cache(*args, **kwargs):
                    if kwargs.get("sender") in locale_senders:
                        # INFO - AM - 01/08/2024 - To follow django cache_page signature cache is a string and not a cache instance. In this behavior we need the cache instance so we get it
                        cache_instance = caches[cache] if cache else default_cache
                        # INFO - AM - 01/08/2024 - For now this is only for Redis cache but this is important to support as it simplify the cache architecture to create if used
                        # Has cache_instance is a django.utils.connection.ConnectionProxy, hasattr will not work so we need to use try except
                        try:
                            cache_instance.delete_pattern(
                                f"views.decorators.cache.cache_header.{_key_prefix}.*"
                            )
                            cache_instance.delete_pattern(
                                f"views.decorators.cache.cache_page.{_key_prefix}.*"
                            )
                        except AttributeError:
                            cache_instance.clear()
            else:
                logger.warning(
                    "You are using cache_endpoint_with_deleter without senders. If you don't need the auto deleter just use cache_endpoint decorator."
                )

            # INFO - AM - 22/08/2024 - http_to_grpc is a decorator so we pass the function to wrap in argument of it's return value
            sender.function = http_to_grpc(
                method_decorator(
                    cache_page(timeout, key_prefix=_key_prefix, cache=cache),
                    name="cache_page",
                ),
                request_setter={"method": "GET"},
                support_async=False,
            )(sender.function)

        # INFO - AM - 05/09/2024 - We return the function directly because the patching of the function is done in the signal receiver
        return func

    return decorator
