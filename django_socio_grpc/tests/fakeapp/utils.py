from django_socio_grpc.utils.servicer_register import AppHandlerRegistry


def make_reloaded_grpc_handler(name, *services):
    def grpc_handler(server):
        app_registry = AppHandlerRegistry(name, server, reload_service=True)
        for service in services:
            app_registry.register(service)

    return grpc_handler
