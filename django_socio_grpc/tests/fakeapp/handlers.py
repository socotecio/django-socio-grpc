from fakeapp.services.basic_service import BasicService
from fakeapp.services.foreign_model_service import ForeignModelService
from fakeapp.services.import_struct_even_in_array_model_service import (
    ImportStructEvenInArrayModelService,
)
from fakeapp.services.related_field_model_service import RelatedFieldModelService
from fakeapp.services.special_fields_model_service import SpecialFieldsModelService
from fakeapp.services.sync_unit_test_model_service import SyncUnitTestModelService
from fakeapp.services.unit_test_model_service import UnitTestModelService

from django_socio_grpc.utils.servicer_register import AppHandlerRegistry

# The API URLs are now determined automatically by the router.
urlpatterns = []


def grpc_handlers(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register(BasicService)
    app_registry.register(ForeignModelService)
    app_registry.register(ImportStructEvenInArrayModelService)
    app_registry.register(RelatedFieldModelService)
    app_registry.register(SpecialFieldsModelService)
    app_registry.register(SyncUnitTestModelService)
    app_registry.register(UnitTestModelService)


services = (
    BasicService,
    ForeignModelService,
    ImportStructEvenInArrayModelService,
    RelatedFieldModelService,
    SpecialFieldsModelService,
    SyncUnitTestModelService,
    UnitTestModelService,
)
