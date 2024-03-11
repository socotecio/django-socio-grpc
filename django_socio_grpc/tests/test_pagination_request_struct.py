import json

from django.test import TestCase, override_settings
from fakeapp.grpc.fakeapp_pb2 import UnitTestModelWithStructFilterListRequest
from fakeapp.grpc.fakeapp_pb2_grpc import (
    UnitTestModelWithStructFilterControllerStub,
    add_UnitTestModelWithStructFilterControllerServicer_to_server,
)
from fakeapp.models import UnitTestModel
from fakeapp.services.unit_test_model_with_struct_filter_service import (
    UnitTestModelWithStructFilterService,
)
from google.protobuf import struct_pb2

from django_socio_grpc.settings import FilterAndPaginationBehaviorOptions

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestPaginationRequestStruct(TestCase):
    def setUp(self):
        for idx in range(10):
            title = "z" * (idx + 1)
            text = chr(idx + ord("a")) + chr(idx + ord("b")) + chr(idx + ord("c"))
            UnitTestModel(title=title, text=text).save()

        self.fake_grpc = FakeFullAIOGRPC(
            add_UnitTestModelWithStructFilterControllerServicer_to_server,
            UnitTestModelWithStructFilterService.as_servicer(),
        )

    def tearDown(self):
        self.fake_grpc.close()

    async def test_page_number_pagination_with_struct_request_not_working_because_metadata_only_behavior(
        self,
    ):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithStructFilterControllerStub)
        pagination_as_dict = {"page_size": 6}
        pagination_as_struct = struct_pb2.Struct()
        pagination_as_struct.update(pagination_as_dict)
        request = UnitTestModelWithStructFilterListRequest(_pagination=pagination_as_struct)
        response = await grpc_stub.List(request=request)

        self.assertEqual(response.count, 10)
        self.assertEqual(len(response.results), 3)

    @override_settings(
        GRPC_FRAMEWORK={
            "GRPC_ASYNC": True,
            "PAGINATION_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
        }
    )
    async def test_page_number_pagination_with_struct_request_only(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithStructFilterControllerStub)
        pagination_as_dict = {"page_size": 6}
        pagination_as_struct = struct_pb2.Struct()
        pagination_as_struct.update(pagination_as_dict)
        request = UnitTestModelWithStructFilterListRequest(_pagination=pagination_as_struct)
        response = await grpc_stub.List(request=request)

        self.assertEqual(response.count, 10)
        self.assertEqual(len(response.results), 6)

        # Testing metadata pagination not working
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithStructFilterControllerStub)
        request = UnitTestModelWithStructFilterListRequest()
        pagination_as_dict = {"page_size": 6}
        metadata = (("PAGINATION", (json.dumps(pagination_as_dict))),)
        response = await grpc_stub.List(request=request, metadata=metadata)

        self.assertEqual(response.count, 10)
        self.assertEqual(len(response.results), 3)

    @override_settings(
        GRPC_FRAMEWORK={
            "GRPC_ASYNC": True,
            "PAGINATION_BEHAVIOR": FilterAndPaginationBehaviorOptions.METADATA_AND_REQUEST_STRUCT,
        }
    )
    async def test_page_number_pagination_with_struct_request_and_metadata(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithStructFilterControllerStub)
        pagination_as_dict = {"page_size": 6}
        pagination_as_struct = struct_pb2.Struct()
        pagination_as_struct.update(pagination_as_dict)
        request = UnitTestModelWithStructFilterListRequest(_pagination=pagination_as_struct)
        response = await grpc_stub.List(request=request)

        self.assertEqual(response.count, 10)
        self.assertEqual(len(response.results), 6)

        # Testing metadata pagination also working
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithStructFilterControllerStub)
        request = UnitTestModelWithStructFilterListRequest()
        pagination_as_dict = {"page_size": 6}
        metadata = (("PAGINATION", (json.dumps(pagination_as_dict))),)
        response = await grpc_stub.List(request=request, metadata=metadata)

        self.assertEqual(response.count, 10)
        self.assertEqual(len(response.results), 6)
