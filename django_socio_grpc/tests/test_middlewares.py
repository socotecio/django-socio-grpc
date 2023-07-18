from unittest import mock

from django.test import TestCase, override_settings
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    BasicControllerStub,
    StreamInControllerStub,
    add_BasicControllerServicer_to_server,
    add_StreamInControllerServicer_to_server,
)
from fakeapp.services.basic_service import BasicService

from django_socio_grpc.tests.fakeapp.services.stream_in_service import StreamInService
from django_socio_grpc.utils.utils import safe_async_response

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC

FakeMiddleware = mock.MagicMock()
FakeMiddleware.async_capable = True


def _middleware_factory(get_response):
    FakeMiddleware.inner_fn.reset_mock()

    async def middleware(request):
        return await safe_async_response(get_response, request)

    FakeMiddleware.inner_fn.side_effect = middleware

    return FakeMiddleware.inner_fn


FakeMiddleware.side_effect = _middleware_factory


@override_settings(
    GRPC_FRAMEWORK={
        "GRPC_MIDDLEWARE": ["django_socio_grpc.tests.test_middlewares.FakeMiddleware"],
        "GRPC_ASYNC": True,
    }
)
class TestMiddleware(TestCase):
    def setUp(self):
        FakeMiddleware.reset_mock()

    def tearDown(self):
        self.fake_grpc.close()

    async def test_middleware_called_with_generator(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_StreamInControllerServicer_to_server, StreamInService.as_servicer()
        )
        FakeMiddleware.assert_called_once()
        FakeMiddleware.inner_fn.assert_not_called()

        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        stream_caller = grpc_stub.StreamToStream()
        await stream_caller.write(fakeapp_pb2.StreamInStreamToStreamRequest(name="a"))

        response1 = await stream_caller.read()

        self.assertEqual(response1.name, "aResponse")

        await stream_caller.done_writing()
        FakeMiddleware.inner_fn.assert_called_once()

    async def test_middleware_called_return(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_BasicControllerServicer_to_server, BasicService.as_servicer()
        )
        FakeMiddleware.assert_called_once()
        FakeMiddleware.inner_fn.assert_not_called()

        grpc_stub = self.fake_grpc.get_fake_stub(BasicControllerStub)

        request = fakeapp_pb2.BasicFetchDataForUserRequest(user_name="test")
        response = await grpc_stub.FetchDataForUser(request=request)

        self.assertEqual(response.user_name, "test")

        FakeMiddleware.inner_fn.assert_called_once()
