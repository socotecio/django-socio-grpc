import asyncio
import functools
import logging
from typing import TYPE_CHECKING, List, Optional, Type
from django.views.decorators.vary import vary_on_headers

from asgiref.sync import async_to_sync, sync_to_async
from grpc.aio._typing import RequestType, ResponseType

import django
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_socio_grpc.cache import get_response_from_cache, put_response_in_cache
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


def cache_endpoint(
    cache_timeout: Optional[int] = None,
    key_prefix: Optional[str] = None,
    cache: Optional[str] = None,
):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(
                service_instance: "Service",
                request: RequestType,
                context: "GRPCInternalProxyContext",
            ) -> ResponseType:
                response_cached = get_response_from_cache(
                    request=context,
                    key_prefix=key_prefix,
                    method=context.method,
                    cache_alias=cache,
                )
                if response_cached:
                    return response_cached.grpc_response

                # func(service_instance, request, context)
                endpoint_result = await func(service_instance, request, context)

                response_proxy = GRPCInternalProxyResponse(endpoint_result, context)

                put_response_in_cache(
                    context,
                    response_proxy,
                    cache_timeout=cache_timeout,
                    key_prefix=key_prefix,
                    cache_alias=cache,
                )

                return endpoint_result

            return async_wrapper
        else:

            @functools.wraps(func)
            def wrapper(
                service_instance: "Service",
                request: RequestType,
                context: "GRPCInternalProxyContext",
            ) -> ResponseType:
                response_cached = get_response_from_cache(
                    request=context,
                    key_prefix=key_prefix,
                    method=context.method,
                    cache_alias=cache,
                )
                if response_cached:
                    return response_cached.grpc_response

                endpoint_result = func(service_instance, request, context)

                response_proxy = GRPCInternalProxyResponse(endpoint_result, context)

                put_response_in_cache(
                    context,
                    response_proxy,
                    cache_timeout=cache_timeout,
                    key_prefix=key_prefix,
                    cache_alias=cache,
                )

                return endpoint_result

            return wrapper

    return decorator


def http_to_grpc(decorator_to_wrap):
    """
    Allow to use Django decorator on grpc endpoint.
    As the working behavior will depend on the grpc support and/or DSG support of the feature it may not work as expected.
    If it's not working as expected, first look at the documentation if the decorators is not listed as one of the unsupported decorator.
    If not, please open an issue and we will look if possible to support it.
    """

    def decorator(func, *args, **kwargs):
        if asyncio.iscoroutinefunction(func):

            async def _simulate_function(service_instance, context):
                print("icicicicic ", context)
                request = context.grpc_request
                endpoint_result = await func(service_instance, request, context)
                response_proxy = GRPCInternalProxyResponse(endpoint_result, context)
                return response_proxy

            @functools.wraps(func)
            async def _view_wrapper(
                service_instance: "Service",
                request: RequestType,
                context: "GRPCInternalProxyContext",
            ):
                # INFO - AM - 03/12/2024 - Before django 5, django decorator didn't support async function. We need to wrap it in a sync function.
                if int(django.__version__[0]) < 5:
                    response_proxy = await sync_to_async(
                        decorator_to_wrap(async_to_sync(_simulate_function))
                    )(service_instance, context)
                else:
                    response_proxy = await decorator_to_wrap(_simulate_function)(
                        service_instance, context
                    )
                return response_proxy.grpc_response

        else:

            def _simulate_function(service_instance, request, context):
                endpoint_result = func(service_instance, request, context)
                response_proxy = GRPCInternalProxyResponse(endpoint_result, context)
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


vary_on_metadata = http_to_grpc(vary_on_headers)
vary_on_metadata.__doc__ = """Same as https://github.com/django/django/blob/0e94f292cda632153f2b3d9a9037eb0141ae9c2e/django/views/decorators/vary.py#L8
but need to wrap the response in a GRPCInternalProxyResponse.
A view decorator that adds the specified metadatas to the Vary metadata of the
response. Usage:

    @vary_on_metadata('Cookie', 'Accept-language')
    def index(request):
        ...

Note that the metadata names are not case-sensitive.
"""


def cache_dsg_page(*args, **kwargs):
    return http_to_grpc(method_decorator(cache_page(*args, **kwargs), name="List"))
