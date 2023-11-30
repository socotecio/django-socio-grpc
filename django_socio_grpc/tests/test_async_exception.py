import logging

import grpc
from django.test import TestCase, override_settings
from fakeapp.grpc.fakeapp_pb2_grpc import (
    ExceptionControllerStub,
    add_ExceptionControllerServicer_to_server,
)
from fakeapp.services.exception_service import ExceptionService
from google.protobuf import empty_pb2

from django_socio_grpc.log import set_log_record_factory

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestAsyncException(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_ExceptionControllerServicer_to_server, ExceptionService.as_servicer()
        )
        set_log_record_factory()

    def tearDown(self):
        self.fake_grpc.close()

    async def test_async_unary_exception(self):
        with self.assertLogs("django_socio_grpc", level=logging.INFO) as cm:
            grpc_stub = self.fake_grpc.get_fake_stub(ExceptionControllerStub)
            request = empty_pb2.Empty()
            with self.assertRaises(grpc.RpcError) as error:
                await grpc_stub.UnaryRaiseException(request=request)

            self.assertEqual(error.exception.code(), grpc.StatusCode.UNKNOWN)

            self.assertTrue("Exception" in str(error.exception))

            self.assertEqual(len(cm.records), 2)

            # INFO - AM - 24/04/2023 - Check the first one from the logrequest middleware
            self.assertEqual(cm.records[0].levelno, logging.INFO)
            self.assertEqual(cm.records[0].grpc_action, "UnaryRaiseException")
            self.assertEqual(cm.records[0].grpc_service_name, "Exception")
            self.assertEqual(
                cm.records[0].msg,
                "Receive action UnaryRaiseException on service ExceptionService",
            )

            # INFO - AM - 24/04/2023 - Check the second one that contain the exception
            self.assertEqual(cm.records[1].levelno, logging.ERROR)
            self.assertEqual(cm.records[1].grpc_action, "UnaryRaiseException")
            self.assertEqual(cm.records[1].grpc_service_name, "Exception")
            self.assertEqual(cm.records[1].msg, "Exception : Exception/UnaryRaiseException")
            self.assertIn("test", str(cm.records[1].exc_info))

    async def test_async_stream_exception(self):
        with self.assertLogs("django_socio_grpc", level=logging.INFO) as cm:
            grpc_stub = self.fake_grpc.get_fake_stub(ExceptionControllerStub)
            request = empty_pb2.Empty()

            response_list = []
            with self.assertRaises(grpc.RpcError) as error:
                async for response in grpc_stub.StreamRaiseException(request=request):
                    response_list.append(response)

            self.assertEqual(error.exception.code(), grpc.StatusCode.UNKNOWN)

            self.assertTrue("Exception" in str(error.exception))
            # INFO - AM - 01/02/2023 we verify that if exception in stream we still receive the firsts message sended in stream
            self.assertEqual(len(response_list), 1)

            # INFO - AM - 24/04/2023 - Check the first one from the logrequest middleware
            self.assertEqual(cm.records[0].levelno, logging.INFO)
            self.assertEqual(cm.records[0].grpc_action, "StreamRaiseException")
            self.assertEqual(cm.records[0].grpc_service_name, "Exception")
            self.assertEqual(
                cm.records[0].msg,
                "Receive action StreamRaiseException on service ExceptionService",
            )

            # INFO - AM - 24/04/2023 - Check the second one that contain the exception
            self.assertEqual(cm.records[1].levelno, logging.ERROR)
            self.assertEqual(cm.records[1].grpc_action, "StreamRaiseException")
            self.assertEqual(cm.records[1].grpc_service_name, "Exception")
            self.assertEqual(cm.records[1].msg, "Exception : Exception/StreamRaiseException")
            self.assertIn("test", str(cm.records[1].exc_info))

    async def test_async_apiexception(self):
        with self.assertLogs("django_socio_grpc", level=logging.INFO) as cm:
            grpc_stub = self.fake_grpc.get_fake_stub(ExceptionControllerStub)
            request = empty_pb2.Empty()

            with self.assertRaises(grpc.RpcError) as error:
                await grpc_stub.APIException(request=request)

            self.assertEqual(error.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)

            self.assertEqual(
                error.exception.details(), '{"test": {"message": "test", "code": "invalid"}}'
            )

            # INFO - AM - 24/04/2023 - Check the first one from the logrequest middleware
            self.assertEqual(cm.records[0].levelno, logging.INFO)
            self.assertEqual(cm.records[0].grpc_action, "APIException")
            self.assertEqual(cm.records[0].grpc_service_name, "Exception")
            self.assertEqual(
                cm.records[0].msg,
                "Receive action APIException on service ExceptionService",
            )

            # INFO - AM - 24/04/2023 - Check the second one that contain the exception
            self.assertEqual(cm.records[1].levelno, logging.WARNING)
            self.assertEqual(cm.records[1].grpc_action, "APIException")
            self.assertEqual(cm.records[1].grpc_service_name, "Exception")
            self.assertEqual(cm.records[1].msg, "ValidationError : Exception/APIException")
            self.assertIsNotNone(cm.records[1].exc_info)

    async def test_async_grpcexception(self):
        with self.assertLogs("django_socio_grpc", level=logging.INFO) as cm:
            grpc_stub = self.fake_grpc.get_fake_stub(ExceptionControllerStub)
            request = empty_pb2.Empty()

            with self.assertRaises(grpc.RpcError) as error:
                await grpc_stub.GRPCException(request=request)

            self.assertEqual(error.exception.code(), grpc.StatusCode.NOT_FOUND)

            self.assertEqual(
                error.exception.details(), '{"message": "Not found.", "code": "not_found"}'
            )

            # INFO - AM - 24/04/2023 - Check the first one from the logrequest middleware
            self.assertEqual(cm.records[0].levelno, logging.INFO)
            self.assertEqual(cm.records[0].grpc_action, "GRPCException")
            self.assertEqual(cm.records[0].grpc_service_name, "Exception")
            self.assertEqual(
                cm.records[0].msg,
                "Receive action GRPCException on service ExceptionService",
            )

            # INFO - AM - 24/04/2023 - Check the second one that contain the exception
            self.assertEqual(cm.records[1].levelno, logging.WARNING)
            self.assertEqual(cm.records[1].grpc_action, "GRPCException")
            self.assertEqual(cm.records[1].grpc_service_name, "Exception")
            self.assertEqual(cm.records[1].msg, "NotFound : Exception/GRPCException")
            self.assertIsNotNone(cm.records[1].exc_info)
