from fakeapp.services.basic_service import BasicService
from fakeapp.services.foreign_model_service import ForeignModelService
from fakeapp.services.import_struct_even_in_array_model_service import (
    ImportStructEvenInArrayModelService,
)
from fakeapp.services.related_field_model_service import RelatedFieldModelService
from fakeapp.services.special_fields_model_service import SpecialFieldsModelService
from fakeapp.services.sync_unit_test_model_service import SyncUnitTestModelService
from fakeapp.services.unit_test_model_service import UnitTestModelService

from django_socio_grpc.tests.fakeapp.utils import make_grpc_handler

# The API URLs are now determined automatically by the router.
urlpatterns = []

services = (
    BasicService,
    ForeignModelService,
    ImportStructEvenInArrayModelService,
    RelatedFieldModelService,
    SpecialFieldsModelService,
    SyncUnitTestModelService,
    UnitTestModelService,
)


grpc_handlers = make_grpc_handler("fakeapp", *services)

reloaded_grpc_handlers = make_grpc_handler("fakeapp", *services, reload_services=True)
