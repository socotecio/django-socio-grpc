from decimal import Decimal
from enum import Enum
from typing import Annotated, Optional
from unittest import mock

import pytest
from django.db import models
from django.test import TestCase, override_settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination

from django_socio_grpc import proto_serializers
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.generics import GenericService
from django_socio_grpc.grpc_actions.actions import GRPCAction
from django_socio_grpc.protobuf import ProtoComment, ProtoRegistrationError
from django_socio_grpc.protobuf.generation_plugin import (
    FilterGenerationPlugin,
    ListGenerationPlugin,
    PaginationGenerationPlugin,
)
from django_socio_grpc.protobuf.message_name_constructor import (
    DefaultMessageNameConstructor,
    MessageNameConstructor,
)
from django_socio_grpc.protobuf.proto_classes import (
    EmptyMessage,
    FieldCardinality,
    ProtoField,
    ProtoMessage,
    RequestProtoMessage,
    ResponseProtoMessage,
    StructMessage,
)
from django_socio_grpc.services import Service
from django_socio_grpc.settings import FilterAndPaginationBehaviorOptions
from django_socio_grpc.tests.fakeapp.models import RelatedFieldModel
from django_socio_grpc.tests.fakeapp.serializers import (
    BasicProtoListChildSerializer,
    BasicServiceSerializer,
    RelatedFieldModelSerializer,
)


class MyIntegerChoices(models.IntegerChoices):
    """
    This is a test enum
    """

    VALUE_1: Annotated[int, ["My comment", "on two lines"]] = 1
    VALUE_2: Annotated[int, "My comment"] = 2
    VALUE_3 = 3


class CustomMessageNameConstructor(DefaultMessageNameConstructor):
    def construct_response_name(self, before_suffix=""):
        name = super().construct_response_name(before_suffix=before_suffix)
        name += "Custom"

        return name


class WrongMessageNameConstructor(MessageNameConstructor):
    pass


class MyPropertyModel(models.Model):
    @property
    def str_property(self) -> str:
        return "str_property"

    @property
    def int_property(self) -> int:
        return 1


class MyPropertySerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = MyPropertyModel
        fields = ["str_property", "int_property"]


class MyIntField(serializers.IntegerField): ...


class MyOtherSerializer(proto_serializers.ProtoSerializer):
    uuid = serializers.UUIDField()
    name = serializers.CharField()


class MySerializer(proto_serializers.ProtoSerializer):
    user_name = MyIntField(help_text=ProtoComment(["@test=comment1", "@test2=comment2"]))
    title = serializers.CharField()
    optional_field = serializers.CharField(allow_null=True)
    default_char = serializers.CharField(default="value")
    list_field = serializers.ListField(child=serializers.CharField())
    list_field_with_serializer = serializers.ListField(child=MyOtherSerializer())

    smf = serializers.SerializerMethodField()
    smf_only_list = serializers.SerializerMethodField()
    smf_with_serializer = serializers.SerializerMethodField()
    smf_with_serializer_pipe = serializers.SerializerMethodField()
    smf_with_list_serializer = serializers.SerializerMethodField()
    smf_with_decimal = serializers.SerializerMethodField()

    read_only_field0 = serializers.CharField(read_only=True)
    read_only_field1 = serializers.CharField(read_only=True)
    write_only_field = serializers.CharField(write_only=True)

    def get_smf(self, obj) -> list[int]: ...

    def get_smf_only_list(self, obj) -> list: ...

    def get_smf_with_serializer(self, obj) -> Optional[BasicServiceSerializer]: ...  # noqa: UP007

    def get_smf_with_serializer_pipe(self, obj) -> BasicServiceSerializer | None: ...

    def get_smf_with_list_serializer(self, obj) -> list[BasicServiceSerializer]: ...  # noqa: UP006

    def get_smf_with_decimal(self, obj) -> Decimal: ...


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
        # INFO - AM - 04/01/2024 - OPTIONAL because slug_test_model can be null in RelatedFieldModel
        assert proto_field.cardinality == FieldCardinality.OPTIONAL
        assert proto_field.comments is None

    def test_from_field_related_field_source(self):
        ser = MyOtherSerializer()
        field = ser.fields["pk_related_source_field"]
        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "pk_related_source_field"
        assert proto_field.field_type == "string"
        # INFO - AM - 04/01/2024 - OPTIONAL because foreign can be null in RelatedFieldModel
        assert proto_field.cardinality == FieldCardinality.OPTIONAL
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

    def test_from_field_serializer_method_field_only_list(self):
        ser = MySerializer()
        field = ser.fields["smf_only_list"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "smf_only_list"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.REPEATED
        assert proto_field.comments is None

    def test_from_field_serializer_method_field_with_serializer(self):
        ser = MySerializer()
        field = ser.fields["smf_with_serializer"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "smf_with_serializer"
        assert proto_field.field_type.name == "BasicServiceResponse"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

    def test_from_field_serializer_method_field_with_serializer_pipe(self):
        ser = MySerializer()
        field = ser.fields["smf_with_serializer_pipe"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "smf_with_serializer_pipe"
        assert proto_field.field_type.name == "BasicServiceResponse"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

    def test_from_field_serializer_method_field_with_list_serializer(self):
        ser = MySerializer()
        field = ser.fields["smf_with_list_serializer"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "smf_with_list_serializer"
        assert proto_field.field_type.name == "BasicServiceResponse"
        assert proto_field.cardinality == FieldCardinality.REPEATED

    def test_from_field_serializer_method_field_with_list_serializer_child_serializer(self):
        ser = MySerializer()
        field = ser.fields["list_field_with_serializer"]

        proto_field = ProtoField.from_field(
            field,
            ProtoMessage.from_serializer,
            parent_serializer=MySerializer,
            name_if_recursive="Fake",
        )

        assert proto_field.name == "list_field_with_serializer"
        assert proto_field.field_type.name == "MyOther"
        assert proto_field.cardinality == FieldCardinality.REPEATED

    def test_from_field_serializer_method_field_with_decimal(self):
        ser = MySerializer()
        field = ser.fields["smf_with_decimal"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "smf_with_decimal"
        assert proto_field.field_type == "double"

    def test_from_property_field(self):
        ser = MyPropertySerializer()
        field = ser.fields["str_property"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "str_property"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.NONE

        field = ser.fields["int_property"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "int_property"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.NONE

    def test_from_field_default(self):
        ser = MySerializer()
        field_char = ser.fields["default_char"]

        proto_field_char = ProtoField.from_field(field_char)

        assert proto_field_char.name == "default_char"
        assert proto_field_char.field_type == "string"
        assert proto_field_char.cardinality == FieldCardinality.OPTIONAL

    def test_from_field_serializer_int_choices(self):
        from django_socio_grpc.tests.test_enum_generation_plugin import MyIntModelSerializer

        ser = MyIntModelSerializer()
        field = ser.fields["choice_field"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "choice_field"
        assert proto_field.field_type == "int32"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

    def test_from_field_serializer_str_choices(self):
        from django_socio_grpc.tests.test_enum_generation_plugin import MyStrModelSerializer

        ser = MyStrModelSerializer()
        field = ser.fields["choice_field"]

        proto_field = ProtoField.from_field(field)

        assert proto_field.name == "choice_field"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.OPTIONAL

    # FROM_SERIALIZER

    def test_from_serializer(self):
        ser = MyOtherSerializer()
        field = ser.fields["serializer"]

        def to_message(serializer_class):
            return serializer_class.__name__

        proto_message = ProtoField.from_serializer(field, to_message)

        assert proto_message.name == "serializer"
        assert proto_message.field_type == "MySerializer"
        assert proto_message.cardinality == FieldCardinality.NONE

    def test_from_list_serializer(self):
        ser = MyOtherSerializer()
        field = ser.fields["serializer_list"]

        def to_message(serializer_class):
            return serializer_class.__name__

        proto_message = ProtoField.from_serializer(field, to_message)

        assert proto_message.name == "serializer_list"
        assert proto_message.field_type == "MySerializer"
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

        field_dict = {
            "name": "title",
            "type": "string",
            "cardinality": "repeated",
            "comment": ["comment0", "comment1"],
        }

        proto_field = ProtoField.from_field_dict(field_dict)

        assert proto_field.name == "title"
        assert proto_field.field_type == "string"
        assert proto_field.cardinality == FieldCardinality.REPEATED
        assert proto_field.comments == ["comment0", "comment1"]

        with pytest.raises(ProtoRegistrationError):
            field_dict = {
                "name": "title",
                "type": "unknown string",
                "comment": ["comment0", "comment1"],
            }

            ProtoField.from_field_dict(field_dict)

    def test_from_field_dict_enum(self):
        field_dict = {
            "name": "my_enum",
            "type": MyIntegerChoices,
            "comment": ["my_enum comment"],
        }

        proto_field = ProtoField.from_field_dict(field_dict)

        assert proto_field.name == "my_enum"
        assert proto_field.cardinality == FieldCardinality.NONE
        assert proto_field.comments == ["my_enum comment"]

        assert issubclass(proto_field.field_type, Enum)
        assert proto_field.field_type.__annotations__[
            MyIntegerChoices.VALUE_1.name
        ].__metadata__[0] == [
            "My comment",
            "on two lines",
        ]
        assert (
            proto_field.field_type.__annotations__[MyIntegerChoices.VALUE_2.name].__metadata__[
                0
            ]
            == "My comment"
        )


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
        proto_message = ProtoMessage.from_serializer(MySerializer, name="My")

        assert proto_message.name == "My"
        assert len(proto_message.fields) == 15

    def test_from_serializer_request(self):
        proto_message = RequestProtoMessage.from_serializer(MySerializer, name="MyRequest")

        assert proto_message.name == "MyRequest"
        assert len(proto_message.fields) == 7

        assert "write_only_field" in proto_message

        proto_message = RequestProtoMessage.from_serializer(MySerializer, "CustomName")

        assert proto_message.name == "CustomName"
        assert len(proto_message.fields) == 7

    def test_from_serializer_response(self):
        proto_message = ResponseProtoMessage.from_serializer(MySerializer, name="MyResponse")

        assert proto_message.name == "MyResponse"
        assert len(proto_message.fields) == 14

    def test_from_serializer_nested(self):
        proto_message = ResponseProtoMessage.from_serializer(
            MyOtherSerializer, name="MyOtherResponse"
        )

        assert proto_message.name == "MyOtherResponse"
        assert len(proto_message.fields) == 4
        assert proto_message.comments == ["serializer comment"]

        assert proto_message.fields[0].name == "serializer"
        assert len(proto_message.fields[0].field_type.fields) == 14


class TestGrpcActionProto(TestCase):
    class MyBaseAction(Service):
        serializer_class = MySerializer
        pagination_class = None

        @grpc_action(
            request=[],
            response=BasicProtoListChildSerializer,
            request_name="ReqNameRequest",
            use_generation_plugins=[ListGenerationPlugin(request=True, response=True)],
        )
        async def BasicList(self, request, context): ...

        @grpc_action(
            request="TestRequest",
            response="TestResponse",
        )
        async def BasicActionWithString(self, request, context): ...

        @grpc_action(
            request="TestRequest",
            response="TestResponse",
            use_generation_plugins=[ListGenerationPlugin(request=True, response=True)],
        )
        async def BasicActionListWithString(self, request, context): ...

        @grpc_action(
            request=[],
            response=BasicProtoListChildSerializer,
            use_generation_plugins=[ListGenerationPlugin(request=True, response=True)],
        )
        async def BasicListArgPlugin(self, request, context): ...

    class MyAction(GenericService):
        serializer_class = MySerializer

        @grpc_action(
            request=[],
            response=BasicProtoListChildSerializer,
            request_name="ReqNameRequest",
            use_generation_plugins=[ListGenerationPlugin(request=True, response=True)],
        )
        async def BasicList(self, request, context): ...

        @grpc_action(
            request=[],
            response=BasicProtoListChildSerializer,
            use_response_list=True,
            use_request_list=True,
        )
        async def BasicListOldCompat(self, request, context): ...

        @grpc_action(
            request="google.protobuf.Struct",
            use_generation_plugins=[ListGenerationPlugin(request=True)],
        )
        async def ImportedReq(self, request, context): ...

        @grpc_action(
            request=[{"name": "optional_title", "type": "optional string"}],
            response=MySerializer,
        )
        async def Optional(self, request, context): ...

        @grpc_action(
            request=[],
            response="google.protobuf.Empty",
        )
        async def EmptyMessages(self, request, context): ...

    class MyActionWithFilter(GenericService):
        serializer_class = MySerializer
        filter_backends = [DjangoFilterBackend]
        filterset_fields = ["title", "text"]

        @grpc_action(
            request=[],
            response=BasicProtoListChildSerializer,
            request_name="ReqNameRequest",
            use_generation_plugins=[
                ListGenerationPlugin(request=True, response=True),
                FilterGenerationPlugin(),
            ],
        )
        async def BasicListWithFilter(self, request, context): ...

        @grpc_action(
            request=[],
            response="google.protobuf.Empty",
            use_generation_plugins=[FilterGenerationPlugin()],
        )
        async def FilterInEmpty(self, request, context): ...

        @grpc_action(
            request=[{"name": "test", "type": "bool"}],
            response="google.protobuf.Empty",
            use_generation_plugins=[FilterGenerationPlugin()],
        )
        async def FilterInRequest(self, request, context): ...

    class MyActionWithPagination(GenericService):
        serializer_class = MySerializer
        pagination_class = PageNumberPagination

        @grpc_action(
            request=[],
            response=BasicProtoListChildSerializer,
            request_name="ReqNameRequest",
            use_generation_plugins=[
                ListGenerationPlugin(request=True, response=True),
                PaginationGenerationPlugin(),
            ],
        )
        async def BasicListWithPagination(self, request, context): ...

        @grpc_action(
            request=[],
            response="google.protobuf.Empty",
            use_generation_plugins=[PaginationGenerationPlugin()],
        )
        async def PaginationInEmpty(self, request, context): ...

        @grpc_action(
            request=[{"name": "test", "type": "bool"}],
            response="google.protobuf.Empty",
            use_generation_plugins=[PaginationGenerationPlugin()],
        )
        async def PaginationInRequest(self, request, context): ...

    def test_instanciate_GRPCAction_with_default_value(self):
        fake_func = mock.Mock()
        grpc_action = GRPCAction(
            function=fake_func,
        )

        self.assertEqual(grpc_action.function, fake_func)

    def test_register_action_on_base_service_list(self):
        proto_rpc = self.MyBaseAction.BasicList.make_proto_rpc("BasicList", self.MyBaseAction)

        response = proto_rpc.response

        assert response.name == "BasicProtoListChildListResponse"
        assert response["results"].field_type.name == "BasicProtoListChildResponse"
        assert "count" not in response

        request = proto_rpc.request

        assert request.name == "ReqNameListRequest"
        assert request["results"].field_type.name == "ReqNameRequest"

    def test_register_action_on_base_service_list_with_arg_plugin(self):
        proto_rpc = self.MyBaseAction.BasicListArgPlugin.make_proto_rpc(
            "BasicListArgPlugin", self.MyBaseAction
        )

        response = proto_rpc.response

        assert response.name == "BasicProtoListChildListResponse"
        assert response["results"].field_type.name == "BasicProtoListChildResponse"

        request = proto_rpc.request

        assert request.name == "MyBaseActionBasicListArgPluginListRequest"
        assert request["results"].field_type.name == "MyBaseActionBasicListArgPluginRequest"

    def test_register_action_on_base_service_with_message_str(self):
        proto_rpc = self.MyBaseAction.BasicActionWithString.make_proto_rpc(
            "BasicActionWithString", self.MyBaseAction
        )

        assert proto_rpc.response == "TestResponse"
        assert proto_rpc.request == "TestRequest"

    def test_register_action_on_base_service_with_message_str_and_list_plugin(self):
        proto_rpc = self.MyBaseAction.BasicActionListWithString.make_proto_rpc(
            "BasicActionListWithString", self.MyBaseAction
        )

        response = proto_rpc.response

        assert response.name == "MyBaseActionBasicActionListWithStringListResponse"
        assert response["results"].field_type == "TestResponse"

        request = proto_rpc.request

        assert request.name == "MyBaseActionBasicActionListWithStringListRequest"
        assert request["results"].field_type == "TestRequest"

    def test_register_action_list_imported(self):
        proto_rpc = self.MyAction.ImportedReq.make_proto_rpc("ImportedReq", self.MyAction)

        request = proto_rpc.request

        assert request.name == "MyActionImportedReqListRequest"

    def test_register_action_list_imported_old_compat(self):
        proto_rpc = self.MyAction.BasicListOldCompat.make_proto_rpc(
            "BasicListOldCompat", self.MyAction
        )

        request = proto_rpc.request

        assert request.name == "MyActionBasicListOldCompatListRequest"

    def test_register_action_with_optional(self):
        proto_rpc = self.MyAction.Optional.make_proto_rpc("Optional", self.MyAction)

        request = proto_rpc.request
        response = proto_rpc.response

        assert request["optional_title"].cardinality == FieldCardinality.OPTIONAL
        assert response["optional_field"].cardinality == FieldCardinality.OPTIONAL

    def test_register_action_with_empty(self):
        proto_rpc = self.MyAction.EmptyMessages.make_proto_rpc("EmptyMessages", self.MyAction)

        request = proto_rpc.request
        response = proto_rpc.response

        assert request is EmptyMessage
        assert response is EmptyMessage

    # TESTING STRUCT FILTER #########################
    @override_settings(
        GRPC_FRAMEWORK={
            "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
            "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
        }
    )
    def test_register_action_empty_message_with_struct_filters(self):
        proto_rpc = self.MyActionWithFilter.FilterInEmpty.make_proto_rpc(
            "FilterInEmpty", self.MyActionWithFilter
        )

        request = proto_rpc.request
        response = proto_rpc.response

        assert request.name == "MyActionWithFilterFilterInEmptyRequest"
        assert request["_filters"].cardinality == FieldCardinality.OPTIONAL
        assert request["_filters"].field_type.name == "google.protobuf.Struct"

        assert response is EmptyMessage

    @override_settings(
        GRPC_FRAMEWORK={
            "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
            "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
        }
    )
    def test_register_action_list_with_struct_filters(self):
        proto_rpc = self.MyActionWithFilter.BasicListWithFilter.make_proto_rpc(
            "BasicListWithFilter", self.MyActionWithFilter
        )

        response = proto_rpc.response

        assert response.name == "BasicProtoListChildListResponse"
        assert response["results"].field_type.name == "BasicProtoListChildResponse"

        request = proto_rpc.request

        assert request.name == "ReqNameListRequest"
        assert request["results"].field_type.name == "ReqNameRequest"
        assert request["_filters"].cardinality == FieldCardinality.OPTIONAL
        assert request["_filters"].field_type.name == "google.protobuf.Struct"

    @override_settings(
        GRPC_FRAMEWORK={
            "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
            "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
        }
    )
    def test_register_action_with_struct_filters(self):
        proto_rpc = self.MyActionWithFilter.FilterInRequest.make_proto_rpc(
            "FilterInRequest", self.MyActionWithFilter
        )

        request = proto_rpc.request
        response = proto_rpc.response

        assert request.name == "MyActionWithFilterFilterInRequest"
        assert len(request.fields) == 2
        assert request["_filters"].cardinality == FieldCardinality.OPTIONAL
        assert request["_filters"].field_type.name == "google.protobuf.Struct"
        assert "test" in request

        assert response is EmptyMessage

    # TESTING STRUCT PAGINATION #########################
    @override_settings(
        GRPC_FRAMEWORK={
            "PAGINATION_BEHAVIOR": FilterAndPaginationBehaviorOptions.METADATA_AND_REQUEST_STRUCT,
            "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        }
    )
    def test_register_action_empty_message_with_struct_pagination(self):
        proto_rpc = self.MyActionWithPagination.PaginationInEmpty.make_proto_rpc(
            "PaginationInEmpty", self.MyActionWithPagination
        )

        request = proto_rpc.request
        response = proto_rpc.response

        assert request.name == "MyActionWithPaginationPaginationInEmptyRequest"
        assert request["_pagination"].cardinality == FieldCardinality.OPTIONAL
        assert request["_pagination"].field_type.name == "google.protobuf.Struct"

        assert response is EmptyMessage

    @override_settings(
        GRPC_FRAMEWORK={
            "PAGINATION_BEHAVIOR": FilterAndPaginationBehaviorOptions.METADATA_AND_REQUEST_STRUCT,
            "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        }
    )
    def test_register_action_list_with_struct_pagination(self):
        proto_rpc = self.MyActionWithPagination.BasicListWithPagination.make_proto_rpc(
            "BasicListWithPagination", self.MyActionWithPagination
        )

        response = proto_rpc.response

        assert response.name == "BasicProtoListChildListResponse"
        assert response["results"].field_type.name == "BasicProtoListChildResponse"
        assert "count" in response
        assert response["count"].field_type == "int32"

        request = proto_rpc.request

        assert request.name == "ReqNameListRequest"
        assert request["results"].field_type.name == "ReqNameRequest"
        assert request["_pagination"].cardinality == FieldCardinality.OPTIONAL
        assert request["_pagination"].field_type.name == "google.protobuf.Struct"

    @override_settings(
        GRPC_FRAMEWORK={
            "PAGINATION_BEHAVIOR": FilterAndPaginationBehaviorOptions.METADATA_AND_REQUEST_STRUCT,
            "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        }
    )
    def test_register_action_with_struct_pagination(self):
        proto_rpc = self.MyActionWithPagination.PaginationInRequest.make_proto_rpc(
            "PaginationInRequest", self.MyActionWithPagination
        )

        request = proto_rpc.request
        response = proto_rpc.response

        assert request.name == "MyActionWithPaginationPaginationInRequest"
        assert len(request.fields) == 2
        assert request["_pagination"].cardinality == FieldCardinality.OPTIONAL
        assert request["_pagination"].field_type.name == "google.protobuf.Struct"
        assert "test" in request

        assert response is EmptyMessage

    # TEST WITH PLUGIN GLOBAL SETTINGS ##############
    @override_settings(
        GRPC_FRAMEWORK={
            "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
            "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
            "DEFAULT_GENERATION_PLUGINS": [FilterGenerationPlugin()],
        }
    )
    def test_register_action_with_default_generation_plugins(self):
        # INFO - AM - 23/02/2024 - Need to declare action in test because settings only overrided in the test
        class MyActionBis(GenericService):
            serializer_class = MySerializer

            @grpc_action(
                request=[{"name": "optional_title", "type": "optional string"}],
                response=MySerializer,
            )
            async def Optional(self, request, context): ...

        proto_rpc = MyActionBis.Optional.make_proto_rpc("Optional", MyActionBis)

        request = proto_rpc.request
        assert "_filters" in request

    # TEST WITH MESSAGE NAME CONSTRUCTOR GLOBAL SETTINGS ##############
    @override_settings(
        GRPC_FRAMEWORK={
            "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
            "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
            "DEFAULT_MESSAGE_NAME_CONSTRUCTOR": "django_socio_grpc.tests.test_protobuf_registration.CustomMessageNameConstructor",
        }
    )
    def test_register_action_with_default_message_name_constructor(self):
        # INFO - AM - 23/02/2024 - Need to declare action in test because settings only overrided in the test
        class MyActionBis(GenericService):
            serializer_class = MySerializer

            @grpc_action(
                request=[{"name": "optional_title", "type": "optional string"}],
                response=MySerializer,
            )
            async def Optional(self, request, context): ...

        proto_rpc = MyActionBis.Optional.make_proto_rpc("Optional", MyActionBis)

        assert proto_rpc.response.name == "MyResponseCustom"

    @override_settings(
        GRPC_FRAMEWORK={
            "FILTER_BEHAVIOR": FilterAndPaginationBehaviorOptions.REQUEST_STRUCT_STRICT,
            "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
            "DEFAULT_MESSAGE_NAME_CONSTRUCTOR": "django_socio_grpc.tests.test_protobuf_registration.WrongMessageNameConstructor",
        }
    )
    def test_register_action_with_wrong_message_name_constructor(self):
        # INFO - AM - 23/02/2024 - Need to declare action in test because settings only overrided in the test
        class MyActionBis(GenericService):
            serializer_class = MySerializer

            @grpc_action(
                request=[{"name": "optional_title", "type": "optional string"}],
                response=MySerializer,
            )
            async def Optional(self, request, context): ...

        with self.assertRaises(TypeError):
            MyActionBis.Optional.make_proto_rpc("Optional", MyActionBis)
