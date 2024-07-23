from unittest import mock

from django.test import TestCase, override_settings
from fakeapp.grpc.fakeapp_pb2_grpc import (
    UnitTestModelWithCacheControllerStub,
    add_UnitTestModelWithCacheControllerServicer_to_server,
)
from fakeapp.models import UnitTestModel
from fakeapp.services.unit_test_model_with_cache_service import (
    UnitTestModelWithCacheService,
)
from google.protobuf import empty_pb2

from django_socio_grpc.cache import get_dsg_cache

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestCacheService(TestCase):
    def setUp(self):
        for idx in range(10):
            title = "z" * (idx + 1)
            text = chr(idx + ord("a")) + chr(idx + ord("b")) + chr(idx + ord("c"))
            UnitTestModel(title=title, text=text).save()

        self.fake_grpc = FakeFullAIOGRPC(
            add_UnitTestModelWithCacheControllerServicer_to_server,
            UnitTestModelWithCacheService.as_servicer(),
        )

    def tearDown(self):
        self.fake_grpc.close()

    # @mock.patch.object(
    #     UnitTestModelWithCacheService,
    #     "List",
    #     side_effect=UnitTestModelWithCacheService.List,
    # )
    @mock.patch("django_socio_grpc.cache.learn_dsg_cache_key")
    async def test_basic_list_cache_working(self, mock_learn_dsg_cache_key):
        cache_test_key = "test_cache_key"
        mock_learn_dsg_cache_key.return_value = cache_test_key

        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 3)

        cache = get_dsg_cache()
        self.assertEqual(cache.get(cache_test_key).grpc_response, response)
        assert False

    # async def test_list_with_filter_struct_cache_working(
    #     self,
    # ):
    #     grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
    #     pagination_as_dict = {"page_size": 6}
    #     pagination_as_struct = struct_pb2.Struct()
    #     pagination_as_struct.update(pagination_as_dict)
    #     request = UnitTestModelWithStructFilterListRequest(_pagination=pagination_as_struct)
    #     response = await grpc_stub.List(request=request)

    #     self.assertEqual(response.count, 10)
    #     self.assertEqual(len(response.results), 3)

    # @override_settings(
    #     GRPC_FRAMEWORK={
    #         "GRPC_ASYNC": True,
    #         "PAGINATION_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
    #     }
    # )
    # async def test_page_number_pagination_with_struct_request_only(self):
    #     grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
    #     pagination_as_dict = {"page_size": 6}
    #     pagination_as_struct = struct_pb2.Struct()
    #     pagination_as_struct.update(pagination_as_dict)
    #     request = UnitTestModelWithStructFilterListRequest(_pagination=pagination_as_struct)
    #     response = await grpc_stub.List(request=request)

    #     self.assertEqual(response.count, 10)
    #     self.assertEqual(len(response.results), 6)

    #     # Testing metadata pagination not working
    #     grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
    #     request = UnitTestModelWithStructFilterListRequest()
    #     pagination_as_dict = {"page_size": 6}
    #     metadata = (("PAGINATION", (json.dumps(pagination_as_dict))),)
    #     response = await grpc_stub.List(request=request, metadata=metadata)

    #     self.assertEqual(response.count, 10)
    #     self.assertEqual(len(response.results), 3)

    # @override_settings(
    #     GRPC_FRAMEWORK={
    #         "GRPC_ASYNC": True,
    #         "PAGINATION_BEHAVIOR": FilterAndPaginationBehaviorOptions.METADATA_AND_REQUEST_STRUCT,
    #     }
    # )
    # async def test_page_number_pagination_with_struct_request_and_metadata(self):
    #     grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
    #     pagination_as_dict = {"page_size": 6}
    #     pagination_as_struct = struct_pb2.Struct()
    #     pagination_as_struct.update(pagination_as_dict)
    #     request = UnitTestModelWithStructFilterListRequest(_pagination=pagination_as_struct)
    #     response = await grpc_stub.List(request=request)

    #     self.assertEqual(response.count, 10)
    #     self.assertEqual(len(response.results), 6)

    #     # Testing metadata pagination also working
    #     grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
    #     request = UnitTestModelWithStructFilterListRequest()
    #     pagination_as_dict = {"page_size": 6}
    #     metadata = (("PAGINATION", (json.dumps(pagination_as_dict))),)
    #     response = await grpc_stub.List(request=request, metadata=metadata)

    #     self.assertEqual(response.count, 10)
    #     self.assertEqual(len(response.results), 6)
