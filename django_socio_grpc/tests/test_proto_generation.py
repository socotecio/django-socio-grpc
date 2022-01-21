import os
from unittest.mock import mock_open, patch

import mock
from django.core.management import call_command
from django.test import TestCase

from django.test import override_settings
from importlib import reload

from .assets.generated_protobuf_files import (
    ALL_APP_GENERATED,
    CUSTOM_APP_MODEL_GENERATED,
    MODEL_WITH_M2M_GENERATED,
    MODEL_WITH_STRUCT_IMORT_IN_ARRAY,
    SIMPLE_APP_MODEL_GENERATED_FROM_OLD_ORDER,
    SIMPLE_APP_MODEL_OLD_ORDER,
    SIMPLE_MODEL_GENERATED
)
from django_socio_grpc.utils.servicer_register import AppHandlerRegistry, RegistrySingleton
import fakeapp.services.unittestmodel_service as unitestmodel_service
import fakeapp.services.syncunittestmodel_service as syncunitestmodel_service

def relatedfieldmodel_handler_hook(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("RelatedFieldModel")

def unittestmodel_handler_hook(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("UnitTestModel")

def foreignmodel_handler_hook(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("ForeignModel")

def importstructeveninarraymodel_handler_hook(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("ImportStructEvenInArrayModel")

def overide_grpc_framework(name_of_function):
    return {
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "ROOT_HANDLERS_HOOK": f"django_socio_grpc.tests.test_proto_generation.{name_of_function}",
    }



@patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "myproject.settings"})
class TestProtoGeneration(TestCase):

    def setUp(self):
        # INFO - AM - 14/01/2022 - This is necessary as RegistrySingleton is a singleton and each test reload django settings
        # Tryed with reload to do the same as for decorator but without success. Maybe just not reloading the good module. It is not a priority as this work as expected and only for tests
        RegistrySingleton.clean_all()

        return super().setUp()

    # @mock.patch(
    #     "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
    #     mock.MagicMock(return_value=False),
    # )
    # def test_check_option(self):
    #     self.maxDiff = None
    #     args = []
    #     opts = {"generate_python": False, "check": True}
    #     with patch("builtins.open", mock_open(read_data=ALL_APP_GENERATED)) as m:
    #         call_command("generateproto", *args, **opts)

    #     # this is done to avoid error on different absolute path
    #     assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
    #     assert m.mock_calls[0].args[1] == "r+"

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("relatedfieldmodel_handler_hook"))
    def test_generate_message_with_repeated_for_m2m(self):
        self.maxDiff = None

        args = []
        opts = {"generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, MODEL_WITH_M2M_GENERATED)


    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("unittestmodel_handler_hook"))
    def test_generate_one_app_one_model(self):
        reload(unitestmodel_service)
        self.maxDiff = None
        args = []
        opts = {"generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, SIMPLE_MODEL_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("foreignmodel_handler_hook"))
    def test_generate_one_app_one_model_customized(self):
        self.maxDiff = None
        args = []
        opts = {"generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, CUSTOM_APP_MODEL_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("importstructeveninarraymodel_handler_hook"))
    def test_generate_one_app_one_model_import_struct_in_array(self):
        self.maxDiff = None
        args = []
        opts = {"generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, MODEL_WITH_STRUCT_IMORT_IN_ARRAY)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=True),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("unittestmodel_handler_hook"))
    def test_order_proto_field_if_existing(self):
        """
        This test make the like the old unittestmodel have only id and title field.
        So when regeneration with the text field it should appear in third position and not in second
        """
        self.maxDiff = None
        args = []
        opts = {"generate_python": False}
        with patch("builtins.open", mock_open(read_data=SIMPLE_APP_MODEL_OLD_ORDER)) as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "r"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, SIMPLE_APP_MODEL_GENERATED_FROM_OLD_ORDER)


    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_all_models(self):
        reload(unitestmodel_service)
        reload(syncunitestmodel_service)
        self.maxDiff = None

        args = []
        opts = {"generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, ALL_APP_GENERATED)
