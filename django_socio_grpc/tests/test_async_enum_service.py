from django.test import TestCase, override_settings
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    EnumControllerStub,
    add_EnumControllerServicer_to_server,
)
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

    async def test_async_enum_service_with_annotated_model(self):
        grpc_stub = self.fake_grpc.get_fake_stub(EnumControllerStub)
        request = fakeapp_pb2.EnumServiceRequest(
            char_choices=fakeapp_pb2.MyTestStrEnum.Enum.VALUE_1,
            int_choices=fakeapp_pb2.MyTestIntEnum.Enum.TWO,
        )
        response = await grpc_stub.BasicEnumRequestWithAnnotatedModel(request=request)
        self.assertEqual(response.char_choices, fakeapp_pb2.MyTestStrEnum.Enum.VALUE_1)
        self.assertEqual(response.int_choices, fakeapp_pb2.MyTestIntEnum.Enum.TWO)

    async def test_async_enum_service_with_annotated_serializer(self):
        grpc_stub = self.fake_grpc.get_fake_stub(EnumControllerStub)
        request = fakeapp_pb2.EnumServiceAnnotatedSerializerRequest(
            char_choices=fakeapp_pb2.MyTestStrEnum.Enum.VALUE_1
        )
        response = await grpc_stub.BasicEnumRequestWithAnnotatedSerializer(request=request)
        self.assertEqual(response.char_choices, fakeapp_pb2.MyTestStrEnum.Enum.VALUE_1)
