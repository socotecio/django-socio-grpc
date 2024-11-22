from django_socio_grpc.services import AppHandlerRegistry


def make_reloaded_grpc_handler(name, *services):
    def grpc_handler(server, directory: str = None):
        app_registry = AppHandlerRegistry(name, server, reload_services=True)
        for service in services:
            app_registry.register(service)

    return grpc_handler
