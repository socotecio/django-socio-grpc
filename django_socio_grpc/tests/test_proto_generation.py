import os
import sys
from importlib import reload
from unittest import mock
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from django_socio_grpc.exceptions import ProtobufGenerationException
from django_socio_grpc.tests.fakeapp.utils import make_reloaded_grpc_handler
from django_socio_grpc.tests.utils import patch_open
from django_socio_grpc.utils.registry_singleton import RegistrySingleton
from django_socio_grpc.utils.servicer_register import AppHandlerRegistry

from .assets.generated_protobuf_files import (
    ALL_APP_GENERATED_NO_SEPARATE,
    ALL_APP_GENERATED_SEPARATE,
    CUSTOM_APP_MODEL_GENERATED,
    MODEL_WITH_KNOWN_METHOD_OVERRIDEN_GENERATED,
    MODEL_WITH_M2M_GENERATED,
    MODEL_WITH_STRUCT_IMORT_IN_ARRAY,
    NO_MODEL_GENERATED,
    SIMPLE_APP_MODEL_GENERATED_FROM_OLD_ORDER,
    SIMPLE_APP_MODEL_OLD_ORDER,
    SIMPLE_MODEL_GENERATED,
)


def relatedfieldmodel_handler_hook(server):
    from fakeapp.services.related_field_model_service import RelatedFieldModelService

    return make_reloaded_grpc_handler("fakeapp", RelatedFieldModelService)(server)


def unittestmodel_handler_hook(server):
    from fakeapp.services.unit_test_model_service import UnitTestModelService

    return make_reloaded_grpc_handler("fakeapp", UnitTestModelService)(server)


def specialfieldmodel_handler_hook(server):
    from fakeapp.services.special_fields_model_service import SpecialFieldsModelService

    return make_reloaded_grpc_handler("fakeapp", SpecialFieldsModelService)(server)


def foreignmodel_handler_hook(server):
    from fakeapp.services.foreign_model_service import ForeignModelService

    return make_reloaded_grpc_handler("fakeapp", ForeignModelService)(server)


def importstructeveninarraymodel_handler_hook(server):
    from fakeapp.services.import_struct_even_in_array_model_service import (
        ImportStructEvenInArrayModelService,
    )

    return make_reloaded_grpc_handler("fakeapp", ImportStructEvenInArrayModelService)(server)


def basicservice_handler_hook(server):
    from fakeapp.services.basic_service import BasicService

    return make_reloaded_grpc_handler("fakeapp", BasicService)(server)


def reloaded_grpc_handler_hook(server):
    from fakeapp.handlers import services

    return make_reloaded_grpc_handler("fakeapp", *services)(server)


def service_in_root_grpc_handler_hook(server):
    from fakeapp.services.basic_service import BasicService

    app_registry = AppHandlerRegistry("myapp", server, reload_services=True, to_root_grpc=True)
    app_registry.register(BasicService)


def empty_handler_hook(server):
    RegistrySingleton().clean_all()
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
        "ROOT_HANDLERS_HOOK": "django_socio_grpc.tests.test_proto_generation.reloaded_grpc_handler_hook",
        "SEPARATE_READ_WRITE_MODEL": False,
    }


def overide_grpc_framework_in_root_grpc():
    return {
        "ROOT_HANDLERS_HOOK": "django_socio_grpc.tests.test_proto_generation.service_in_root_grpc_handler_hook",
    }


def reload_all():
    RegistrySingleton().clean_all()
    from fakeapp.handlers import services

    for service in services:
        reload(sys.modules[service.__module__])


@patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "myproject.settings"})
class TestProtoGeneration(TestCase):
    maxDiff = None

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_check_option(self):

        reload_all()

        args = []
        opts = {"check": True, "generate_python": False}
        with patch_open(read_data=ALL_APP_GENERATED_SEPARATE) as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
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

        args = []
        opts = {"generate_python": False}
        with patch_open() as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
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
        args = []
        opts = {"generate_python": False}
        with patch_open() as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
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
        args = []
        opts = {"generate_python": False}
        with patch_open() as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, MODEL_WITH_KNOWN_METHOD_OVERRIDEN_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("foreignmodel_handler_hook"))
    def test_generate_one_app_one_model_customized(self):
        args = []
        opts = {"generate_python": False}
        with patch_open() as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
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
        args = []
        opts = {"generate_python": False}
        with patch_open() as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
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
        args = []
        opts = {"generate_python": False}
        with patch_open(read_data=SIMPLE_APP_MODEL_OLD_ORDER) as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
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

        args = []
        opts = {"generate_python": False}
        with patch_open() as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, NO_MODEL_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_all_models_separate_read_write(self):
        reload_all()

        args = []
        opts = {"generate_python": False}
        with patch_open() as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
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

        args = []
        opts = {"generate_python": False}
        with patch_open() as m:
            call_command("generateproto", *args, **opts)

        # this is done to avoid error on different absolute path
        assert str(m.mock_calls[0].args[0]).endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, ALL_APP_GENERATED_NO_SEPARATE)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework_in_root_grpc())
    def test_generate_proto_to_root_grpc(self):

        args = []
        opts = {"generate_python": False}
        with patch_open() as m:
            call_command("generateproto", *args, **opts)

        assert str(m.mock_calls[0].args[0]).endswith("grpc_folder/myapp/myapp.proto")
        assert m.mock_calls[0].args[1] == "w+"
