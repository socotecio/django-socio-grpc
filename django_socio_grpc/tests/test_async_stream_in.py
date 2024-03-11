import asyncio

import grpc
from django.test import TestCase, override_settings
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    StreamInControllerStub,
    add_StreamInControllerServicer_to_server,
)
from grpc import RpcError

from django_socio_grpc.tests.fakeapp.services.stream_in_service import StreamInService

from .grpc_test_utils.fake_grpc import FakeAsyncContext, FakeFullAIOGRPC


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

        def generate_requests():
            for name in ["a", "b", "c"]:
                yield fakeapp_pb2.StreamInStreamInRequest(name=name)
            yield grpc.aio.EOF

        response = await grpc_stub.StreamIn(generate_requests())

        assert response.count == 3

    async def test_async_stream_in_async_gen(self):
        queue = asyncio.Queue()

        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        async def generate_requests():
            message = None
            while message != grpc.aio.EOF:
                message = await queue.get()
                yield message

        await queue.put(fakeapp_pb2.StreamInStreamInRequest(name="a"))
        await queue.put(fakeapp_pb2.StreamInStreamInRequest(name="b"))
        await queue.put(fakeapp_pb2.StreamInStreamInRequest(name="c"))
        await queue.put(grpc.aio.EOF)

        response = await grpc_stub.StreamIn(generate_requests())

        assert response.count == 3

    async def test_stream_raises_timeout_error(self):
        # INFO - AM - 05/01/2024 - Speed up the timeout for this test
        old_timeout_count = FakeAsyncContext.timeout_count
        FakeAsyncContext.timeout_count = 10

        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        async def generate_requests():
            for name in ["a", "b", "c"]:
                yield fakeapp_pb2.StreamInStreamInRequest(name=name)

            await asyncio.sleep(3)
            yield fakeapp_pb2.StreamInStreamInRequest(name="too late")

        with self.assertRaisesMessage(RpcError, "TimeoutError"):
            await grpc_stub.StreamIn(generate_requests())

        FakeAsyncContext.timeout_count = old_timeout_count

    async def test_async_stream_stream(self):
        FakeAsyncContext.timeout_count = 20

        queue = asyncio.Queue()

        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        async def generate_requests():
            while True:
                message = await queue.get()
                if message == grpc.aio.EOF:
                    break
                yield message

        await queue.put(fakeapp_pb2.StreamInStreamInRequest(name="a"))

        counter = 1
        async for message in grpc_stub.StreamToStream(generate_requests()):
            if counter == 1:
                self.assertEqual(message.name, "aResponse")
                await queue.put(fakeapp_pb2.StreamInStreamInRequest(name="b"))
                # await asyncio.sleep(2)
                counter += 1
            elif counter == 2:
                self.assertEqual(message.name, "bResponse")
                await queue.put(fakeapp_pb2.StreamInStreamInRequest(name="c"))
                counter += 1
            elif counter == 3:
                self.assertEqual(message.name, "cResponse")
                await queue.put(grpc.aio.EOF)
                counter += 1

        self.assertEqual(counter, 4)
