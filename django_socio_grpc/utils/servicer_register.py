from collections import OrderedDict
from importlib import import_module

from rest_framework.fields import IntegerField

from django_socio_grpc import mixins
from django_socio_grpc.mixins import get_default_grpc_messages, get_default_grpc_methods
from django_socio_grpc.settings import grpc_settings


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
        self.registered_app = OrderedDict()

    def register_service(self, Service):
        print("register_service", Service)

        service_instance = Service()

        Model = service_instance.get_queryset().model
        app_name = Model._meta.app_label

        model_name = Model.__name__

        if app_name not in self.registered_app:
            self.registered_app[app_name] = {
                "registered_controllers": OrderedDict(),
                "registered_messages": OrderedDict(),
            }

        controller_name = f"{model_name}Controller"

        print("REGISTER:")
        print("App name: ", app_name)
        print("Model", model_name)
        print("Controller", controller_name)

        self.set_controller_and_messages(
            app_name, model_name, controller_name, service_instance
        )

    def register_custom_action(self, *args, **kwargs):
        print("register_custom_action", args, kwargs)

    def set_controller_and_messages(
        self, app_name, model_name, controller_name, service_instance
    ):
        default_grpc_methods = mixins.get_default_grpc_methods(model_name)
        default_grpc_messages = mixins.get_default_grpc_messages(model_name)

        print(self.registered_app[app_name])

        if controller_name not in self.registered_app[app_name]["registered_controllers"]:
            self.registered_app[app_name]["registered_controllers"][controller_name] = {}

        controller_object = self.registered_app[app_name]["registered_controllers"][
            controller_name
        ]

        for method in self.know_methods:
            if not getattr(service_instance, method, None):
                continue

            # If we already have registered this method for this controlleur (with a decorator) we do not use the default behavior
            if method in controller_object:
                continue

            controller_object[method] = default_grpc_methods[method]

            self.register_default_message_from_method(
                app_name, model_name, method, service_instance
            )

        print(self.registered_app[app_name]["registered_controllers"])
        print(self.registered_app[app_name]["registered_messages"])

    def register_default_message_from_method(
        self, app_name, model_name, method, service_instance
    ):
        registered_messages = self.registered_app[app_name]["registered_messages"]
        if method == "List":

            serializer_instance = self.get_message_from_serializer(service_instance, method)
            self.register_list_serializer_as_message_response(
                app_name, service_instance, serializer_instance
            )

            self.register_serializer_as_message_if_not_exist(app_name, serializer_instance)

            # If we have only list without create or update or retrieve we need to add the model message
            if model_name not in self.registered_app[app_name]["registered_messages"]:
                pass

    def get_message_from_serializer(self, service_instance, method):
        service_instance.action = method.lower()
        SerializerClass = service_instance.get_serializer_class()

        serializer_instance = SerializerClass()

        # fields = serializer_instance.get_fields()

        return serializer_instance

    def register_serializer_as_message_if_not_exist(self, app_name, serializer_instance):
        serializer_name = serializer_instance.__class__.__name__.replace("Serializer", "")
        if serializer_name not in self.registered_app[app_name]["registered_messages"]:
            self.registered_app[app_name]["registered_messages"][
                serializer_name
            ] = serializer_instance.get_fields()

            print(
                "icicic ",
                self.registered_app[app_name]["registered_messages"][serializer_name],
            )

    def register_list_serializer_as_message_response(
        self, app_name, service_instance, serializer_instance, response_field_name="results"
    ):
        serializer_name = serializer_instance.__class__.__name__.replace("Serializer", "")
        pagination = service_instance.pagination_class
        if pagination is None:
            pagination = grpc_settings.DEFAULT_PAGINATION_CLASS is not None

        response_fields = [(f"{serializer_name}", serializer_instance)]
        if pagination:
            response_fields += [("count", IntegerField())]

        self.registered_app[app_name]["registered_messages"][
            f"{serializer_name}ListRequest"
        ] = []
        self.registered_app[app_name]["registered_messages"][
            f"{serializer_name}ListResponse"
        ] = response_fields

        self.register_serializer_as_message_if_not_exist(app_name, serializer_instance)


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
        Model = getattr(
            import_module(model_service_path),
            f"{model_name}Service",
        )

        if self.server is None:
            service_registry = RegistrySingleton()
            service_registry.register_service(Model)
            return

        pb2_grpc = import_module(
            f"{self.app_name}.{self.grpc_folder}.{self.app_name}_pb2_grpc"
        )
        add_server = getattr(pb2_grpc, f"add_{model_name}ControllerServicer_to_server")

        add_server(Model.as_servicer(), self.server)
