from django_socio_grpc.utils.servicer_register import RegistrySingleton


class _grpc_action:
    def __init__(self, function, request=None, response=None, request_stream=False, response_stream=False, *args, **kwargs):
        self.request = request
        self.response = response
        self.request_stream = request_stream
        self.response_stream = response_stream
        self.function = function

    def __set_name__(self, owner, name):
        print(f"decorator set name {owner}, {name}")
        # print(f"Je décore la fonction {self.function} de la class {owner}")
        # print(f"Je suis dans le décorateur voici mon params: {self.params}")
        # print(f"Ici j'ai un seralizer par ex: {owner.serializer_class}")
        service_registry = RegistrySingleton()
        # service_registry.register_custom_action(owner, self.function, name, self.params)
        service_registry.register_custom_action(owner, name, self.request, self.response, self.request_stream, self.response_stream)
        setattr(owner, name, self.function)

    def __get__(self, obj, type=None):
        return self.__class__(self.function.__get__(obj, type))

    def __call__(self, *args, **kwargs):
        self.function(*args, **kwargs)


def grpc_action(request=None, response=None, request_stream=False, response_stream=False):
    def wrapper(function):
        return _grpc_action(function, request, response, request_stream, response_stream)

    return wrapper
