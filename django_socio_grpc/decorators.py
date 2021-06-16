from django_socio_grpc.utils.servicer_register import RegistrySingleton


class _grpc_action:
    def __init__(self, function, params="", *args, **kwargs):
        self.params = params
        self.function = function

    def __set_name__(self, owner, name):
        print(f"Je décore la fonction {self.function} de la class {owner}")
        print(f"Je suis dans le décorateur voici mon params: {self.params}")
        print(f"Ici j'ai un seralizer par ex: {owner.serializer_class}")
        service_registry = RegistrySingleton()
        service_registry.register_service(owner, self.function, name, self.params)
        setattr(owner, name, self.function)

    def __get__(self, obj, type=None):
        return self.__class__(self.function.__get__(obj, type))

    def __call__(self, *args, **kwargs):
        self.function(*args, **kwargs)


def grpc_action(function=None, params=""):
    def wrapper(function):
        return _grpc_action(function, params)

    return wrapper
