import os
from importlib import reload
from unittest.mock import mock_open, patch

import fakeapp.services.basic_service as basic_service
import fakeapp.services.special_fields_model_service as special_fields_model_service
import fakeapp.services.sync_unit_test_model_service as syncunitestmodel_service
import fakeapp.services.unit_test_model_service as unitestmodel_service
import mock
from django.core.management import call_command
from django.test import TestCase, override_settings

from django_socio_grpc.exceptions import ProtobufGenerationException
from django_socio_grpc.utils.registry_singleton import RegistrySingleton
from django_socio_grpc.utils.servicer_register import AppHandlerRegistry

from .assets.generated_protobuf_files import (
    ALL_APP_GENERATED_NO_SEPARATE,
    ALL_APP_GENERATED_SEPARATE,
    CUSTOM_APP_MODEL_GENERATED,
    MODEL_WITH_KNOWN_METHOD_OVERRIDED_GENERATED,
    MODEL_WITH_M2M_GENERATED,
    MODEL_WITH_STRUCT_IMORT_IN_ARRAY,
    NO_MODEL_GENERATED,
    SIMPLE_APP_MODEL_GENERATED_FROM_OLD_ORDER,
    SIMPLE_APP_MODEL_OLD_ORDER,
    SIMPLE_MODEL_GENERATED,
)


def relatedfieldmodel_handler_hook(server):
    from fakeapp.services.related_field_model_service import RelatedFieldModelService

    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register(RelatedFieldModelService)


def unittestmodel_handler_hook(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("UnitTestModelService")


def specialfieldmodel_handler_hook(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("SpecialFieldsModelService")


def foreignmodel_handler_hook(server):
    from fakeapp.services.foreign_model_service import ForeignModelService

    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register(ForeignModelService)


def importstructeveninarraymodel_handler_hook(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("ImportStructEvenInArrayModelService")


def basicservice_handler_hook(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("BasicService")


def empty_handler_hook(server):
    pass


def error_app_unkown_handler_hook(server):
    app_registry = AppHandlerRegistry("notexisting", server)
    app_registry.register("UnknowService")


def error_service_unkown_handler_hook(server):
    app_registry = AppHandlerRegistry("fakeapp", server)
    app_registry.register("UnknowService")


def overide_grpc_framework(name_of_function):
    return {
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "ROOT_HANDLERS_HOOK": f"django_socio_grpc.tests.test_proto_generation.{name_of_function}",
    }


def overide_grpc_framework_no_separate():
    return {
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "ROOT_HANDLERS_HOOK": "fakeapp.handlers.grpc_handlers",
        "SEPARATE_READ_WRITE_MODEL": False,
    }


@patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "myproject.settings"})
class TestProtoGeneration(TestCase):
    def setUp(self):
        # INFO - AM - 14/01/2022 - This is necessary as RegistrySingleton is a singleton and each test reload django settings
        # Tryed with reload to do the same as for decorator but without success. Maybe just not reloading the good module. It is not a priority as this work as expected and only for tests
        RegistrySingleton.clean_all()

        return super().setUp()

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_check_option(self):
        reload(unitestmodel_service)
        reload(syncunitestmodel_service)
        reload(special_fields_model_service)
        reload(basic_service)
        self.maxDiff = None
        args = []
        opts = {"check": True, "generate_python": False}
        with patch("builtins.open", mock_open(read_data=ALL_APP_GENERATED_SEPARATE)) as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "r"

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("empty_handler_hook"))
    def test_raise_when_no_service_registered(self):
        args = []
        opts = {"generate_python": False}
        with self.assertRaises(ProtobufGenerationException) as fake_generation_error:
            call_command("generateproto", *args, **opts)

        self.assertEqual(
            str(fake_generation_error.exception),
            "Error on protobuf generation on model None on app None: No Service registered. You should use ROOT_HANDLERS_HOOK settings and register Service using AppHandlerRegistry.",
        )

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("error_app_unkown_handler_hook"))
    def test_raise_when_app_not_exising(self):
        args = []
        opts = {"generate_python": False}
        with self.assertRaises(ModuleNotFoundError) as fake_generation_error:
            call_command("generateproto", *args, **opts)

        self.assertEqual(
            str(fake_generation_error.exception),
            "No module named 'notexisting'",
        )

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(
        GRPC_FRAMEWORK=overide_grpc_framework("error_service_unkown_handler_hook")
    )
    def test_raise_when_service_not_existing(self):
        args = []
        opts = {"generate_python": False}
        with self.assertRaises(ModuleNotFoundError) as fake_generation_error:
            call_command("generateproto", *args, **opts)

        self.assertEqual(
            str(fake_generation_error.exception),
            "No module named 'fakeapp.services.unknow_service_service'",
        )

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
    def test_generate_one_app_one_model_with_custom_action(self):
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
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("specialfieldmodel_handler_hook"))
    def test_generate_one_app_one_model_with_override_know_method(self):
        reload(special_fields_model_service)
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
        self.assertEqual(called_with_data, MODEL_WITH_KNOWN_METHOD_OVERRIDED_GENERATED)

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
    @override_settings(
        GRPC_FRAMEWORK=overide_grpc_framework("importstructeveninarraymodel_handler_hook")
    )
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
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("basicservice_handler_hook"))
    def test_generate_service_no_model(self):
        reload(basic_service)
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
        self.assertEqual(called_with_data, NO_MODEL_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_all_models_separate_read_write(self):
        reload(unitestmodel_service)
        reload(syncunitestmodel_service)
        reload(special_fields_model_service)
        reload(basic_service)
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
        self.assertEqual(called_with_data, ALL_APP_GENERATED_SEPARATE)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework_no_separate())
    def test_generate_all_models_no_separate(self):
        reload(unitestmodel_service)
        reload(syncunitestmodel_service)
        reload(special_fields_model_service)
        reload(basic_service)
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
        self.assertEqual(called_with_data, ALL_APP_GENERATED_NO_SEPARATE)
