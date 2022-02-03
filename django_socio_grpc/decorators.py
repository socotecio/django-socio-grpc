import logging

from django_socio_grpc.utils.registry_singleton import RegistrySingleton

logger = logging.getLogger("django_socio_grpc")


class _grpc_action:
    def __init__(
        self,
        function,
        request=None,
        response=None,
        request_name=None,
        response_name=None,
        request_stream=False,
        response_stream=False,
        use_request_list=False,
        use_response_list=False,
        *args,
        **kwargs,
    ):
        self.request = request
        self.response = response
        self.request_name = request_name
        self.response_name = response_name
        self.request_stream = request_stream
        self.response_stream = response_stream
        self.use_request_list = use_request_list
        self.use_response_list = use_response_list
        self.function = function

    def __set_name__(self, owner, name):
        try:
            service_registry = RegistrySingleton()
            service_registry.register_custom_action(
                service_class=owner,
                function_name=name,
                request=self.request,
                response=self.response,
                request_name=self.request_name,
                response_name=self.response_name,
                request_stream=self.request_stream,
                response_stream=self.response_stream,
                use_request_list=self.use_request_list,
                use_response_list=self.use_response_list,
            )
        except Exception as e:
            logger.exception(f"Error while registering grpc_action {owner} - {name}: {e}")
        setattr(owner, name, self.function)

    def __get__(self, obj, type=None):
        return self.__class__(self.function.__get__(obj, type))

    def __call__(self, *args, **kwargs):
        self.function(*args, **kwargs)


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
        return _grpc_action(
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
