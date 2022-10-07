from django.test import TestCase
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    StreamInControllerStub,
    add_StreamInControllerServicer_to_server,
)
from grpc import RpcError

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

    async def test_async_stream_in(self):

        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        stream_caller = grpc_stub.StreamIn()

        for name in ["a", "b", "c"]:
            request = fakeapp_pb2.StreamInStreamInRequest(name=name)
            await stream_caller._context.write(request)

        await stream_caller.done_writing()
        response = await stream_caller

        assert response.count == 3

    async def test_stream_raises_timeout_error(self):

        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        stream_caller = grpc_stub.StreamIn()

        for name in ["a", "b", "c"]:
            request = fakeapp_pb2.StreamInStreamInRequest(name=name)
            await stream_caller._context.write(request)

        with self.assertRaisesMessage(RpcError, "Context read timeout"):
            await stream_caller
