import os
from unittest import mock
from unittest.mock import mock_open, patch

from django.core.management import call_command
from django.test import TestCase

from django_socio_grpc.exceptions import ProtobufGenerationException

from .assets.generated_protobuf_files_old_way import (
    ALL_APP_GENERATED,
    APP_MODEL_WITH_CUSTOM_FIELD_FROM_OLD_ORDER,
    APP_MODEL_WITH_CUSTOM_FIELD_OLD_ORDER,
    CUSTOM_APP_MODEL_GENERATED,
    MODEL_WITH_M2M_GENERATED,
    MODEL_WITH_STRUCT_IMORT_IN_ARRAY,
    SIMPLE_APP_MODEL_GENERATED,
    SIMPLE_APP_MODEL_GENERATED_FROM_OLD_ORDER,
    SIMPLE_APP_MODEL_NO_GENERATION,
    SIMPLE_APP_MODEL_OLD_ORDER,
    SIMPLE_MODEL_GENERATED,
)


@patch.dict(os.environ, {"DJANGO_SETTINGS_MODULE": "myproject.settings"})
class TestProtoGenerationOldWay(TestCase):
    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_one_model(self):
        self.maxDiff = None
        args = []
        opts = {
            "model": "unittestmodel",
            "file": "proto/unittestmodel.proto",
            "generate_python": False,
        }
        with patch("builtins.open", mock_open()) as m:
            call_command("generate_proto_old_way", *args, **opts)

        m.assert_called_once_with("proto/unittestmodel.proto", "w+")
        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, SIMPLE_MODEL_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_check_option(self):
        self.maxDiff = None
        args = []
        opts = {"app": "fakeapp", "generate_python": False, "check": True}
        with patch("builtins.open", mock_open(read_data=ALL_APP_GENERATED)) as m:
            call_command("generate_proto_old_way", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "r+"

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_raise_when_no_app_and_no_model_options(self):
        args = []
        opts = {}
        with self.assertRaises(ProtobufGenerationException) as fake_generation_error:
            call_command("generate_proto_old_way", *args, **opts)

        self.assertEqual(
            str(fake_generation_error.exception),
            "Error on protobuf generation on model None on app None: You need to specify at least one app or one model",
        )

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_raise_when_app_not_found(self):
        args = []
        opts = {"app": "app_not_existing"}
        with self.assertRaises(ProtobufGenerationException) as fake_generation_error:
            call_command("generate_proto_old_way", *args, **opts)

        self.assertEqual(
            str(fake_generation_error.exception),
            "Error on protobuf generation on model None on app app_not_existing: Invalid Django app",
        )

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_raise_when_model_not_found(self):
        args = []
        opts = {"model": "model_not_existing"}
        with self.assertRaises(ProtobufGenerationException) as fake_generation_error:
            call_command("generate_proto_old_way", *args, **opts)

        self.assertEqual(
            str(fake_generation_error.exception),
            "Error on protobuf generation on model model_not_existing on app None: Invalid Django model",
        )

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_message_with_repeated_for_m2m(self):
        self.maxDiff = None

        args = []
        opts = {"app": "fakeapp", "model": "RelatedFieldModel", "generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generate_proto_old_way", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, MODEL_WITH_M2M_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_one_app_one_model_no_message_no_methods(self):
        self.maxDiff = None

        args = []
        opts = {"app": "fakeapp", "model": "NotDisplayedModel", "generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generate_proto_old_way", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"
        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, SIMPLE_APP_MODEL_NO_GENERATION)

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_one_app_one_model(self):
        self.maxDiff = None
        args = []
        opts = {"app": "fakeapp", "model": "unittestmodel", "generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generate_proto_old_way", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, SIMPLE_APP_MODEL_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_one_app_all_models(self):
        self.maxDiff = None

        args = []
        opts = {"app": "fakeapp", "generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generate_proto_old_way", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, ALL_APP_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_one_app_one_model_customized(self):
        self.maxDiff = None
        args = []
        opts = {"app": "fakeapp", "model": "ForeignModel", "generate_python": False}
        with patch("builtins.open", mock_open()) as m:
            call_command("generate_proto_old_way", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, CUSTOM_APP_MODEL_GENERATED)

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=False),
    )
    def test_generate_one_app_one_model_import_struct_in_array(self):
        self.maxDiff = None
        args = []
        opts = {
            "app": "fakeapp",
            "model": "ImportStructEvenInArrayModel",
            "generate_python": False,
        }
        with patch("builtins.open", mock_open()) as m:
            call_command("generate_proto_old_way", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "w+"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, MODEL_WITH_STRUCT_IMORT_IN_ARRAY)

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=True),
    )
    def test_order_proto_field_if_existing(self):
        """
        This test make the like the old unittestmodel have only id and title field.
        So when regeneration with the text field it should appear in third position and not in second
        """
        self.maxDiff = None
        args = []
        opts = {"app": "fakeapp", "model": "unittestmodel", "generate_python": False}
        with patch("builtins.open", mock_open(read_data=SIMPLE_APP_MODEL_OLD_ORDER)) as m:
            call_command("generate_proto_old_way", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "r"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, SIMPLE_APP_MODEL_GENERATED_FROM_OLD_ORDER)

    @mock.patch(
        "django_socio_grpc.protobuf.generators_old_way.ModelProtoGeneratorOldWay.check_if_existing_proto_file",
        mock.MagicMock(return_value=True),
    )
    def test_order_proto_field_if_existing_with_custom_field(self):
        """
        This test make the like the old RelatedFieldModel on the RelatedFieldModelListResponse message have only uuid and custom_field_name field.
        So when regeneration with all the new field custom_field_name should keep is second position and the other go at the end
        """
        self.maxDiff = None
        args = []
        opts = {"app": "fakeapp", "model": "relatedfieldmodel", "generate_python": False}
        with patch(
            "builtins.open", mock_open(read_data=APP_MODEL_WITH_CUSTOM_FIELD_OLD_ORDER)
        ) as m:
            call_command("generate_proto_old_way", *args, **opts)

        # this is done to avoid error on different absolute path
        assert m.mock_calls[0].args[0].endswith("fakeapp/grpc/fakeapp.proto")
        assert m.mock_calls[0].args[1] == "r"

        handle = m()

        called_with_data = handle.write.call_args[0][0]
        self.assertEqual(called_with_data, APP_MODEL_WITH_CUSTOM_FIELD_FROM_OLD_ORDER)
