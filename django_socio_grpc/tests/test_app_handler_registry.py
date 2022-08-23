from django.test import TestCase
from fakeapp.grpc.fakeapp_pb2 import UnitTestModelListRequest
from fakeapp.grpc.fakeapp_pb2_grpc import UnitTestModelControllerStub
from fakeapp.models import UnitTestModel

from django_socio_grpc.utils.registry_singleton import RegistrySingleton
from django_socio_grpc.utils.servicer_register import (
    AppHandlerRegistry,
    AppHandlerRegistryError,
)

from .grpc_test_utils.fake_grpc import FakeChannel, FakeGRPC, FakeServer


class TestAppHandlerRegistry(TestCase):
    def setUp(self):
        for idx in range(10):
            title = "z" * (idx + 1)
            text = chr(idx + ord("a")) + chr(idx + ord("b")) + chr(idx + ord("c"))
            UnitTestModel(title=title, text=text).save()
        pass

    def tearDown(self) -> None:
        RegistrySingleton().clean_all()

    def test_AppHandlerRegistry_old_way(self):

        ################
        #  Setup fake server but with the registry handler
        ################
        grpc_addr = FakeGRPC.get_grpc_addr()
        fake_server = FakeServer()

        fake_server.add_insecure_port(grpc_addr)
        fake_server.start()

        fake_channel = FakeChannel(fake_server)

        fakeapp_handler_registry = AppHandlerRegistry(app_name="fakeapp", server=fake_server)
        fakeapp_handler_registry.register("UnitTestModel")

        ###############
        # Test that the service is correctly registered
        ###############
        grpc_stub = UnitTestModelControllerStub(fake_channel)

        request = UnitTestModelListRequest()
        response = grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 10)

        ###############
        # stop fake server
        ###############
        fake_server.stop(grace=None)

    def test_AppHandlerRegistry(self):

        ################
        #  Setup fake server but with the registry handler
        ################
        grpc_addr = FakeGRPC.get_grpc_addr()
        fake_server = FakeServer()

        fake_server.add_insecure_port(grpc_addr)
        fake_server.start()

        fake_channel = FakeChannel(fake_server)

        fakeapp_handler_registry = AppHandlerRegistry(app_name="fakeapp", server=fake_server)
        fakeapp_handler_registry.register("UnitTestModelService")

        with self.assertRaises(AppHandlerRegistryError):
            AppHandlerRegistry(app_name="fakeapp", server=fake_server)

        ###############
        # Test that the service is correctly registered
        ###############
        grpc_stub = UnitTestModelControllerStub(fake_channel)

        request = UnitTestModelListRequest()
        response = grpc_stub.List(request=request)

        self.assertEqual(len(response.results), 10)

        ###############
        # stop fake server
        ###############
        fake_server.stop(grace=None)
