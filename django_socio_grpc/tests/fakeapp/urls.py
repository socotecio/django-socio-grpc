from django_socio_grpc.utils.servicer_register import AppHandlerRegistry

# The API URLs are now determined automatically by the router.
urlpatterns = []


def grpc_handlers(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("UnitTestModel")
    app_registry.register("ForeignModel")
