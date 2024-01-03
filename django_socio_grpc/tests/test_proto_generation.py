import os
import sys
from importlib import reload
from pathlib import Path
from unittest import mock
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from django_socio_grpc.exceptions import ProtobufGenerationException
from django_socio_grpc.protobuf import RegistrySingleton
from django_socio_grpc.protobuf.protoparser import protoparser
from django_socio_grpc.services import AppHandlerRegistry
from django_socio_grpc.tests.fakeapp.utils import make_reloaded_grpc_handler
from django_socio_grpc.tests.utils import patch_open


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


def recursive_handler_hook(server):
    from fakeapp.services.recursive_test_model_service import RecursiveTestModelService

    return make_reloaded_grpc_handler("fakeapp", RecursiveTestModelService)(server)


def service_in_root_grpc_handler_hook(server):
    from fakeapp.services.basic_service import BasicService

    app_registry = AppHandlerRegistry("myapp", server, reload_services=True, to_root_grpc=True)
    app_registry.register(BasicService)


def empty_handler_hook(server):
    RegistrySingleton.clean_all()


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


OVERRIDEN_SETTINGS = {
    "ALL_APP_GENERATED_NO_SEPARATE": overide_grpc_framework_no_separate(),
    "ALL_APP_GENERATED_SEPARATE": {},
    "CUSTOM_APP_MODEL_GENERATED": overide_grpc_framework("foreignmodel_handler_hook"),
    "MODEL_WITH_KNOWN_METHOD_OVERRIDEN_GENERATED": overide_grpc_framework(
        "specialfieldmodel_handler_hook"
    ),
    "MODEL_WITH_M2M_GENERATED": overide_grpc_framework("relatedfieldmodel_handler_hook"),
    "MODEL_WITH_STRUCT_IMORT_IN_ARRAY": overide_grpc_framework(
        "importstructeveninarraymodel_handler_hook"
    ),
    "NO_MODEL_GENERATED": overide_grpc_framework("basicservice_handler_hook"),
    "SIMPLE_MODEL_GENERATED": overide_grpc_framework("unittestmodel_handler_hook"),
    "RECURSIVE_MODEL_GENERATED": overide_grpc_framework("recursive_handler_hook"),
}


def get_proto_file_content(name):
    with open(Path(__file__).parent / "protos" / name / "fakeapp.proto") as f:
        return f.read()


def reload_all():
    RegistrySingleton.clean_all()
    from fakeapp.handlers import services

    for service in services:
        reload(sys.modules[service.__module__])


old_order_data = get_proto_file_content("SIMPLE_APP_MODEL_OLD_ORDER")


@patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "myproject.settings"})
class TestProtoGeneration(TestCase):
    maxDiff = None

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    def test_check_option(self):
        reload_all()

        args = []
        opts = {"check": True, "no_generate_pb2": True}

        input_data = get_proto_file_content("ALL_APP_GENERATED_SEPARATE")

        with patch_open(read_data=input_data) as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].kwargs["mode"] == "r"

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("empty_handler_hook"))
    def test_raise_when_no_service_registered(self):
        args = []
        opts = {"no_generate_pb2": True}
        with self.assertRaises(ProtobufGenerationException) as fake_generation_error:
            call_command("generateproto", *args, **opts)

        self.assertEqual(
            str(fake_generation_error.exception),
            "Error on protobuf generation on model None on app None: No Service registered. You should use ROOT_HANDLERS_HOOK settings and register Service using AppHandlerRegistry.",
        )

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("error_app_unkown_handler_hook"))
    def test_raise_when_app_not_exising(self):
        args = []
        opts = {"no_generate_pb2": True}
        with self.assertRaises(ModuleNotFoundError) as fake_generation_error:
            call_command("generateproto", *args, **opts)

        self.assertEqual(
            str(fake_generation_error.exception),
            "No module named 'notexisting'",
        )

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(
        GRPC_FRAMEWORK=overide_grpc_framework("error_service_unkown_handler_hook")
    )
    def test_raise_when_service_not_existing(self):
        args = []
        opts = {"no_generate_pb2": True}
        with self.assertRaises(ModuleNotFoundError) as fake_generation_error:
            call_command("generateproto", *args, **opts)

        self.assertEqual(
            str(fake_generation_error.exception),
            "No module named 'fakeapp.services.unknow_service_service'",
        )

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=OVERRIDEN_SETTINGS["MODEL_WITH_M2M_GENERATED"])
    def test_generate_message_with_repeated_for_m2m(self):
        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        proto_file_content = get_proto_file_content("MODEL_WITH_M2M_GENERATED")

        self.assertEqual(called_with_data, proto_file_content)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=OVERRIDEN_SETTINGS["SIMPLE_MODEL_GENERATED"])
    def test_generate_one_app_one_model_with_custom_action(self):
        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        proto_file_content = get_proto_file_content("SIMPLE_MODEL_GENERATED")

        self.assertEqual(called_with_data, proto_file_content)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=OVERRIDEN_SETTINGS["RECURSIVE_MODEL_GENERATED"])
    def test_generate_one_app_one_model_recursive(self):
        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        proto_file_content = get_proto_file_content("RECURSIVE_MODEL_GENERATED")

        self.assertEqual(called_with_data, proto_file_content)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(
        GRPC_FRAMEWORK=OVERRIDEN_SETTINGS["MODEL_WITH_KNOWN_METHOD_OVERRIDEN_GENERATED"]
    )
    def test_generate_one_app_one_model_with_override_know_method(self):
        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        proto_file_content = get_proto_file_content(
            "MODEL_WITH_KNOWN_METHOD_OVERRIDEN_GENERATED"
        )

        self.assertEqual(called_with_data, proto_file_content)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=OVERRIDEN_SETTINGS["CUSTOM_APP_MODEL_GENERATED"])
    def test_generate_one_app_one_model_customized(self):
        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        proto_file_content = get_proto_file_content("CUSTOM_APP_MODEL_GENERATED")

        self.assertEqual(called_with_data, proto_file_content)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=OVERRIDEN_SETTINGS["MODEL_WITH_STRUCT_IMORT_IN_ARRAY"])
    def test_generate_one_app_one_model_import_struct_in_array(self):
        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        proto_file_content = get_proto_file_content("MODEL_WITH_STRUCT_IMORT_IN_ARRAY")

        self.assertEqual(called_with_data, proto_file_content)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=protoparser.parse(old_order_data)),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework("unittestmodel_handler_hook"))
    def test_order_proto_field_if_existing(self):
        """
        This test make the like the old unittestmodel have only id and title field.
        So when regeneration with the text field it should appear in third position and not in second
        """
        args = []
        opts = {"no_generate_pb2": True}

        with patch_open(read_data=old_order_data) as mocked_open:
            call_command("generateproto", *args, **opts)

        mocked_open.assert_called()
        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        output_data = get_proto_file_content("SIMPLE_APP_MODEL_GENERATED_FROM_OLD_ORDER")

        self.assertEqual(called_with_data, output_data)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=OVERRIDEN_SETTINGS["NO_MODEL_GENERATED"])
    def test_generate_service_no_model(self):
        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        proto_file_content = get_proto_file_content("NO_MODEL_GENERATED")

        self.assertEqual(called_with_data, proto_file_content)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    def test_generate_all_models_separate_read_write(self):
        reload_all()

        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        proto_file_content = get_proto_file_content("ALL_APP_GENERATED_SEPARATE")

        self.assertEqual(called_with_data, proto_file_content)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=OVERRIDEN_SETTINGS["ALL_APP_GENERATED_NO_SEPARATE"])
    def test_generate_all_models_no_separate(self):
        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"

        handle = mocked_open()

        called_with_data = handle.write.call_args[0][0]

        proto_file_content = get_proto_file_content("ALL_APP_GENERATED_NO_SEPARATE")

        self.assertEqual(called_with_data, proto_file_content)

    @mock.patch(
        "django_socio_grpc.protobuf.generators.RegistryToProtoGenerator.parse_proto_file",
        mock.MagicMock(return_value=None),
    )
    @override_settings(GRPC_FRAMEWORK=overide_grpc_framework_in_root_grpc())
    def test_generate_proto_to_root_grpc(self):
        args = []
        opts = {"no_generate_pb2": True}
        with patch_open() as mocked_open:
            call_command("generateproto", *args, **opts)

        assert mocked_open.mock_calls[0].args[0] == "w+"
