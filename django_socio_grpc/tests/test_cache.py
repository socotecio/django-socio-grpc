from django.test import TestCase, override_settings
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    BasicControllerStub,
    add_BasicControllerServicer_to_server,
)
from fakeapp.services.basic_service import BasicService
from google.protobuf import json_format

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestCache(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_BasicControllerServicer_to_server, BasicService.as_servicer()
        )

    def tearDown(self):
        self.fake_grpc.close()

    async def test_cache_on_grpc_action(self):
        grpc_stub = self.fake_grpc.get_fake_stub(BasicControllerStub)
        request = fakeapp_pb2.BasicTestCachedAnswerRequest(cache_test="test")
        response = await grpc_stub.TestCachedAnswer(request=request)

        self.assertEqual(response.user_name, "test")
        user_data_dict = json_format.MessageToDict(response.user_data)
        self.assertEqual(
            user_data_dict,
            {
                "email": "fake_email@email.com",
                "birth_date": "25/01/1996",
                "slogan": "Do it better",
            },
        )

        assert False
