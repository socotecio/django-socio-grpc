from django.test import TestCase, override_settings
from fakeapp.grpc.fakeapp_pb2 import UnitTestModelWithStructFilterListRequest
from fakeapp.grpc.fakeapp_pb2_grpc import (
    UnitTestModelWithStructFilterControllerStub,
    add_UnitTestModelWithStructFilterControllerServicer_to_server,
)
from fakeapp.models import UnitTestModel
from fakeapp.services.unit_test_model_with_struct_filter_service import (
    UnitTestModelWithStructFilterService,
)
from google.protobuf import struct_pb2

from django_socio_grpc.settings import FilterAndPaginationBehaviorOptions

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestOrderingRequestStruct(TestCase):
    def setUp(self):
        for idx in range(10):
            title = "z" * (idx + 1)
            text = chr(idx + ord("a")) + chr(idx + ord("b")) + chr(idx + ord("c"))
            UnitTestModel(title=title, text=text).save()

        # INFO - AM - 14/02/2024 - pagination in tested in django_socio_grpc/tests/test_pagination_request_struct.py
        # Reset it to None to avoid having to deal in pagination in this test
        self.old_pagination_class = UnitTestModelWithStructFilterService.pagination_class
        UnitTestModelWithStructFilterService.pagination_class = None

        UnitTestModel(title="zzzz", text=text).save()
        self.fake_grpc = FakeFullAIOGRPC(
            add_UnitTestModelWithStructFilterControllerServicer_to_server,
            UnitTestModelWithStructFilterService.as_servicer(),
        )

    def tearDown(self):
        UnitTestModelWithStructFilterService.pagination_class = self.old_pagination_class

    @override_settings(
        GRPC_FRAMEWORK={
            "GRPC_ASYNC": True,
            "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
        }
    )
    async def test_django_ordering_with_struct_request(self):
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithStructFilterControllerStub)
        filter_as_dict = {"ordering": "title"}
        filter_as_struct = struct_pb2.Struct()
        filter_as_struct.update(filter_as_dict)
        request = UnitTestModelWithStructFilterListRequest(_filters=filter_as_struct)
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 11)
        # responses_as_list[0] is type of django_socio_grpc.tests.grpc_test_utils.unittest_pb2.Test
        self.assertEqual(response.results[0].title, "z")
        self.assertEqual(response.results[1].title, "zz")
        self.assertEqual(response.results[2].title, "zzz")
        self.assertEqual(response.results[3].title, "zzzz")

        filtered_models = UnitTestModel.objects.all().order_by("-title")
        print((await filtered_models.afirst()).title)

        # Testing metadata filter not working
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithStructFilterControllerStub)
        filter_as_dict = {"ordering": "-title"}
        filter_as_struct = struct_pb2.Struct()
        filter_as_struct.update(filter_as_dict)
        request = UnitTestModelWithStructFilterListRequest(_filters=filter_as_struct)
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 11)
        # responses_as_list[0] is type of django_socio_grpc.tests.grpc_test_utils.unittest_pb2.Test
        self.assertEqual(response.results[0].title, "zzzzzzzzzz")
        self.assertEqual(response.results[1].title, "zzzzzzzzz")
        self.assertEqual(response.results[2].title, "zzzzzzzz")
        self.assertEqual(response.results[3].title, "zzzzzzz")

    @override_settings(
        GRPC_FRAMEWORK={
            "GRPC_ASYNC": True,
            "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
        }
    )
    async def test_django_ordering_array_with_struct_request(self):
        await UnitTestModel(title="z", text="fake").asave()
        await UnitTestModel(title="z", text="fake").asave()

        z_unit_models = UnitTestModel.objects.filter(title="z")
        # INFO - AM - Check that there is only 3 (one in setup and 2 in this method) To help maintainability if someone add an other and it break ordering
        self.assertEqual(await z_unit_models.acount(), 3)
        first_z_unit_model, second_z_unit_model, third_z_unit_model = [
            item async for item in z_unit_models
        ]

        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithStructFilterControllerStub)
        filter_as_dict = {"ordering": ["title", "-id"]}
        filter_as_struct = struct_pb2.Struct()
        filter_as_struct.update(filter_as_dict)
        request = UnitTestModelWithStructFilterListRequest(_filters=filter_as_struct)
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 13)
        # responses_as_list[0] is type of django_socio_grpc.tests.grpc_test_utils.unittest_pb2.Test
        self.assertEqual(response.results[0].title, "z")
        self.assertEqual(response.results[0].id, third_z_unit_model.id)
        self.assertEqual(response.results[1].title, "z")
        self.assertEqual(response.results[1].id, second_z_unit_model.id)
        self.assertEqual(response.results[2].title, "z")
        self.assertEqual(response.results[2].id, first_z_unit_model.id)
        self.assertEqual(response.results[3].title, "zz")
        self.assertEqual(response.results[4].title, "zzz")
        self.assertEqual(response.results[5].title, "zzzz")

        filtered_models = UnitTestModel.objects.all().order_by("-title")
        print((await filtered_models.afirst()).title)

        # Testing metadata filter not working
        grpc_stub = self.fake_grpc.get_fake_stub(UnitTestModelWithStructFilterControllerStub)
        filter_as_dict = {"ordering": ["-title", "id"]}
        filter_as_struct = struct_pb2.Struct()
        filter_as_struct.update(filter_as_dict)
        request = UnitTestModelWithStructFilterListRequest(_filters=filter_as_struct)
        response = await grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 13)
        # responses_as_list[0] is type of django_socio_grpc.tests.grpc_test_utils.unittest_pb2.Test
        self.assertEqual(response.results[0].title, "zzzzzzzzzz")
        self.assertEqual(response.results[1].title, "zzzzzzzzz")
        self.assertEqual(response.results[2].title, "zzzzzzzz")
        self.assertEqual(response.results[3].title, "zzzzzzz")
        self.assertEqual(response.results[10].title, "z")
        self.assertEqual(response.results[10].id, first_z_unit_model.id)
        self.assertEqual(response.results[11].title, "z")
        self.assertEqual(response.results[11].id, second_z_unit_model.id)
        self.assertEqual(response.results[12].title, "z")
        self.assertEqual(response.results[12].id, third_z_unit_model.id)
