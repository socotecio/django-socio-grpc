from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils.decorators import async_only_middleware
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    BasicControllerStub,
    add_BasicControllerServicer_to_server,
)
from fakeapp.services.basic_service import BasicService
from google.protobuf import json_format
from rest_framework.permissions import IsAuthenticated

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


class BasicServiceWithAuth(BasicService):
    permission_classes = (IsAuthenticated,)

    def resolve_user(self):
        user = User(email="john.doe@johndoe.com")
        return (user, {})


@async_only_middleware
def auth_without_session_middleware(get_response):
    async def middleware(request):
        assert request.context.user.email == "john.doe@johndoe.com"
        return await get_response(request)

    return middleware


@override_settings(
    GRPC_FRAMEWORK={
        "GRPC_MIDDLEWARE": [
            "django_socio_grpc.middlewares.auth_without_session_middleware",
            "django_socio_grpc.tests.test_auth_without_session_middleware.auth_without_session_middleware",
        ],
        "GRPC_ASYNC": True,
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework.authentication.BasicAuthentication"
        ],
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    },
)
class TestAuthWithoutSessionMiddleware(TestCase):
    def tearDown(self):
        self.fake_grpc.close()

    async def test_user_set_in_next_middleware_and_service(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_BasicControllerServicer_to_server, BasicServiceWithAuth.as_servicer()
        )

        grpc_stub = self.fake_grpc.get_fake_stub(BasicControllerStub)
        request = fakeapp_pb2.BasicFetchDataForUserRequest(user_name="test")
        response = await grpc_stub.FetchDataForUser(request=request)

        user_data_dict = json_format.MessageToDict(response.user_data)

        self.assertEqual(user_data_dict["email"], "john.doe@johndoe.com")
