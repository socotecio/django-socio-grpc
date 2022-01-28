import logging

from django_socio_grpc.utils.registry_singleton import RegistrySingleton

logger = logging.getLogger("django_socio_grpc")


class _grpc_action:
    def __init__(
        self,
        function,
        request=None,
        response=None,
        request_stream=False,
        response_stream=False,
        use_request_list=False,
        use_response_list=False,
        *args,
        **kwargs,
    ):
        self.request = request
        self.response = response
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
    request_stream=False,
    response_stream=False,
    use_request_list=False,
    use_response_list=False,
):
    def wrapper(function):
        return _grpc_action(
            function,
            request,
            response,
            request_stream,
            response_stream,
            use_request_list,
            use_response_list,
        )

    return wrapper
