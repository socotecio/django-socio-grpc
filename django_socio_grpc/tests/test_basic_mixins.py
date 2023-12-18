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
class TestBasicMixin(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_BasicControllerServicer_to_server, BasicService.as_servicer()
        )

    def tearDown(self):
        self.fake_grpc.close()

    async def test_async_fetch_data_for_user(self):
        grpc_stub = self.fake_grpc.get_fake_stub(BasicControllerStub)
        request = fakeapp_pb2.BasicFetchDataForUserRequest(user_name="test")
        response = await grpc_stub.FetchDataForUser(request=request)

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

    async def test_basic_service_attr_name_on_inheritance(self):
        grpc_stub = self.fake_grpc.get_fake_stub(BasicControllerStub)
        bob = fakeapp_pb2.BasicProtoListChildResponse(title="Bob", text="Is Cool")
        alice = fakeapp_pb2.BasicProtoListChildResponse(title="Alice", text="Is Nice")
        request = fakeapp_pb2.BasicProtoListChildListResponse()
        request.results.append(bob)
        request.results.append(alice)
        response = await grpc_stub.BasicList(request)
        self.assertEqual(len(response.results), 2)
