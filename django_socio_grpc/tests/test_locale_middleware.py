import json

from django.test import TestCase, override_settings
from fakeapp.grpc.fakeapp_pb2_grpc import (
    BasicControllerStub,
    add_BasicControllerServicer_to_server,
)
from fakeapp.services.basic_service import BasicService
from google.protobuf import empty_pb2

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(
    GRPC_FRAMEWORK={
        "GRPC_MIDDLEWARE": ["django_socio_grpc.middlewares.locale_middleware"],
        "GRPC_ASYNC": True,
    }
)
class TestLocaleMiddleware(TestCase):
    def tearDown(self):
        self.fake_grpc.close()

    async def test_middleware_called_with_generator(self):
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
