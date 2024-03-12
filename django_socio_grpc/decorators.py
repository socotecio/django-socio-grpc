import logging
from typing import List, Type

from django_socio_grpc.protobuf.generation_plugin import (
    BaseGenerationPlugin,
    RequestAsListGenerationPlugin,
    ResponseAsListGenerationPlugin,
)
from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.settings import grpc_settings

from .grpc_actions.actions import GRPCAction

logger = logging.getLogger("django_scoio_grpc.generation")


def _maintain_compat(use_request_list, use_response_list, use_generation_plugins):
    """
    Transform old arguments to the correct plugins
    """
    internal_plugins = [] if use_generation_plugins is None else use_generation_plugins
    warning_message = "You are using {0} argument in grpc_action. This argument is deprecated and has been remplaced by a specific GenerationPlugin. Please update following the documentation: https://django-socio-grpc.readthedocs.io/en/stable/features/proto-generation.html#proto-generation-plugins"
    if use_request_list:
        logger.warning(warning_message.format("use_request_list"))
        internal_plugins.insert(
            0,
            RequestAsListGenerationPlugin(list_field_name="results"),
        )

    if use_response_list:
        logger.warning(warning_message.format("use_response_list"))
        internal_plugins.insert(
            0,
            ResponseAsListGenerationPlugin(list_field_name="results"),
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
    message_name_constructor_class: Type[MessageNameConstructor] = None,
    use_generation_plugins: List["BaseGenerationPlugin"] = None,
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
