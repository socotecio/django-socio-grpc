import json

from django.conf import settings
from django.test import TestCase, override_settings
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    BasicControllerStub,
    StreamInControllerStub,
    add_BasicControllerServicer_to_server,
    add_StreamInControllerServicer_to_server,
)
from fakeapp.services.basic_service import BasicService
from google.protobuf import empty_pb2

from django_socio_grpc.tests.fakeapp.services.stream_in_service import StreamInService

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC

urlpatterns = []


@override_settings(
    GRPC_FRAMEWORK={
        "GRPC_MIDDLEWARE": [
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.middleware.locale.LocaleMiddleware",
        ],
        "GRPC_ASYNC": True,
    },
    INSTALLED_APPS=[
        "django.contrib.sessions",  # INFO - AM - 26/04/2023 - Only used to test legacy middleware
        *settings.INSTALLED_APPS,
    ],
    ROOT_URLCONF="django_socio_grpc.tests.test_legacy_django_middlewares",
)
class TestLegacyDjangoMiddleware(TestCase):
    """
    This
    """

    def tearDown(self):
        self.fake_grpc.close()

    async def test_middleware_not_crashing_with_generator(self):
        """
        JUST TESTING THAT SOME DJANGO MIDDLEWARE NOT MAKING THING CRASH IN GENERATOR.
        IF SOMEONE MAKE ISSUE ABOUT A MIDDLEWARE NOT WORKING PLEASE ADD IT IN THE override_settings OF THIS CLASS
        """
        self.fake_grpc = FakeFullAIOGRPC(
            add_StreamInControllerServicer_to_server, StreamInService.as_servicer()
        )

        grpc_stub = self.fake_grpc.get_fake_stub(StreamInControllerStub)

        stream_caller = grpc_stub.StreamToStream()
        await stream_caller.write(fakeapp_pb2.StreamInStreamToStreamRequest(name="a"))

        response1 = await stream_caller.read()

        self.assertEqual(response1.name, "aResponse")

        await stream_caller.done_writing()

    async def test_middleware_return(self):
        """
        JUST TESTING THAT SOME DJANGO MIDDLEWARE NOT MAKING THING CRASH IN SIMPLE CALL.
        IF SOMEONE MAKE ISSUE ABOUT A MIDDLEWARE NOT WORKING PLEASE ADD IT IN THE override_settings OF THIS CLASS
        """

        self.fake_grpc = FakeFullAIOGRPC(
            add_BasicControllerServicer_to_server, BasicService.as_servicer()
        )

        grpc_stub = self.fake_grpc.get_fake_stub(BasicControllerStub)

        request = fakeapp_pb2.BasicFetchDataForUserRequest(user_name="test")
        response = await grpc_stub.FetchDataForUser(request=request)

        self.assertEqual(response.user_name, "test")

    async def test_locale_middleware(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_BasicControllerServicer_to_server, BasicService.as_servicer()
        )

        grpc_stub = self.fake_grpc.get_fake_stub(BasicControllerStub)

        # TEST default english
        response = await grpc_stub.FetchTranslatedKey(request=empty_pb2.Empty())

        self.assertEqual(response.text, "Test translation en")

        # TEST accept language in header key -- simple
        french_accept_language = {"Accept-Language": "fr"}

        metadata = (("HEADERS", (json.dumps(french_accept_language))),)
        response = await grpc_stub.FetchTranslatedKey(
            request=empty_pb2.Empty(), metadata=metadata
        )

        self.assertEqual(response.text, "Test traduction français")

        # TEST accept language in header key -- complex
        french_accept_language = {"Accept-Language": "fr,en-US;q=0.9,en;q=0.8"}

        metadata = (("HEADERS", (json.dumps(french_accept_language))),)
        response = await grpc_stub.FetchTranslatedKey(
            request=empty_pb2.Empty(), metadata=metadata
        )

        self.assertEqual(response.text, "Test traduction français")

        # TEST accept language directly in metadata -- simple
        metadata = (("Accept-Language", "fr"),)
        response = await grpc_stub.FetchTranslatedKey(
            request=empty_pb2.Empty(), metadata=metadata
        )

        self.assertEqual(response.text, "Test traduction français")

        # TEST accept language directly in metadata in maj -- simple
        metadata = (("ACCEPT-LANGUAGE", "fr"),)
        response = await grpc_stub.FetchTranslatedKey(
            request=empty_pb2.Empty(), metadata=metadata
        )

        self.assertEqual(response.text, "Test traduction français")
