import json
from datetime import datetime, timezone
from unittest import mock

import grpc
from fakeapp.grpc.fakeapp_pb2 import (
    UnitTestModelWithCacheListResponse,
    UnitTestModelWithCacheListWithStructFilterRequest,
    UnitTestModelWithCacheResponse,
    UnitTestModelWithCacheRetrieveRequest,
)
from fakeapp.grpc.fakeapp_pb2_grpc import (
    UnitTestModelWithCacheControllerStub,
    add_UnitTestModelWithCacheControllerServicer_to_server,
)
from fakeapp.models import UnitTestModel
from fakeapp.services.unit_test_model_with_cache_service import (
    UnitTestModelWithCacheService,
)
from freezegun import freeze_time
from google.protobuf import empty_pb2, struct_pb2

from django.core.cache import caches
from django.test import TestCase, override_settings
from django_socio_grpc.cache import get_dsg_cache
from django_socio_grpc.request_transformer import (
    GRPCInternalProxyResponse,
)
from django_socio_grpc.settings import FilterAndPaginationBehaviorOptions, grpc_settings

from .grpc_test_utils.fake_grpc import FakeAsyncContext, FakeFullAIOGRPC


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
        # INFO - AM - 26/07/2024 - Clear all cache after each test to be sure none conflict
        for cache in caches.all():
            cache.clear()

    @mock.patch("django_socio_grpc.cache.get_cache_key")
    @mock.patch("django_socio_grpc.cache.learn_cache_key")
    async def test_verify_that_response_in_cache(
        self, mock_learn_cache_key, mock_get_cache_key
    ):
        """
        Just verify that the response is in cache with the key returned by learn_cache_key
        """
        cache_test_key = "test_cache_key"
        mock_learn_cache_key.return_value = cache_test_key
        mock_get_cache_key.return_value = None

        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 3)

        cache = get_dsg_cache()
        self.assertEqual(cache.get(cache_test_key).grpc_response, response)

        mock_learn_cache_key.assert_called_with(
            mock.ANY,
            mock.ANY,
            cache_timeout=grpc_settings.GRPC_CACHE_SECONDS,
            key_prefix=grpc_settings.GRPC_CACHE_KEY_PREFIX,
            cache=cache,
        )
        mock_get_cache_key.assert_called_with(
            mock.ANY,
            key_prefix=grpc_settings.GRPC_CACHE_KEY_PREFIX,
            method="GET",
            cache=cache,
        )

    @mock.patch("django_socio_grpc.cache.get_cache_key")
    async def test_verify_that_if_response_in_cache_it_return_it(self, mock_get_cache_key):
        """
        Just verify that is a repsonse already exist in cache with the key returned by get_cache_key it return it
        """
        cache_test_key = "test_cache_key"
        mock_get_cache_key.return_value = cache_test_key

        results = [
            UnitTestModelWithCacheResponse(title="test_manual_1", text="test_manual_1"),
            UnitTestModelWithCacheResponse(title="test_manual_2", text="test_manual_2"),
        ]
        grpc_response = UnitTestModelWithCacheListResponse(results=results, count=2)

        fake_socio_response = GRPCInternalProxyResponse(grpc_response, FakeAsyncContext())

        cache = get_dsg_cache()
        cache.set(
            cache_test_key,
            fake_socio_response,
        )

        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.count, 2)
        self.assertEqual(response.results[0].title, "test_manual_1")

    @mock.patch("django_socio_grpc.cache.get_cache_key")
    @mock.patch("django_socio_grpc.cache.learn_cache_key")
    async def test_cache_decorators_paremeters_correctly_working(
        self, mock_learn_cache_key, mock_get_cache_key
    ):
        """
        Verify that django get_cache_key and learn_cache_key are correctly called with the decorators parameters
        """
        cache_test_key = "test_cache_key"
        mock_learn_cache_key.return_value = cache_test_key
        mock_get_cache_key.return_value = None

        second_cache = caches["second"]

        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        first_unit_test_model = await UnitTestModel.objects.afirst()
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = UnitTestModelWithCacheRetrieveRequest(id=first_unit_test_model.id)
        await grpc_stub.Retrieve(request=request)

        mock_learn_cache_key.assert_called_with(
            mock.ANY, mock.ANY, cache_timeout=1000, key_prefix="second", cache=second_cache
        )

    @override_settings(
        GRPC_FRAMEWORK={
            "GRPC_ASYNC": True,
            "PAGINATION_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
        }
    )
    async def test_when_page_change_in_struct_cache_not_used(
        self,
    ):
        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")

        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        pagination_as_dict = {"page": 2}
        pagination_as_struct = struct_pb2.Struct()
        pagination_as_struct.update(pagination_as_dict)
        request = UnitTestModelWithCacheListWithStructFilterRequest(
            _pagination=pagination_as_struct
        )
        response = await grpc_stub.ListWithStructFilter(request=request)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "zzzz")

    async def test_when_page_change_in_metadata_cache_not_used(
        self,
    ):
        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")

        pagination_as_dict = {"page": 2}
        metadata = (("pagination", json.dumps(pagination_as_dict)),)

        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()
        response = await grpc_stub.List(request=request, metadata=metadata)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "zzzz")

    @override_settings(
        GRPC_FRAMEWORK={
            "GRPC_ASYNC": True,
            "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
        }
    )
    async def test_when_filter_change_in_struct_cache_not_used(
        self,
    ):
        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")

        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        filter_as_dict = {"title": "zzzzzzz"}
        filter_as_struct = struct_pb2.Struct()
        filter_as_struct.update(filter_as_dict)
        request = UnitTestModelWithCacheListWithStructFilterRequest(_filters=filter_as_struct)
        response = await grpc_stub.ListWithStructFilter(request=request)

        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.results[0].title, "zzzzzzz")

    async def test_when_filter_change_in_metadata_cache_not_used(
        self,
    ):
        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")

        pagination_as_dict = {"title": "zzzzzzz"}
        metadata = (("filters", json.dumps(pagination_as_dict)),)

        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()
        response = await grpc_stub.List(request=request, metadata=metadata)

        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.results[0].title, "zzzzzzz")

    async def test_when_headers_vary_route_not_cached(
        self,
    ):
        """
        In this test we verify that by setting different value on the custom_header metadata the cache is not used
        This is done by the vary_on_metadata decorator used in the service
        """
        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()

        metadata_1 = (("custom_header", "test1"),)
        response = await grpc_stub.List(request=request, metadata=metadata_1)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")
        self.assertEqual(response.results[0].verify_custom_header, "test1")

        await UnitTestModel.objects.filter(title="z").aupdate(title="a")

        metadata_2 = (("custom_header", "test2"),)
        response = await grpc_stub.List(request=request, metadata=metadata_2)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "a")
        self.assertEqual(response.results[0].verify_custom_header, "test2")

    async def test_when_headers_vary_but_not_specified_in_decorator_route_is_cached(
        self,
    ):
        """
        In this test we verify that by setting different value on the custom_header metadata the cache is not used
        This is done by the vary_on_metadata decorator used in the service
        """
        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()

        metadata_1 = (("metdata_not_specified", "test1"),)
        response = await grpc_stub.List(request=request, metadata=metadata_1)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")

        await UnitTestModel.objects.filter(title="z").aupdate(title="a")

        metadata_2 = (("metdata_not_specified", "test2"),)
        response = await grpc_stub.List(request=request, metadata=metadata_2)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")

    @mock.patch(
        "fakeapp.services.unit_test_model_with_cache_service.UnitTestModelWithCacheService.custom_function_not_called_when_cached"
    )
    async def test_cache_working_really(self, mock_custom_function_not_called_when_cached):
        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()

        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")

        mock_custom_function_not_called_when_cached.assert_called_once()

        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")
        # self.assertEqual(response.results[0].verify_custom_header, "test2")

        mock_custom_function_not_called_when_cached.assert_called_once()

    async def test_cache_control_and_expires_metadata_correctly_set(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()

        with freeze_time(datetime(2024, 7, 26, 14, 0, 0, tzinfo=timezone.utc)):
            _, call = await grpc_stub.List.with_call(request=request)

        metadata_to_dict = dict(call.trailing_metadata())

        self.assertEqual(metadata_to_dict["Expires"], "Fri, 26 Jul 2024 14:05:00 GMT")
        self.assertEqual(metadata_to_dict["Cache-Control"], "max-age=300")

    async def test_age_metdata_set_when_expires_metadata_set(self):
        """
        If a response is returned from cache there is an "Age" metadata set explaining how old is the cached response
        """
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()

        with freeze_time(datetime(2024, 7, 26, 14, 0, 0, tzinfo=timezone.utc)):
            _, call = await grpc_stub.List.with_call(request=request)

        metadata_before_cache = dict(call.trailing_metadata())

        self.assertEqual(metadata_before_cache["Expires"], "Fri, 26 Jul 2024 14:05:00 GMT")
        self.assertEqual(metadata_before_cache["Cache-Control"], "max-age=300")
        self.assertNotIn("Age", metadata_before_cache)

        with freeze_time(datetime(2024, 7, 26, 14, 2, 0, tzinfo=timezone.utc)):
            _, call_with_age = await grpc_stub.List.with_call(request=request)

        metadata_to_dict = dict(call_with_age.trailing_metadata())

        self.assertEqual(metadata_to_dict["Expires"], "Fri, 26 Jul 2024 14:05:00 GMT")
        self.assertEqual(metadata_to_dict["Cache-Control"], "max-age=300")
        self.assertEqual(metadata_to_dict["Age"], 120)

    @mock.patch(
        "fakeapp.services.unit_test_model_with_cache_service.UnitTestModelWithCacheService.custom_function_not_called_when_cached"
    )
    async def test_cache_not_set_when_max_age_0_in_cache_control_in_the_response(
        self, mock_custom_function_not_called_when_cached
    ):
        # INFO - AM - 26/07/2024 - This mock the server action of setting max-age=0 to the response cache control metadata
        def set_max_age_to_0(unit_test_model_with_cache_service, *args, **kwargs):
            metadata = (("Cache-Control", "max-age=0"),)
            unit_test_model_with_cache_service.context.set_trailing_metadata(metadata)

        mock_custom_function_not_called_when_cached.side_effect = set_max_age_to_0

        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()

        response = await grpc_stub.List(request=request)
        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")

        mock_custom_function_not_called_when_cached.assert_called_once()

        await UnitTestModel.objects.filter(title="z").aupdate(title="a")

        response = await grpc_stub.List(request=request)
        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "a")

        self.assertEqual(mock_custom_function_not_called_when_cached.call_count, 2)

    @mock.patch(
        "fakeapp.services.unit_test_model_with_cache_service.UnitTestModelWithCacheService.custom_function_not_called_when_cached"
    )
    async def test_cache_not_set_when_not_successfull_request(
        self, mock_custom_function_not_called_when_cached
    ):
        # INFO - AM - 26/07/2024 - This mock the server action of raising an exception
        def raise_exception(unit_test_model_with_cache_service, *args, **kwargs):
            raise Exception("Error")

        mock_custom_function_not_called_when_cached.side_effect = raise_exception

        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()

        with self.assertRaises(grpc.RpcError):
            response = await grpc_stub.List(request=request)

        mock_custom_function_not_called_when_cached.side_effect = None

        await UnitTestModel.objects.filter(title="z").aupdate(title="a")

        response = await grpc_stub.List(request=request)
        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "a")

        self.assertEqual(mock_custom_function_not_called_when_cached.call_count, 2)

    @mock.patch(
        "fakeapp.services.unit_test_model_with_cache_service.UnitTestModelWithCacheService.custom_function_not_called_when_cached"
    )
    async def test_cache_not_set_when_private_in_cache_control(
        self, mock_custom_function_not_called_when_cached
    ):
        # INFO - AM - 26/07/2024 - This mock the server action of setting private to the response cache control metadata
        def set_cache_control_private(unit_test_model_with_cache_service, *args, **kwargs):
            metadata = (("Cache-Control", "private"),)
            unit_test_model_with_cache_service.context.set_trailing_metadata(metadata)

        mock_custom_function_not_called_when_cached.side_effect = set_cache_control_private

        self.assertEqual(await UnitTestModel.objects.acount(), 10)
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()

        response = await grpc_stub.List(request=request)
        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "z")

        mock_custom_function_not_called_when_cached.assert_called_once()

        await UnitTestModel.objects.filter(title="z").aupdate(title="a")

        response = await grpc_stub.List(request=request)
        self.assertEqual(len(response.results), 3)
        self.assertEqual(response.results[0].title, "a")

        self.assertEqual(mock_custom_function_not_called_when_cached.call_count, 2)

    async def test_vary_metadata_correctly_set_when_using_decorator(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithCacheControllerStub)
        request = empty_pb2.Empty()

        response, call = await grpc_stub.List.with_call(request=request)

        metadata_to_dict = dict(call.trailing_metadata())

        self.assertEqual(metadata_to_dict["Vary"], "CUSTOM_HEADER")