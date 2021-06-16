from collections import OrderedDict
from importlib import import_module


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RegistrySingleton(metaclass=SingletonMeta):

    _instances = {}

    def __init__(self):
        self.registered_controlleur = OrderedDict()
        self.registered_message = OrderedDict()

    def register_service(self, *args, **kwargs):
        print("register_service", args, kwargs)


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
            # service_registry = RegistrySingleton()
            # service_registry.register_service(ModelService)
            return

        pb2_grpc = import_module(
            f"{self.app_name}.{self.grpc_folder}.{self.app_name}_pb2_grpc"
        )
        add_server = getattr(pb2_grpc, f"add_{model_name}ControllerServicer_to_server")

        add_server(ModelService.as_servicer(), self.server)
