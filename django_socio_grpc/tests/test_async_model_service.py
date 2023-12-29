from datetime import datetime, timezone

from asgiref.sync import sync_to_async
from django.test import TestCase, override_settings
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    RelatedFieldModelControllerStub,
    SimpleRelatedFieldModelControllerStub,
    UnitTestModelControllerStub,
    add_RelatedFieldModelControllerServicer_to_server,
    add_SimpleRelatedFieldModelControllerServicer_to_server,
    add_UnitTestModelControllerServicer_to_server,
)
from fakeapp.models import ForeignModel, RelatedFieldModel, UnitTestModel
from fakeapp.services.unit_test_model_service import UnitTestModelService
from freezegun import freeze_time

from django_socio_grpc.tests.fakeapp.services.related_field_model_service import (
    RelatedFieldModelService,
    SimpleRelatedFieldModelService,
)

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestAsyncModelService(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_UnitTestModelControllerServicer_to_server, UnitTestModelService.as_servicer()
        )

        self.create_instances()

    def tearDown(self):
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

    async def test_optional_field(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = fakeapp_pb2.UnitTestModelRequest(title="fake")
        response = await grpc_stub.Create(request=request)

        self.assertFalse(response.HasField("text"))

        request = fakeapp_pb2.UnitTestModelRetrieveRequest(id=response.id)
        response = await grpc_stub.Retrieve(request=request)

        self.assertFalse(response.HasField("text"))

        instance = await UnitTestModel.objects.aget(id=response.id)
        assert instance.text is None


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestAsyncRelatedFieldModelService(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_RelatedFieldModelControllerServicer_to_server,
            RelatedFieldModelService.as_servicer(),
        )

    def tearDown(self):
        self.fake_grpc.close()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.item1 = RelatedFieldModelService.queryset.create()
        cls.foreign = ForeignModel.objects.create(name="foreign")
        cls.item2 = RelatedFieldModelService.queryset.create(foreign=cls.foreign)

    async def test_async_retrieve(self):
        grpc_stub = self.fake_grpc.get_fake_stub(RelatedFieldModelControllerStub)

        request = fakeapp_pb2.RelatedFieldModelRetrieveRequest(uuid=str(self.item1.uuid))
        response = await grpc_stub.Retrieve(request=request)

        self.assertEqual(response.proto_slug_related_field, "")

        request = fakeapp_pb2.RelatedFieldModelRetrieveRequest(uuid=str(self.item2.uuid))
        response = await grpc_stub.Retrieve(request=request)

        self.assertEqual(response.proto_slug_related_field, str(self.foreign.uuid))


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestSimpleRelatedFieldModelService(TestCase):
    """
    This tests the behavior of PrimaryKeyRelatedField with UUIDField
    when dealing with serializers converting to/from proto.
    """

    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_SimpleRelatedFieldModelControllerServicer_to_server,
            SimpleRelatedFieldModelService.as_servicer(),
        )

    def tearDown(self):
        self.fake_grpc.close()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.item1 = RelatedFieldModel.objects.create()
        cls.foreign = ForeignModel.objects.create(name="foreign")
        cls.item2 = RelatedFieldModel.objects.create(foreign=cls.foreign)

    async def test_async_retrieve(self):
        grpc_stub = self.fake_grpc.get_fake_stub(SimpleRelatedFieldModelControllerStub)

        request = fakeapp_pb2.SimpleRelatedFieldModelRetrieveRequest(uuid=str(self.item1.uuid))
        response = await grpc_stub.Retrieve(request=request)

        self.assertEqual(response.foreign, "")

        request = fakeapp_pb2.SimpleRelatedFieldModelRetrieveRequest(uuid=str(self.item2.uuid))
        response = await grpc_stub.Retrieve(request=request)

        self.assertEqual(response.foreign, str(self.foreign.uuid))

    async def test_async_create(self):
        grpc_stub = self.fake_grpc.get_fake_stub(SimpleRelatedFieldModelControllerStub)

        request = fakeapp_pb2.SimpleRelatedFieldModelRequest(
            uuid=str(self.item1.uuid), foreign=str(self.foreign.uuid)
        )
        response = await grpc_stub.Create(request=request)

        self.assertEqual(response.foreign, str(self.foreign.uuid))
