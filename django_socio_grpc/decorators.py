from .grpc_actions.actions import GRPCAction


def grpc_action(
    request=None,
    response=None,
    request_name=None,
    response_name=None,
    request_stream=False,
    response_stream=False,
    use_request_list=False,
    use_response_list=False,
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
    """

    def wrapper(function):
        return GRPCAction(
            function,
            request,
            response,
            request_name,
            response_name,
            request_stream,
            response_stream,
            use_request_list,
            use_response_list,
        )

    return wrapper
