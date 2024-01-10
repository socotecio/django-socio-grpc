from django_socio_grpc.protobuf.proto_classes import (
    FieldCardinality,
    ProtoField,
)
from fakeapp.serializers import DefaultValueSerializer
from django.test import TestCase, override_settings

from .grpc_test_utils.fake_grpc import FakeFullAIOGRPC

from fakeapp.grpc.fakeapp_pb2_grpc import (
    SimpleRelatedFieldModelControllerStub,
    add_SimpleRelatedFieldModelControllerServicer_to_server,
)
from fakeapp.services.default_value_service import DefaultValueService
from fakeapp.grpc import fakeapp_pb2
from fakeapp.models import DefaultValueModel



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
            add_SimpleRelatedFieldModelControllerServicer_to_server, DefaultValueService.as_servicer()
        )

        self.setup_instance = DefaultValueModel.objects.create(string_required="setUp", string_required_but_serializer_default="setup_serializer", int_required=50, int_required_but_serializer_default="60", boolean_required=True, boolean_required_but_serializer_default=False)

    async def test_retrieve_all_default_value(self):

        grpc_stub = self.fake_grpc.get_fake_stub(SimpleRelatedFieldModelControllerStub)
        request = fakeapp_pb2.UnitTestModelRetrieveRequest(id=self.setup_instance.id)
        response = await grpc_stub.Retrieve(request=request)

        self.assertEqual(response.title, "z")
        self.assertEqual(response.text, "abc")
        assert False