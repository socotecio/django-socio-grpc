import logging
import re
import sys
from importlib import import_module, reload

from .registry_singleton import RegistrySingleton

logger = logging.getLogger("django_socio_grpc")


class AppHandlerRegistry:
    def __init__(
        self,
        app_name,
        server,
        service_folder="services",
        grpc_folder="grpc",
        reload_service=False,
        disable_proto_generation=False,
        override_pb2_grpc_file_path=None,
    ):
        self.app_name = app_name
        self.server = server
        self.service_folder = service_folder
        self.grpc_folder = grpc_folder
        self.disable_proto_generation = disable_proto_generation
        self.override_pb2_grpc_file_path = override_pb2_grpc_file_path
        if reload_service:
            RegistrySingleton().clean_all()
        self.reload_services = reload_service

    def get_service_file_path(self, service_name):
        service_file_path = ""
        if self.service_folder:
            service_name = self.camel_to_snake(service_name)
            service_file_path = f"{self.app_name}.{self.service_folder}.{service_name}"
        else:
            service_file_path = f"{self.app_name}.services"

        return service_file_path

    def camel_to_snake(self, name):
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    def get_service_class_from_service_name(self, service_name, service_file_path=None):
        is_manual_service_path = service_file_path is not None

        try:
            # INFO - AM - 21/01/2022 - Old way of doing where we was generating from model so we was just added Service at the end. Please do not use this feature anymore
            # We need to check old way first because instance of model existing in service module so it's import model instead of service...

            if service_file_path is not is_manual_service_path:
                service_file_path = self.get_service_file_path(service_name)

            service_class = getattr(
                import_module(service_file_path),
                service_name,
            )
        except ModuleNotFoundError:
            logger.warning(
                f"WARNING: Service {service_name} not found. Since new version you need to pass the explicit name of the service. The feature that was adding Service at the end of the name will be removed in version 1.0.0"
            )

            service_name = f"{service_name}Service"

            if service_file_path is not is_manual_service_path:
                service_file_path = self.get_service_file_path(service_name)

            service_class = getattr(
                import_module(service_file_path),
                service_name,
            )

        return service_class

    def register(self, service, service_file_path=None):
        """
        Register a service to the grpc server

        :param service: Service class to register. This can also be the name of the service and we will gonna import it
        :param: service_file_path: If you pass the service name but he path is not possibly find manually
        """

        service_class = service
        if isinstance(service_class, str):
            service_class = self.get_service_class_from_service_name(
                service_class, service_file_path
            )

        if self.reload_services:
            reload(sys.modules[service_class.__module__])

        if self.server is None:
            if self.disable_proto_generation:
                return
            service_registry = RegistrySingleton()
            service_registry.register_service(self.app_name, service_class)
            return

        try:
            if self.override_pb2_grpc_file_path is not None:
                pb2_grpc = import_module(self.override_pb2_grpc_file_path)
            else:
                pb2_grpc = import_module(
                    f"{self.app_name}.{self.grpc_folder}.{self.app_name}_pb2_grpc"
                )
            service_instance = service_class()

            controller_name = service_instance.get_service_name()
            add_server = getattr(
                pb2_grpc, f"add_{controller_name}ControllerServicer_to_server"
            )

            add_server(service_class.as_servicer(), self.server)
        except ModuleNotFoundError:
            if self.override_pb2_grpc_file_path is not None:
                logger.error(
                    f"PB2 module {self.override_pb2_grpc_file_path} not found. Please generate proto before launching server"
                )
                return
            logger.error(
                f"PB2 module {self.app_name}.{self.grpc_folder}.{self.app_name}_pb2_grpc not found. Please generate proto before launching server"
            )
