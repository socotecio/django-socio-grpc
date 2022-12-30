from typing import List

import pytest
from django.db import models
from rest_framework import serializers

from django_socio_grpc import proto_serializers
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.protobuf import ProtoComment, ProtoRegistrationError
from django_socio_grpc.protobuf.proto_classes import (
    FieldCardinality,
    ProtoField,
    ProtoMessage,
    RequestProtoMessage,
    ResponseProtoMessage,
    StructMessage,
)
from django_socio_grpc.services import Service
from django_socio_grpc.tests.fakeapp.models import RelatedFieldModel
from django_socio_grpc.tests.fakeapp.serializers import (
    BasicProtoListChildSerializer,
    BasicServiceSerializer,
    RelatedFieldModelSerializer,
)


class MyIntModel(models.Model):
    class Choices(models.IntegerChoices):
        ONE = 1
        TWO = 2
        THREE = 3

    choice_field = models.IntegerField(
        choices=Choices.choices,
        default=Choices.ONE,
    )


class MyIntSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = MyIntModel
        fields = "__all__"


class MySerializer(proto_serializers.ProtoSerializer):

    user_name = serializers.IntegerField(
        help_text=ProtoComment(["@test=comment1", "@test2=comment2"])
    )
    title = serializers.CharField()
    optional_field = serializers.CharField(allow_null=True)
    list_field = serializers.ListField(child=serializers.CharField())

    smf = serializers.SerializerMethodField()
    smf_with_serializer = serializers.SerializerMethodField()

    read_only_field0 = serializers.CharField(read_only=True)
    read_only_field1 = serializers.CharField(read_only=True)
    write_only_field = serializers.CharField(write_only=True)

    def get_smf(self, obj) -> List[int]:
        ...

    def get_smf_with_serializer(self, obj) -> BasicServiceSerializer:
        ...


class MyOtherSerializer(proto_serializers.ModelProtoSerializer):

    serializer = MySerializer()
    serializer_list = MySerializer(many=True)

    pk_related_source_field = serializers.PrimaryKeyRelatedField(
        read_only=True,
        source="foreign.uuid",
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )

    many_related_field = serializers.SlugRelatedField(
        slug_field="name", source="many_many_foreigns.foreign", read_only=True, many=True
    )

    class Meta:
        model = RelatedFieldModel
        proto_comment = "serializer comment"
        message_list_attr = "custom_results"
        fields = (
            "serializer",
            "serializer_list",
            "pk_related_source_field",
            "many_related_field",
        )


class TestFields:
    def test_to_string(self):
        proto_field = ProtoField("title", "string", FieldCardinality.NONE, index=0)
        assert str(proto_field) == "string title = 0;"
        proto_field = ProtoField("title", "string", FieldCardinality.REPEATED, index=0)
        assert str(proto_field) == "repeated string title = 0;"
        proto_field = ProtoField("number", "int32", FieldCardinality.OPTIONAL, index=1)
        assert str(proto_field) == "optional int32 number = 1;"
        proto_field = ProtoField(
            "number",
            "int32",
            FieldCardinality.REPEATED,
            index=1,
            comments=["comment0", "comment1"],
        )
        assert str(proto_field) == "// comment0\n// comment1\nrepeated int32 number = 1;"
        proto_field = ProtoField(
            "req",
            ProtoMessage("TestMessage", []),
            FieldCardinality.NONE,
            index=1,
        )
        assert str(proto_field) == "TestMessage req = 1;"

    # FROM_FIELD
    def test_from_field_basic(self):
        ser = MySerializer()
        field = ser.fields["title"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "title"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.NONE
        assert proto_field.comments is None

    def test_from_field_with_comments(self):
        ser = MySerializer()
        field = ser.fields["user_name"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "user_name"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.NONE
        assert proto_field.comments == ["@test=comment1", "@test2=comment2"]

    def test_from_field_optional(self):
        ser = MySerializer()
        field = ser.fields["optional_field"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "optional_field"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL
        assert proto_field.comments is None

    def test_from_field_repeated(self):
        ser = MySerializer()
        field = ser.fields["list_field"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "list_field"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.REPEATED
        assert proto_field.comments is None

    def test_from_field_slug_related_field(self):
        ser = RelatedFieldModelSerializer()
        field = ser.fields["slug_test_model"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "slug_test_model"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.NONE
        assert proto_field.comments is None

    def test_from_field_related_field_source(self):
        ser = MyOtherSerializer()
        field = ser.fields["pk_related_source_field"]
        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "pk_related_source_field"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.NONE
        assert proto_field.comments is None

        field = ser.fields["many_related_field"]
        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "many_related_field"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.REPEATED
        assert proto_field.comments is None

    def test_from_field_serializer_method_field(self):
        ser = MySerializer()
        field = ser.fields["smf"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "smf"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.REPEATED
        assert proto_field.comments is None

    def test_from_field_serializer_method_field_with_serializer(self):
        ser = MySerializer()
        field = ser.fields["smf_with_serializer"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "smf_with_serializer"
        assert proto_field.field_type is BasicServiceSerializer
        assert proto_field.cardinality == FieldCardinality.NONE

    def test_from_field_serializer_choice_field(self):
        ser = MyIntSerializer()
        field = ser.fields["choice_field"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "choice_field"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.NONE

    # FROM_SERIALIZER

    def test_from_serializer(self):
        ser = MyOtherSerializer()
        field = ser.fields["serializer"]

        proto_message = ProtoField.from_serializer(field)

        assert proto_message.name == "serializer"
        assert proto_message.field_type is MySerializer
        assert proto_message.cardinality == FieldCardinality.NONE

    def test_from_list_serializer(self):
        ser = MyOtherSerializer()
        field = ser.fields["serializer_list"]

        proto_message = ProtoField.from_serializer(field)

        assert proto_message.name == "serializer_list"
        assert proto_message.field_type is MySerializer
        assert proto_message.cardinality == FieldCardinality.REPEATED

    def test_from_field_dict(self):
        field_dict = {
            "name": "title",
            "type": "string",
            "comment": None,
        }

        proto_field = ProtoField.from_field_dict(field_dict)

        assert proto_field.name == "title"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.NONE
        assert proto_field.comments is None

        field_dict = {
            "name": "title",
            "type": "repeated string",
            "comment": "comment0",
        }

        proto_field = ProtoField.from_field_dict(field_dict)

        assert proto_field.name == "title"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.REPEATED
        assert proto_field.comments == ["comment0"]

        field_dict = {
            "name": "title",
            "type": "optional string",
            "comment": ["comment0", "comment1"],
        }

        proto_field = ProtoField.from_field_dict(field_dict)

        assert proto_field.name == "title"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL
        assert proto_field.comments == ["comment0", "comment1"]

        with pytest.raises(ProtoRegistrationError):
            field_dict = {
                "name": "title",
                "type": "unknown string",
                "comment": ["comment0", "comment1"],
            }

            proto_field = ProtoField.from_field_dict(field_dict)


class TestProtoMessage:
    def test_from_field_dicts(self):
        field_dicts = [
            {
                "name": "title",
                "type": "string",
                "comment": None,
            },
            {
                "name": "title",
                "type": "repeated string",
                "comment": "comment0",
            },
            {
                "name": "struct",
                "type": "google.protobuf.Struct",
            },
        ]

        proto_message = ProtoMessage.from_field_dicts(field_dicts, "name")

        assert proto_message.name == "name"
        assert len(proto_message.fields) == 3

        assert proto_message.fields[0].name == "title"
        assert proto_message.fields[0].field_type == "string"
        assert proto_message.fields[0].cardinality == FieldCardinality.NONE
        assert proto_message.fields[0].comments is None

        assert proto_message.fields[1].name == "title"
        assert proto_message.fields[1].field_type == "string"
        assert proto_message.fields[1].cardinality == FieldCardinality.REPEATED
        assert proto_message.fields[1].comments == ["comment0"]

        assert proto_message.fields[2].name == "struct"
        assert proto_message.fields[2].field_type == StructMessage
        assert proto_message.fields[2].cardinality == FieldCardinality.NONE

    def test_from_serializer(self):
        proto_message = ProtoMessage.from_serializer(MySerializer)

        assert proto_message.name == "My"
        assert len(proto_message.fields) == 9

    def test_from_serializer_request(self):
        proto_message = RequestProtoMessage.from_serializer(MySerializer)

        assert proto_message.name == "MyRequest"
        assert len(proto_message.fields) == 5

        assert "write_only_field" in proto_message

        proto_message = RequestProtoMessage.from_serializer(MySerializer, "CustomName")

        assert proto_message.name == "CustomName"
        assert len(proto_message.fields) == 5

    def test_from_serializer_response(self):
        proto_message = ResponseProtoMessage.from_serializer(MySerializer)

        assert proto_message.name == "MyResponse"
        assert len(proto_message.fields) == 8

    def test_from_serializer_nested(self):
        proto_message = ResponseProtoMessage.from_serializer(MyOtherSerializer)

        assert proto_message.name == "MyOtherResponse"
        assert len(proto_message.fields) == 4
        assert proto_message.comments == ["serializer comment"]

        assert proto_message.fields[0].name == "serializer"
        assert len(proto_message.fields[0].field_type.fields) == 8

    def test_as_list_message(self):
        proto_message = ResponseProtoMessage.from_serializer(MySerializer)
        list_message = ResponseProtoMessage.as_list_message(proto_message)
        assert "results" in list_message

        proto_message = ResponseProtoMessage.from_serializer(MyOtherSerializer)
        list_message = ResponseProtoMessage.as_list_message(proto_message)

        assert list_message.name == "MyOtherListResponse"
        assert len(list_message.fields) == 2
        results_field = list_message["custom_results"]
        assert results_field.cardinality == FieldCardinality.REPEATED
        results_type = results_field.field_type

        assert results_type.name == "MyOtherResponse"


class TestGrpcActionProto:
    class MyAction(Service):
        serializer_class = MySerializer

        @grpc_action(
            request=[],
            response=BasicProtoListChildSerializer,
            request_name="ReqNameRequest",
            use_response_list=True,
            use_request_list=True,
        )
        async def BasicList(self, request, context):
            ...

        @grpc_action(
            request="google.protobuf.Struct",
            use_request_list=True,
        )
        async def ImportedReq(self, request, context):
            ...

        @grpc_action(
            request=[{"name": "optional_title", "type": "optional string"}],
            response=MySerializer,
        )
        async def Optional(self, request, context):
            ...

    def test_register_action_list(self):
        proto_rpc = self.MyAction.BasicList.make_proto_rpc("BasicList", self.MyAction)

        response = proto_rpc.response

        assert response.name == "BasicProtoListChildListResponse"
        assert response["results"].field_type.name == "BasicProtoListChildResponse"

        request = proto_rpc.request

        assert request.name == "ReqNameListRequest"
        assert request["results"].field_type.name == "ReqNameRequest"

    def test_register_action_list_imported(self):
        proto_rpc = self.MyAction.ImportedReq.make_proto_rpc("ImportedReq", self.MyAction)

        request = proto_rpc.request

        assert request.name == "MyActionImportedReqListRequest"

    def test_register_action_with_optional(self):
        proto_rpc = self.MyAction.Optional.make_proto_rpc("Optional", self.MyAction)

        request = proto_rpc.request
        response = proto_rpc.response

        assert request["optional_title"].cardinality == FieldCardinality.OPTIONAL
        assert response["optional_field"].cardinality == FieldCardinality.OPTIONAL
