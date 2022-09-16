from typing import Dict, List

import fakeapp.grpc.fakeapp_pb2 as fakeapp_pb2
from rest_framework import serializers

from django_socio_grpc import proto_serializers
from django_socio_grpc.utils.tools import ProtoComment

from .models import (
    ForeignModel,
    ImportStructEvenInArrayModel,
    ManyManyModel,
    RelatedFieldModel,
    SpecialFieldsModel,
    UnitTestModel,
)


class ForeignModelRetrieveCustomProtoSerializer(proto_serializers.ProtoSerializer):

    name = serializers.CharField()
    custom = serializers.SerializerMethodField()

    def get_custom(self, obj) -> str:
        return f"{obj.uuid} - {obj.name}"

    class Meta:
        model = ForeignModel
        proto_class = fakeapp_pb2.ForeignModelRetrieveCustomResponse
        fields = ["uuid", "name"]


class ForeignModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = ForeignModel
        proto_class = fakeapp_pb2.ForeignModelResponse
        proto_class_list = fakeapp_pb2.ForeignModelListResponse
        fields = "__all__"


class UnitTestModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = UnitTestModel
        proto_class = fakeapp_pb2.UnitTestModelResponse
        proto_class_list = fakeapp_pb2.UnitTestModelListResponse
        fields = ("id", "title", "text")


class UnitTestModelListExtraArgsSerializer(proto_serializers.ProtoSerializer):
    count = serializers.IntegerField()
    query_fetched_datetime = serializers.DateTimeField()
    results = UnitTestModelSerializer(many=True)

    class Meta:
        proto_class = fakeapp_pb2.UnitTestModelListExtraArgsResponse


class ManyManyModelSerializer(proto_serializers.ModelProtoSerializer):

    test_write_only_on_nested = serializers.CharField(write_only=True)

    class Meta:
        model = ManyManyModel
        proto_class = fakeapp_pb2.ManyManyModelResponse
        fields = ["uuid", "name", "test_write_only_on_nested"]


class RelatedFieldModelSerializer(proto_serializers.ModelProtoSerializer):
    foreign_obj = ForeignModelSerializer(read_only=True)
    many_many_obj = ManyManyModelSerializer(many=True)

    slug_test_model = serializers.SlugRelatedField(slug_field="special_number", read_only=True)
    slug_reverse_test_model = serializers.SlugRelatedField(
        slug_field="is_active", read_only=True
    )
    slug_many_many = serializers.SlugRelatedField(slug_field="name", read_only=True, many=True)

    custom_field_name = serializers.CharField()

    class Meta:
        model = RelatedFieldModel
        proto_class = fakeapp_pb2.RelatedFieldModelResponse
        proto_class_list = fakeapp_pb2.RelatedFieldModelListResponse
        message_list_attr = "list_custom_field_name"
        fields = "__all__"


class SpecialFieldsModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        proto_comment = ProtoComment(["Special Fields Model", "with two lines comment"])
        model = SpecialFieldsModel
        proto_class = fakeapp_pb2.SpecialFieldsModelResponse
        proto_class_list = fakeapp_pb2.SpecialFieldsModelListResponse
        fields = "__all__"


class ImportStructEvenInArrayModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = ImportStructEvenInArrayModel
        proto_class = fakeapp_pb2.ImportStructEvenInArrayModelResponse
        fields = "__all__"


class CustomRetrieveResponseSpecialFieldsModelSerializer(
    proto_serializers.ModelProtoSerializer
):

    default_method_field = serializers.SerializerMethodField()

    custom_method_field = serializers.SerializerMethodField(method_name="custom_method")

    def get_default_method_field(self, obj) -> int:
        return 3

    def custom_method(self, obj) -> List[Dict]:
        return [{"test": "test"}]

    class Meta:
        proto_comment = "Test comment for whole message"
        model = SpecialFieldsModel
        proto_class = fakeapp_pb2.RelatedFieldModelResponse
        fields = ["uuid", "default_method_field", "custom_method_field"]


class BasicServiceSerializer(proto_serializers.ProtoSerializer):

    user_name = serializers.CharField(
        help_text=ProtoComment(["@test=comment1", "@test2=comment2"])
    )
    user_data = serializers.DictField(help_text=ProtoComment("@test=test_in_serializer"))
    user_password = serializers.CharField(
        write_only=True, help_text="not showing in proto comment"
    )
    bytes_example = proto_serializers.BinaryField()
    list_of_dict = serializers.ListField(child=serializers.DictField())

    class Meta:
        proto_class = fakeapp_pb2.BasicServiceResponse
        proto_class_list = fakeapp_pb2.BasicServiceListResponse
        fields = ["user_name", "user_data", "user_password", "bytes_example", "list_of_dict"]


class BaseProtoExampleSerializer(proto_serializers.BaseProtoSerializer):
    def to_representation(self, el):
        return {
            "uuid": str(el.uuid),
            "number_of_elements": el.number_of_elements,
            "is_archived": el.is_archived,
        }

    def to_proto_message(self):
        return [
            {"name": "uuid", "type": "string"},
            {"name": "number_of_elements", "type": "int32"},
            {"name": "is_archived", "type": "bool"},
        ]

    class Meta:
        pass
        proto_class = fakeapp_pb2.BaseProtoExampleResponse
        proto_class_list = fakeapp_pb2.BaseProtoExampleListResponse


class BasicListProtoSerializer(proto_serializers.ListProtoSerializer):
    pass


class BasicProtoListChildSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = UnitTestModel
        proto_class = fakeapp_pb2.BasicProtoListChildResponse
        proto_class_list = fakeapp_pb2.BasicProtoListChildListResponse
        list_serializer_class = BasicListProtoSerializer
        fields = "__all__"
