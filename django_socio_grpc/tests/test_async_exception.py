import json

import mock
from django.test import TestCase, override_settings
from fakeapp.grpc.fakeapp_pb2_grpc import (
    ExceptionControllerStub,
    add_ExceptionControllerServicer_to_server,
)
from fakeapp.services.exception_service import ExceptionService
from google.protobuf import empty_pb2
from grpc import RpcError

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestAsyncException(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_ExceptionControllerServicer_to_server, ExceptionService.as_servicer()
        )

    def tearDown(self):
        self.fake_grpc.close()

    @mock.patch("django_socio_grpc.log.GRPCHandler.emit")
    async def test_async_unary_exception(self, mock_emit):
        mock_emit.return_value = mock.MagicMock()
        grpc_stub = self.fake_grpc.get_fake_stub(ExceptionControllerStub)
        request = empty_pb2.Empty()
        with self.assertRaises(RpcError) as error:
            await grpc_stub.UnaryRaiseException(request=request)

        self.assertTrue("test" in str(error.exception))
        mock_emit.assert_called()
        args = mock_emit.call_args
        self.assertEqual(json.loads(args[0][0].locals)["test_export_local"], "'var'")

    @mock.patch("django_socio_grpc.log.GRPCHandler.emit")
    async def test_async_stream_exception(self, mock_emit):
        mock_emit.return_value = mock.MagicMock()
        grpc_stub = self.fake_grpc.get_fake_stub(ExceptionControllerStub)
        request = empty_pb2.Empty()

        response_list = []
        with self.assertRaises(RpcError) as error:
            async for response in grpc_stub.StreamRaiseException(request=request):
                response_list.append(response)

        self.assertTrue("test" in str(error.exception))
        # INFO - AM - 01/02/2023 we verify that if exception in stream we still receive the firsts message sended in stream
        self.assertEqual(len(response_list), 1)
        mock_emit.assert_called()
        args = mock_emit.call_args
        self.assertEqual(json.loads(args[0][0].locals)["test_export_local"], "'var'")
