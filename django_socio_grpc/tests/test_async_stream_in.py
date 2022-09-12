from django.test import TestCase
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    StreamInControllerStub,
    add_StreamInControllerServicer_to_server,
)

from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.tests.fakeapp.services.stream_in_service import StreamInService

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


class TestAsyncStreamIn(TestCase):
    def setUp(self):
        grpc_settings.GRPC_ASYNC = True
        self.fake_grpc = FakeFullAIOGRPC(
            add_StreamInControllerServicer_to_server, StreamInService.as_servicer()
        )

    def tearDown(self):
        grpc_settings.GRPC_ASYNC = False
        self.fake_grpc.close()

    async def test_async_partial_update(self):

        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        stream_caller = grpc_stub.StreamIn()

        for name in ["a", "b", "c"]:
            request = fakeapp_pb2.StreamInStreamInRequest(name=name)
            await stream_caller.write(request)

        response = await stream_caller

        assert response.count == 3
