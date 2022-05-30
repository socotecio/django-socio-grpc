import sys
from importlib import reload

from django_socio_grpc.utils.registry_singleton import RegistrySingleton
from django_socio_grpc.utils.servicer_register import AppHandlerRegistry


def make_grpc_handler(name, *services, reload_services=False):
    def grpc_handler(server):
        if reload_services:
            RegistrySingleton().clean_all()
        app_registry = AppHandlerRegistry(name, server)
        for service in services:
            if reload_services:
                reload(sys.modules[service.__module__])
            app_registry.register(service)

    return grpc_handler
