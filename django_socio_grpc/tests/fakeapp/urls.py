from django_socio_grpc.utils.servicer_register import AppHandlerRegistry

# The API URLs are now determined automatically by the router.
urlpatterns = []


def grpc_handlers(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("UnitTestModelService")
    app_registry.register("SyncUnitTestModelService")
    app_registry.register("ForeignModelService")
    app_registry.register("RelatedFieldModelService")
    app_registry.register("SpecialFieldsModelService")
    app_registry.register("ImportStructEvenInArrayModelService")
    app_registry.register("BasicService")
