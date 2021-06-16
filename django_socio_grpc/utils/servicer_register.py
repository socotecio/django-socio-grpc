from collections import OrderedDict
from importlib import import_module

from django_socio_grpc import mixins
from django_socio_grpc.mixins import get_default_grpc_messages, get_default_grpc_methods


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RegistrySingleton(metaclass=SingletonMeta):

    _instances = {}
    know_methods = [
        "Create",
        "List",
        "Stream",
        "Retrieve",
        "Update",
        "PartialUpdate",
        "Destroy",
    ]

    def __init__(self):
        self.registered_controlleur = OrderedDict()
        self.registered_message = OrderedDict()

    def register_service(self, Service):
        print("register_service", Service)

        service_instance = Service()

        ModelService = service_instance.get_queryset().model

        print("ModelSefice", ModelService)

        model_service_name = ModelService.__name__
        controlleur_name = f"{model_service_name}Controlleur"

        self.registered_controlleur[controlleur_name] = {}

        default_grpc_methods = mixins.get_default_grpc_methods(model_service_name)
        default_grpc_messages = mixins.get_default_grpc_messages(model_service_name)

        for method in self.know_methods:
            if not getattr(Service, method, None):
                continue

            # If we already have registered this method for this controlleur (with a decorator) we do not use the default behavior
            if method in self.registered_controlleur[controlleur_name]:
                continue

            self.registered_controlleur[controlleur_name][method] = default_grpc_methods[
                method
            ]

            self.register_default_message_from_method(
                model_service_name, method, service_instance
            )

        print(self.registered_controlleur)
        print(self.registered_message)

    def register_custom_action(self, *args, **kwargs):
        print("register_custom_action", args, kwargs)

    def register_default_message_from_method(
        self, model_service_name, method, service_instance
    ):
        if method == "List":
            self.registered_message = {
                **self.registered_message,
                **mixins.ListModelMixin.get_default_message(
                    model_name=model_service_name, pagination=service_instance.pagination_class
                ),
            }
            # TODO add the serializer response if get_message_from_serializer != retrieve
            # TODO add serializer for retrieve if no Retrieve but list yes

    def get_message_from_serializer(self, service_instance, method):
        service_instance.action = method
        serializer_class = service_instance.get_serializer_class()

        print(serializer_class)


class AppHandlerRegistry:
    def __init__(self, app_name, server, service_folder="services", grpc_folder="grpc"):
        self.app_name = app_name
        self.server = server
        self.service_folder = service_folder
        self.grpc_folder = grpc_folder

    def register(self, model_name):
        if self.service_folder:
            model_service_path = (
                f"{self.app_name}.{self.service_folder}.{model_name.lower()}_service"
            )
        else:
            model_service_path = f"{self.app_name}.services"
        ModelService = getattr(
            import_module(model_service_path),
            f"{model_name}Service",
        )

        if self.server is None:
            service_registry = RegistrySingleton()
            service_registry.register_service(ModelService)
            return

        pb2_grpc = import_module(
            f"{self.app_name}.{self.grpc_folder}.{self.app_name}_pb2_grpc"
        )
        add_server = getattr(pb2_grpc, f"add_{model_name}ControllerServicer_to_server")

        add_server(ModelService.as_servicer(), self.server)
