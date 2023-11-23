from django.test import TestCase, override_settings
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    StreamInControllerStub,
    add_StreamInControllerServicer_to_server,
)
from grpc import RpcError

from django_socio_grpc.tests.fakeapp.services.stream_in_service import StreamInService

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestAsyncStreamIn(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_StreamInControllerServicer_to_server, StreamInService.as_servicer()
        )

    def tearDown(self):
        self.fake_grpc.close()

    async def test_async_stream_in(self):
        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        stream_caller = grpc_stub.StreamIn()

        for name in ["a", "b", "c"]:
            request = fakeapp_pb2.StreamInStreamInRequest(name=name)
            await stream_caller.write(request)

        await stream_caller.done_writing()
        response = await stream_caller

        assert response.count == 3

    async def test_stream_raises_timeout_error(self):
        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        stream_caller = grpc_stub.StreamIn()

        for name in ["a", "b", "c"]:
            request = fakeapp_pb2.StreamInStreamInRequest(name=name)
            await stream_caller.write(request)

        with self.assertRaisesMessage(RpcError, "TimeoutError"):
            await stream_caller

    async def test_async_stream_stream(self):
        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        stream_caller = grpc_stub.StreamToStream()

        await stream_caller.write(fakeapp_pb2.StreamInStreamToStreamRequest(name="a"))
        await stream_caller.write(fakeapp_pb2.StreamInStreamToStreamRequest(name="b"))

        response1 = await stream_caller.read()

        self.assertEqual(response1.name, "aResponse")

        await stream_caller.write(fakeapp_pb2.StreamInStreamToStreamRequest(name="c"))

        response2 = await stream_caller.read()
        response3 = await stream_caller.read()

        self.assertEqual(response2.name, "bResponse")
        self.assertEqual(response3.name, "cResponse")

        await stream_caller.done_writing()
