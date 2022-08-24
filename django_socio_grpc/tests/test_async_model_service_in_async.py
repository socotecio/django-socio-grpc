from datetime import datetime

from asgiref.sync import sync_to_async
from django.test import TestCase
from django.utils import timezone
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    UnitTestModelControllerStub,
    add_UnitTestModelControllerServicer_to_server,
)
from fakeapp.models import UnitTestModel
from fakeapp.services.unit_test_model_service import UnitTestModelService
from freezegun import freeze_time

from django_socio_grpc.settings import grpc_settings

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


class TestAsyncModelService(TestCase):
    def setUp(self):
        grpc_settings.GRPC_ASYNC = True
        self.fake_grpc = FakeFullAIOGRPC(
            add_UnitTestModelControllerServicer_to_server, UnitTestModelService.as_servicer()
        )

        self.create_instances()

    def tearDown(self):
        grpc_settings.GRPC_ASYNC = False
        self.fake_grpc.close()

    def create_instances(self):
        for idx in range(10):
            title = "z" * (idx + 1)
            text = chr(idx + ord("a")) + chr(idx + ord("b")) + chr(idx + ord("c"))
            UnitTestModel(title=title, text=text).save()

    async def test_async_create(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = fakeapp_pb2.UnitTestModelRequest(title="fake", text="text")
        response = await grpc_stub.Create(request=request)

        self.assertNotEqual(response.id, None)
        self.assertEqual(response.title, "fake")
        self.assertEqual(response.text, "text")
        self.assertEqual(await sync_to_async(UnitTestModel.objects.count)(), 11)

    async def test_async_list(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = fakeapp_pb2.UnitTestModelListRequest()
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 10)

    async def test_async_retrieve(self):
        unit_id = (await sync_to_async(UnitTestModel.objects.first)()).id
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = fakeapp_pb2.UnitTestModelRetrieveRequest(id=unit_id)
        response = await grpc_stub.Retrieve(request=request)

        self.assertEqual(response.title, "z")
        self.assertEqual(response.text, "abc")

    async def test_async_update(self):
        unit_id = (await sync_to_async(UnitTestModel.objects.first)()).id
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = fakeapp_pb2.UnitTestModelRequest(
            id=unit_id, title="newTitle", text="newText"
        )
        response = await grpc_stub.Update(request=request)

        self.assertEqual(response.title, "newTitle")
        self.assertEqual(response.text, "newText")

    async def test_async_destroy(self):
        unit_id = (await sync_to_async(UnitTestModel.objects.first)()).id
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = fakeapp_pb2.UnitTestModelDestroyRequest(id=unit_id)
        await grpc_stub.Destroy(request=request)

        self.assertFalse(
            await sync_to_async(UnitTestModel.objects.filter(id=unit_id).exists)()
        )

    async def test_async_stream(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = fakeapp_pb2.UnitTestModelStreamRequest()

        response_list = []
        stream = grpc_stub.Stream(request=request)

        import grpc

        while True:
            result = await stream.read()
            if result == grpc.aio.EOF:
                break
            response_list.append(result)

        self.assertEqual(len(response_list), 10)

    async def test_async_stream_generator(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = fakeapp_pb2.UnitTestModelStreamRequest()

        response_list = []
        async for response in grpc_stub.Stream(request=request):
            response_list.append(response)

        self.assertEqual(len(response_list), 10)

    async def test_async_list_custom_action(self):

        with freeze_time(datetime(2022, 1, 21, tzinfo=timezone.utc)):
            grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
            request = fakeapp_pb2.UnitTestModelListWithExtraArgsRequest(archived=False)
            response = await grpc_stub.ListWithExtraArgs(request=request)

            self.assertEqual(len(response.results), 10)

            self.assertEqual(response.query_fetched_datetime, "2022-01-21T00:00:00Z")

    async def test_async_partial_update(self):
        instance = await sync_to_async(UnitTestModel.objects.first)()

        old_text = instance.text

        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)

        request = fakeapp_pb2.UnitTestModelPartialUpdateRequest(
            id=instance.id, _partial_update_fields=["title"], title="newTitle"
        )
        response = await grpc_stub.PartialUpdate(request=request)

        self.assertEqual(response.title, "newTitle")
        self.assertEqual(response.text, old_text)
