from fakeapp.services.basic_service import BasicService
from fakeapp.services.default_value_service import DefaultValueService
from fakeapp.services.exception_service import ExceptionService
from fakeapp.services.foreign_model_service import ForeignModelService
from fakeapp.services.import_struct_even_in_array_model_service import (
    ImportStructEvenInArrayModelService,
)
from fakeapp.services.recursive_test_model_service import RecursiveTestModelService
from fakeapp.services.related_field_model_service import (
    RelatedFieldModelService,
    SimpleRelatedFieldModelService,
)
from fakeapp.services.special_fields_model_service import SpecialFieldsModelService
from fakeapp.services.stream_in_service import StreamInService
from fakeapp.services.sync_unit_test_model_service import SyncUnitTestModelService
from fakeapp.services.unit_test_model_service import UnitTestModelService

from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
from django_socio_grpc.tests.fakeapp.services.unit_test_model_with_struct_filter_service import (
    UnitTestModelWithStructFilterService,
)

# The API URLs are now determined automatically by the router.
urlpatterns = []


def grpc_handlers(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register(BasicService)
    app_registry.register(ForeignModelService)
    app_registry.register(ImportStructEvenInArrayModelService)
    app_registry.register(RelatedFieldModelService)
    app_registry.register(SimpleRelatedFieldModelService)
    app_registry.register(SpecialFieldsModelService)
    app_registry.register(SyncUnitTestModelService)
    app_registry.register(UnitTestModelService)
    app_registry.register(StreamInService)
    app_registry.register(ExceptionService)
    app_registry.register(RecursiveTestModelService)
    app_registry.register(UnitTestModelWithStructFilterService)
    app_registry.register(DefaultValueService)


services = (
    BasicService,
    ForeignModelService,
    ImportStructEvenInArrayModelService,
    RelatedFieldModelService,
    SimpleRelatedFieldModelService,
    SpecialFieldsModelService,
    SyncUnitTestModelService,
    UnitTestModelService,
    StreamInService,
    RecursiveTestModelService,
    UnitTestModelWithStructFilterService,
)
