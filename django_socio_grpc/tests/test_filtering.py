import json

from django.test import TestCase
from fakeapp.grpc.fakeapp_pb2 import UnitTestModelListRequest
from fakeapp.grpc.fakeapp_pb2_grpc import (
    UnitTestModelControllerStub,
    add_UnitTestModelControllerServicer_to_server,
)
from fakeapp.models import UnitTestModel
from fakeapp.services.unit_test_model_service import UnitTestModelService

from .grpc_test_utils.fake_grpc import FakeGRPC


class TestFiltering(TestCase):
    def setUp(self):
        for idx in range(10):
            title = "z" * (idx + 1)
            text = chr(idx + ord("a")) + chr(idx + ord("b")) + chr(idx + ord("c"))
            UnitTestModel(title=title, text=text).save()
        self.fake_grpc = FakeGRPC(
            add_UnitTestModelControllerServicer_to_server, UnitTestModelService.as_servicer()
        )

    def tearDown(self):
        self.fake_grpc.close()

    def test_django_filter(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelControllerStub)
        request = UnitTestModelListRequest()
        filter_as_dict = {"title": "zzzzzzz"}
        metadata = (("FILTERS", (json.dumps(filter_as_dict))),)
        response = grpc_stub.List(request=request, metadata=metadata)

        self.assertEqual(len(response.results), 1)
        # responses_as_list[0] is type of django_socio_grpc.tests.grpc_test_utils.unittest_pb2.Test
        self.assertEqual(response.results[0].title, "zzzzzzz")
