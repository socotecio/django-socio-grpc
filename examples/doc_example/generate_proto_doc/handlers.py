from django_socio_grpc.protobuf import AppHandlerRegistry


def grpc_handlers(server):
    app_registry = AppHandlerRegistry("generate_proto_doc", server)
    app_registry.register("Something")
