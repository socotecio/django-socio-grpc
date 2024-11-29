from django.test import TestCase, override_settings
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    EnumControllerStub,
    add_EnumControllerServicer_to_server,
)
from fakeapp.models import EnumModel
from fakeapp.services.enum_service import EnumService

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestAsyncEnumService(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_EnumControllerServicer_to_server, EnumService.as_servicer()
        )

    def tearDown(self):
        self.fake_grpc.close()

    async def test_async_enum_service(self):
        grpc_stub = self.fake_grpc.get_fake_stub(EnumControllerStub)
        request = fakeapp_pb2.EnumServiceRequest(
            char_choices=fakeapp_pb2.MyTestStrEnum.Enum.VALUE_1,
            int_choices=fakeapp_pb2.MyTestIntEnum.Enum.TWO,
            char_choices_not_annotated="VALUE_2",
        )
        response = await grpc_stub.BasicEnumRequestWithAnnotatedModel(request=request)
        self.assertEqual(response.char_choices, fakeapp_pb2.MyTestStrEnum.Enum.VALUE_1)
        self.assertEqual(response.int_choices, fakeapp_pb2.MyTestIntEnum.Enum.TWO)
        self.assertEqual(
            response.char_choices_not_annotated,
            "VALUE_2",
        )

    async def test_async_enum_service_with_annotated_serializer(self):
        grpc_stub = self.fake_grpc.get_fake_stub(EnumControllerStub)
        request = fakeapp_pb2.EnumServiceAnnotatedSerializerRequest(
            char_choices_in_serializer=fakeapp_pb2.MyTestStrEnum.Enum.VALUE_1
        )
        response = await grpc_stub.BasicEnumRequestWithAnnotatedSerializer(request=request)
        self.assertEqual(
            response.char_choices_in_serializer, fakeapp_pb2.MyTestStrEnum.Enum.VALUE_1
        )

    async def test_async_enum_service_field_dict_simple_enum(self):
        grpc_stub = self.fake_grpc.get_fake_stub(EnumControllerStub)
        request = fakeapp_pb2.EnumBasicEnumRequest(
            enum=fakeapp_pb2.EnumBasicEnumRequest.MyGRPCActionEnum.Enum.VALUE_2
        )
        response = await grpc_stub.BasicEnumRequest(request=request)
        self.assertEqual(response.enum, fakeapp_pb2.MyTestStrEnum.Enum.VALUE_2)

    async def test_async_enum_service_model_creation_and_fetch(self):
        grpc_stub = self.fake_grpc.get_fake_stub(EnumControllerStub)
        request = fakeapp_pb2.EnumServiceRequest(
            char_choices=fakeapp_pb2.MyTestStrEnum.Enum.VALUE_2,
            int_choices=fakeapp_pb2.MyTestIntEnum.Enum.ONE,
            char_choices_not_annotated="VALUE_2",
        )
        response = await grpc_stub.Create(request=request)
        self.assertEqual(response.char_choices, fakeapp_pb2.MyTestStrEnum.Enum.VALUE_2)
        self.assertEqual(response.int_choices, fakeapp_pb2.MyTestIntEnum.Enum.ONE)
        self.assertEqual(
            response.char_choices_not_annotated,
            "VALUE_2",
        )
        self.assertEqual(await EnumModel.objects.acount(), 1)

        instance = await EnumModel.objects.afirst()
        self.assertEqual(instance.char_choices, "VALUE_2")
        self.assertEqual(instance.int_choices, 1)
        self.assertEqual(instance.char_choices_not_annotated, "VALUE_2")

        request = fakeapp_pb2.EnumServiceRetrieveRequest(id=response.id)
        response = await grpc_stub.Retrieve(request=request)
        self.assertEqual(response.char_choices, fakeapp_pb2.MyTestStrEnum.Enum.VALUE_2)
        self.assertEqual(response.int_choices, fakeapp_pb2.MyTestIntEnum.Enum.ONE)
        self.assertEqual(
            response.char_choices_not_annotated,
            "VALUE_2",
        )