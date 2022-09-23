import logging
import sys
from dataclasses import dataclass, field
from importlib import import_module, reload
from pathlib import Path
from typing import Any, Dict, List, OrderedDict, Tuple, Type, Union

from django.apps.registry import apps
from django.conf import settings

from django_socio_grpc.services import Service
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils import camel_to_snake
from django_socio_grpc.utils.tools import ProtoComment

from .registry_singleton import RegistrySingleton

logger = logging.getLogger("django_socio_grpc")


@dataclass
class AppHandlerRegistry:
    app_name: str
    server: Any
    service_folder: str = "services"
    grpc_folder: str = "grpc"
    reload_services: bool = False
    disable_proto_generation: bool = False
    override_pb2_grpc_file_path: str = None
    to_root_grpc: bool = False
    registered_controllers: OrderedDict = field(default_factory=OrderedDict, init=False)
    registered_messages: OrderedDict[str, List[Tuple[str, str, str]]] = field(
        default_factory=OrderedDict, init=False
    )
    registered_messages_comments: Dict[str, ProtoComment] = field(
        default_factory=lambda: {}, init=False
    )

    def __post_init__(self):
        if self.reload_services:
            RegistrySingleton().clean_all()

        service_registry = RegistrySingleton()
        if self.app_name not in service_registry.registered_app:
            service_registry.registered_app[self.app_name] = self
        elif service_registry.registered_app[self.app_name] is not self:
            raise AppHandlerRegistryError(
                f"{self.app_name} is already registered by another AppHandlerRegistry"
            )

    def get_service_file_path(self, service_name):
        service_file_path = ""
        if self.service_folder:
            service_name = camel_to_snake(service_name)
            service_file_path = f"{self.app_name}.{self.service_folder}.{service_name}"
        else:
            service_file_path = f"{self.app_name}.services"

        return service_file_path

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

    def register(self, service: Union[str, Type[Service]], service_file_path=None):
        """
        Register a service to the grpc server

        :param service: Service class to register. This can also be the name of the service and we will gonna import it
        :param: service_file_path: If you pass the service name but he path is not possibly find manually
        """

        service_class: Type[Service]
        if isinstance(service, str):
            service_class = self.get_service_class_from_service_name(
                service, service_file_path
            )
        else:
            service_class = service

        if self.reload_services:
            reload(sys.modules[service_class.__module__])

        if self.server is None and self.disable_proto_generation:
            return

        service_class._app_handler = self
        service_class.register_actions()

        if self.server is None:
            return

        try:
            path = self.get_pb2_grpc_module()
            pb2_grpc = import_module(path)
            service_instance = service_class()

            controller_name = service_instance.get_service_name()
            add_server = getattr(
                pb2_grpc, f"add_{controller_name}ControllerServicer_to_server"
            )

            add_server(service_class.as_servicer(), self.server)
        except ModuleNotFoundError:
            logger.error(
                f"PB2 module {path} not found. Please generate proto before launching server"
            )

    def get_grpc_folder(self):
        base_dir = Path(settings.BASE_DIR)

        if self.to_root_grpc:
            path = base_dir / Path(grpc_settings.ROOT_GRPC_FOLDER) / self.app_name
        else:
            path = Path(apps.get_app_config(self.app_name).path) / self.grpc_folder

        resolved_path = path.resolve()

        if base_dir not in resolved_path.parents:
            logger.warn(
                f"{self.app_name} AppHandlerRegistry path ({resolved_path}) is not in current working directory"
                "You may want to use `to_root_grpc` option"
            )
        return resolved_path

    def get_grpc_module(self):
        if self.to_root_grpc:
            return ".".join([grpc_settings.ROOT_GRPC_FOLDER, self.app_name])
        else:
            return ".".join(
                [apps.get_app_config(self.app_name).module.__name__, self.grpc_folder]
            )

    def get_pb2_module(self):
        return f"{self.get_grpc_module()}.{self.app_name}_pb2"

    def get_pb2_grpc_module(self):
        return f"{self.get_grpc_module()}.{self.app_name}_pb2_grpc"

    def get_proto_path(self):
        return self.get_grpc_folder() / f"{self.app_name}.proto"


class AppHandlerRegistryError(Exception):
    pass
