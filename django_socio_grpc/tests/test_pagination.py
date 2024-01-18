import json

from django.test import TestCase, override_settings
from fakeapp.grpc.fakeapp_pb2 import UnitTestModelListRequest
from fakeapp.grpc.fakeapp_pb2_grpc import (
    UnitTestModelControllerStub,
    add_UnitTestModelControllerServicer_to_server,
)
from fakeapp.models import UnitTestModel
from fakeapp.serializers import UnitTestModelSerializer
from fakeapp.services.unit_test_model_service import UnitTestModelService
from rest_framework.pagination import PageNumberPagination

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 100


class UnitTestModelServiceWithDifferentPagination(UnitTestModelService):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelSerializer
    pagination_class = StandardResultsSetPagination


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestPagination(TestCase):
    def setUp(self):
        for idx in range(10):
            title = "z" * (idx + 1)
            text = chr(idx + ord("a")) + chr(idx + ord("b")) + chr(idx + ord("c"))
            UnitTestModel(title=title, text=text).save()
        self.fake_grpc = FakeFullAIOGRPC(
            add_UnitTestModelControllerServicer_to_server,
            UnitTestModelServiceWithDifferentPagination.as_servicer(),
        )

    def tearDown(self):
        self.fake_grpc.close()

    async def test_page_number_pagination(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = UnitTestModelListRequest()
        response = await grpc_stub.List(request=request)

        self.assertEqual(response.count, 10)
        self.assertEqual(len(response.results), 3)

    async def test_another_page_number_pagination(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = UnitTestModelListRequest()
        pagination_as_dict = {"page_size": 6}
        metadata = (("PAGINATION", (json.dumps(pagination_as_dict))),)
        response = await grpc_stub.List(request=request, metadata=metadata)

        self.assertEqual(response.count, 10)
        self.assertEqual(len(response.results), 6)
