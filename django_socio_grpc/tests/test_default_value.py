import grpc
from django.test import TestCase, override_settings
from fakeapp.grpc import fakeapp_pb2
from fakeapp.grpc.fakeapp_pb2_grpc import (
    DefaultValueControllerStub,
    add_DefaultValueControllerServicer_to_server,
)
from fakeapp.models import DefaultValueModel
from fakeapp.serializers import DefaultValueSerializer
from fakeapp.services.default_value_service import DefaultValueService

from django_socio_grpc.protobuf.proto_classes import FieldCardinality, ProtoField
from django_socio_grpc.utils.constants import PARTIAL_UPDATE_FIELD_NAME

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC


class TestDefaultValueField:
    # FROM_FIELD
    def test_from_field_string(self):
        ser = DefaultValueSerializer()
        field = ser.fields["string_required"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_required"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.NONE

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["string_blank"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_blank"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["string_nullable"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_nullable"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["string_default"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_default"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["string_required_but_serializer_default"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "string_required_but_serializer_default"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

    def test_from_field_integer(self):
        ser = DefaultValueSerializer()
        field = ser.fields["int_required"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "int_required"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.NONE

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["int_nullable"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "int_nullable"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["int_default"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "int_default"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["int_required_but_serializer_default"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "int_required_but_serializer_default"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

    def test_from_field_boolean(self):
        ser = DefaultValueSerializer()
        field = ser.fields["boolean_required"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "boolean_required"
        assert proto_field.field_type == "bool"
        assert proto_field.cardinality == FieldCardinality.NONE

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["boolean_nullable"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "boolean_nullable"
        assert proto_field.field_type == "bool"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["boolean_default_true"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "boolean_default_true"
        assert proto_field.field_type == "bool"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["boolean_default_false"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "boolean_default_false"
        assert proto_field.field_type == "bool"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

        # ---------------------------------

        ser = DefaultValueSerializer()
        field = ser.fields["boolean_required_but_serializer_default"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "boolean_required_but_serializer_default"
        assert proto_field.field_type == "bool"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL


@override_settings(GRPC_FRAMEWORK={"GRPC_ASYNC": True})
class TestDefaultValueService(TestCase):
    def setUp(self):
        self.fake_grpc = FakeFullAIOGRPC(
            add_DefaultValueControllerServicer_to_server, DefaultValueService.as_servicer()
        )

        self.setup_instance = DefaultValueModel.objects.create(
            string_required="setUp",
            string_required_but_serializer_default="setup_serializer",
            int_required=50,
            int_required_but_serializer_default=60,
            boolean_required=True,
            boolean_required_but_serializer_default=False,
        )

    async def test_retrieve_all_default_value(self):
        grpc_stub = self.fake_grpc.get_fake_stub(DefaultValueControllerStub)
        request = fakeapp_pb2.DefaultValueRequest(id=self.setup_instance.id)
        response = await grpc_stub.Retrieve(request=request)

        # STRING ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertTrue(response.HasField("string_blank"))
        self.assertFalse(response.HasField("string_nullable"))
        self.assertTrue(response.HasField("string_default_and_blank"))
        self.assertTrue(response.HasField("string_null_default_and_blank"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(response.string_required, "setUp")
        self.assertEqual(response.string_blank, "")
        self.assertEqual(response.string_nullable, "")
        self.assertEqual(response.string_default_and_blank, "default_and_blank")
        self.assertEqual(response.string_null_default_and_blank, "null_default_and_blank")
        self.assertEqual(response.string_default, "default")
        self.assertEqual(
            response.string_required_but_serializer_default, "setup_serializer"
        )  # created in setup not serializer so default value != than value in instance because required. See create test for testing default serializer value
        self.assertEqual(
            response.string_default_but_serializer_default, "default"
        )  # created in setup not serializer so default value != than value in serializer. See create test for testing default serializer value
        self.assertEqual(
            response.string_nullable_default_but_serializer_default, "default"
        )  # created in setup not serializer so default value != than value in serializer. See create test for testing default serializer value
        # INTEGER ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertFalse(response.HasField("int_nullable"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(response.int_required, 50)
        self.assertEqual(response.int_nullable, 0)
        self.assertEqual(response.int_default, 5)
        self.assertEqual(
            response.int_required_but_serializer_default, 60
        )  # created in setup not serializer so default value != than value in instance. See create test for testung default serializer value

        # BOOLEAN ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertFalse(response.HasField("boolean_nullable"))
        self.assertTrue(response.HasField("boolean_default_false"))
        self.assertTrue(response.HasField("boolean_default_true"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(response.boolean_required, True)
        self.assertEqual(response.boolean_nullable, False)
        self.assertEqual(response.boolean_default_false, False)
        self.assertEqual(response.boolean_default_true, True)
        self.assertEqual(
            response.boolean_required_but_serializer_default, False
        )  # created in setup not serializer so default value != than value in instance. See create test for testung default serializer value

    async def test_create_all_default_value(self):
        grpc_stub = self.fake_grpc.get_fake_stub(DefaultValueControllerStub)
        request = fakeapp_pb2.DefaultValueRequest(
            string_required="create", int_required=100, boolean_required=True
        )
        response = await grpc_stub.Create(request=request)

        # STRING ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertTrue(response.HasField("string_blank"))
        self.assertFalse(response.HasField("string_nullable"))
        self.assertTrue(response.HasField("string_default_and_blank"))
        self.assertTrue(response.HasField("string_null_default_and_blank"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(response.string_required, "create")
        self.assertEqual(response.string_blank, "")
        self.assertEqual(response.string_nullable, "")
        self.assertEqual(response.string_default_and_blank, "default_and_blank")
        self.assertEqual(response.string_null_default_and_blank, "null_default_and_blank")
        self.assertEqual(response.string_default, "default")
        self.assertEqual(response.string_required_but_serializer_default, "default_serializer")
        self.assertEqual(
            response.string_default_but_serializer_default, "default_serializer_override"
        )
        self.assertEqual(
            response.string_nullable_default_but_serializer_default,
            "default_serializer_override",
        )

        # INTEGER ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertFalse(response.HasField("int_nullable"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(response.int_required, 100)
        self.assertEqual(response.int_nullable, 0)
        self.assertEqual(response.int_default, 5)
        self.assertEqual(response.int_required_but_serializer_default, 10)

        # BOOLEAN ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertFalse(response.HasField("boolean_nullable"))
        self.assertTrue(response.HasField("boolean_default_false"))
        self.assertTrue(response.HasField("boolean_default_true"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(response.boolean_required, True)
        self.assertEqual(response.boolean_nullable, False)
        self.assertEqual(response.boolean_default_false, False)
        self.assertEqual(response.boolean_default_true, True)
        self.assertEqual(response.boolean_required_but_serializer_default, False)

    async def test_update_all_default_value(self):
        all_setted_instance = await DefaultValueModel.objects.acreate(
            string_required="update_required",
            string_blank="update_blank",
            string_nullable="update_nullable",
            string_default="update_default",
            string_default_and_blank="update_default_and_blank",
            string_null_default_and_blank="update_null_default_and_blank",
            string_required_but_serializer_default="update_serializer",
            string_default_but_serializer_default="update_serializer_override",
            string_nullable_default_but_serializer_default="update_serializer_override",
            int_required=200,
            int_nullable=201,
            int_default=202,
            int_required_but_serializer_default=60,
            boolean_required=True,
            boolean_nullable=True,
            boolean_default_false=True,
            boolean_default_true=False,
            boolean_required_but_serializer_default=True,
        )

        grpc_stub = self.fake_grpc.get_fake_stub(DefaultValueControllerStub)
        request = fakeapp_pb2.DefaultValueRequest(
            id=all_setted_instance.id,
            string_required="update_required2",
            string_blank="",
            string_default_and_blank="",
            int_required=0,
            boolean_required=False,
        )
        response = await grpc_stub.Update(request=request)

        # STRING ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertTrue(response.HasField("string_blank"))
        self.assertFalse(response.HasField("string_nullable"))
        self.assertTrue(response.HasField("string_default_and_blank"))
        self.assertFalse(response.HasField("string_null_default_and_blank"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(response.string_required, "update_required2")
        self.assertEqual(response.string_blank, "")
        self.assertEqual(response.string_nullable, "")
        self.assertEqual(response.string_default_and_blank, "")
        self.assertEqual(response.string_null_default_and_blank, "")
        self.assertEqual(
            response.string_default, "update_default"
        )  # This field not updated because model default only apply on creation
        self.assertEqual(response.string_required_but_serializer_default, "default_serializer")
        self.assertEqual(
            response.string_default_but_serializer_default, "default_serializer_override"
        )
        self.assertEqual(
            response.string_nullable_default_but_serializer_default,
            "default_serializer_override",
        )

        await all_setted_instance.arefresh_from_db()
        self.assertEqual(all_setted_instance.string_blank, "")
        self.assertEqual(all_setted_instance.string_nullable, None)
        self.assertEqual(all_setted_instance.string_default_and_blank, "")
        self.assertEqual(all_setted_instance.string_null_default_and_blank, None)

        # INTEGER ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertFalse(response.HasField("int_nullable"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(response.int_required, 0)
        self.assertEqual(response.int_nullable, 0)
        self.assertEqual(
            response.int_default, 202
        )  # This field not updated because model default only apply on creation
        self.assertEqual(response.int_required_but_serializer_default, 10)

        self.assertEqual(all_setted_instance.int_nullable, None)

        # BOOLEAN ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertFalse(response.HasField("boolean_nullable"))
        self.assertTrue(response.HasField("boolean_default_false"))
        self.assertTrue(response.HasField("boolean_default_true"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(response.boolean_required, False)
        self.assertEqual(response.boolean_nullable, False)
        self.assertEqual(
            response.boolean_default_false, True
        )  # This field not updated because model default only apply on creation
        self.assertEqual(
            response.boolean_default_true, False
        )  # This field not updated because model default only apply on creation
        self.assertEqual(response.boolean_required_but_serializer_default, False)

        self.assertEqual(all_setted_instance.boolean_nullable, None)

    async def test_update_string_not_setted_and_blank_not_allowed_raise_error(self):
        grpc_stub = self.fake_grpc.get_fake_stub(DefaultValueControllerStub)
        request = fakeapp_pb2.DefaultValueRequest(
            id=self.setup_instance.id,
            string_required="update_required2",
            string_default="",
            int_required=0,
            boolean_required=False,
        )

        with self.assertRaises(grpc.RpcError) as error:
            await grpc_stub.Update(request=request)

        self.assertEqual(error.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)

        self.assertEqual(
            '{"string_default": [{"message": "This field may not be blank.", "code": "blank"}]}',
            error.exception.details(),
        )

    async def test_partial_update_specifying_optional_but_not_set_them(self):
        all_setted_instance = await DefaultValueModel.objects.acreate(
            string_required="update_required",
            string_blank="update_blank",
            string_nullable="update_nullable",
            string_default="update_default",
            string_default_and_blank="update_default_and_blank",
            string_null_default_and_blank="update_null_default_and_blank",
            string_required_but_serializer_default="update_serializer",
            string_default_but_serializer_default="update_serializer_override",
            string_nullable_default_but_serializer_default="update_serializer_override",
            int_required=200,
            int_nullable=201,
            int_default=202,
            int_required_but_serializer_default=60,
            boolean_required=True,
            boolean_nullable=True,
            boolean_default_false=True,
            boolean_default_true=False,
            boolean_required_but_serializer_default=True,
        )

        grpc_stub = self.fake_grpc.get_fake_stub(DefaultValueControllerStub)

        # Notice abscence of "string_default" as it is a required field and default grpc value (empty string) is not valid if blank not True
        request = fakeapp_pb2.DefaultValuePartialUpdateRequest(
            id=all_setted_instance.id,
            **{
                PARTIAL_UPDATE_FIELD_NAME: [
                    "string_blank",
                    "string_nullable",
                    "string_default_and_blank",
                    "string_null_default_and_blank",
                    "string_required_but_serializer_default",
                    "string_default_but_serializer_default",
                    "string_nullable_default_but_serializer_default",
                    "int_nullable",
                    "int_default",
                    "int_required_but_serializer_default",
                    "boolean_nullable",
                    "boolean_default_false",
                    "boolean_default_true",
                    "boolean_required_but_serializer_default",
                ]
            }
        )
        response = await grpc_stub.PartialUpdate(request=request)

        # STRING ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertTrue(response.HasField("string_blank"))
        self.assertFalse(response.HasField("string_nullable"))
        self.assertTrue(response.HasField("string_default_and_blank"))
        self.assertFalse(response.HasField("string_null_default_and_blank"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(
            response.string_required, "update_required"
        )  # Field not updated because not specified in PARTIAL_UPDATE_FIELD_NAME
        self.assertEqual(response.string_blank, "")
        self.assertEqual(response.string_nullable, "")
        self.assertEqual(response.string_default_and_blank, "")
        self.assertEqual(
            response.string_default, "update_default"
        )  # Field not updated because not specified in PARTIAL_UPDATE_FIELD_NAME
        self.assertEqual(response.string_required_but_serializer_default, "default_serializer")
        self.assertEqual(
            response.string_default_but_serializer_default, "default_serializer_override"
        )
        self.assertEqual(
            response.string_nullable_default_but_serializer_default,
            "default_serializer_override",
        )

        await all_setted_instance.arefresh_from_db()
        self.assertEqual(all_setted_instance.string_blank, "")
        self.assertEqual(all_setted_instance.string_nullable, None)
        self.assertEqual(all_setted_instance.string_default_and_blank, "")
        self.assertEqual(all_setted_instance.string_null_default_and_blank, None)

        # INTEGER ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertFalse(response.HasField("int_nullable"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(
            response.int_required, 200
        )  # Field not updated because not specified in PARTIAL_UPDATE_FIELD_NAME
        self.assertEqual(response.int_nullable, 0)
        self.assertEqual(
            response.int_default, 0
        )  # This field is updated because the default value (0) is authorized by the serializer
        self.assertEqual(response.int_required_but_serializer_default, 10)

        # BOOLEAN ##################

        # INFO - AM - 12/01/2024 - check presence / not presence depending if element is None or empty
        self.assertFalse(response.HasField("boolean_nullable"))
        self.assertTrue(response.HasField("boolean_default_false"))
        self.assertTrue(response.HasField("boolean_default_true"))

        # INFO - AM - 12/01/2024 - check value event if grpc default because we check presence before
        self.assertEqual(
            response.boolean_required, True
        )  # Field not updated because not specified in PARTIAL_UPDATE_FIELD_NAME
        self.assertEqual(response.boolean_nullable, False)
        self.assertEqual(
            response.boolean_default_false, False
        )  # This field is set to false because it's the default value of bool in gRPC as not specified
        self.assertEqual(
            response.boolean_default_true, False
        )  # This field is set to false because it's the default value of bool in gRPC as not specified
        self.assertEqual(response.boolean_required_but_serializer_default, False)

    async def test_partial_update_choosing_a_required_without_setting_it_raise_error(self):
        all_setted_instance = await DefaultValueModel.objects.acreate(
            string_required="update_required",
            string_blank="update_blank",
            string_nullable="update_nullable",
            string_default="update_default",
            string_default_and_blank="update_default_and_blank",
            string_null_default_and_blank="update_null_default_and_blank",
            string_required_but_serializer_default="update_serializer",
            int_required=200,
            int_nullable=201,
            int_default=202,
            int_required_but_serializer_default=60,
            boolean_required=True,
            boolean_nullable=True,
            boolean_default_false=True,
            boolean_default_true=False,
            boolean_required_but_serializer_default=True,
        )

        grpc_stub = self.fake_grpc.get_fake_stub(DefaultValueControllerStub)

        request = fakeapp_pb2.DefaultValuePartialUpdateRequest(
            id=all_setted_instance.id,
            **{
                PARTIAL_UPDATE_FIELD_NAME: [
                    "string_default",
                ]
            }
        )

        with self.assertRaises(grpc.RpcError) as error:
            await grpc_stub.PartialUpdate(request=request)

        self.assertEqual(error.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)

        self.assertEqual(
            '{"string_default": [{"message": "This field may not be blank.", "code": "blank"}]}',
            error.exception.details(),
        )

    async def test_partial_update_choosing_default_grpc_value_for_nullable_field(self):
        # set "" for string_null_default_and_blank
        # set 0 for int_nullable
        # set False for boolean_nullable
        all_setted_instance = await DefaultValueModel.objects.acreate(
            string_required="update_required",
            string_blank="update_blank",
            string_nullable="update_nullable",
            string_default="update_default",
            string_default_and_blank="update_default_and_blank",
            string_null_default_and_blank="update_null_default_and_blank",
            string_required_but_serializer_default="update_serializer",
            int_required=200,
            int_nullable=201,
            int_default=202,
            int_required_but_serializer_default=60,
            boolean_required=True,
            boolean_nullable=True,
            boolean_default_false=True,
            boolean_default_true=False,
            boolean_required_but_serializer_default=True,
        )

        grpc_stub = self.fake_grpc.get_fake_stub(DefaultValueControllerStub)

        # Notice abscence of "string_default" as it is a required field and default grpc value (empty string) is not valid if blank not True
        request = fakeapp_pb2.DefaultValuePartialUpdateRequest(
            id=all_setted_instance.id,
            string_null_default_and_blank="",
            int_nullable=0,
            boolean_nullable=False,
            **{
                PARTIAL_UPDATE_FIELD_NAME: [
                    "string_null_default_and_blank",
                    "int_nullable",
                    "boolean_nullable",
                ]
            }
        )
        response = await grpc_stub.PartialUpdate(request=request)

        self.assertTrue(response.HasField("string_null_default_and_blank"))
        self.assertTrue(response.HasField("int_nullable"))
        self.assertTrue(response.HasField("boolean_nullable"))

        self.assertEqual(response.string_null_default_and_blank, "")
        self.assertEqual(response.int_nullable, 0)
        self.assertEqual(response.boolean_nullable, False)

        await all_setted_instance.arefresh_from_db()
        self.assertEqual(all_setted_instance.string_null_default_and_blank, "")
        self.assertEqual(all_setted_instance.int_nullable, 0)
        self.assertEqual(all_setted_instance.boolean_nullable, False)
