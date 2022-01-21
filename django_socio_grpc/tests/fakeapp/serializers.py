import fakeapp.grpc.fakeapp_pb2 as grpc_model
from django_socio_grpc import proto_serializers
from typing import List, Dict

from .models import UnitTestModel, ForeignModel, RelatedFieldModel, ManyManyModel, SpecialFieldsModel, ImportStructEvenInArrayModel

from rest_framework import serializers

class ForeignModelRetrieveRequestCustomSerializer(proto_serializers.ProtoSerializer):

    name = serializers.CharField()

    class Meta:
        model = ForeignModel
        # proto_class = grpc_model.ForeignModel
        fields = ["name"]


class ForeignModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = ForeignModel
        proto_class = grpc_model.ForeignModel
        proto_class_list = grpc_model.ForeignModelListResponse
        fields = "__all__"


class UnitTestModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = UnitTestModel
        proto_class = grpc_model.UnitTestModel
        proto_class_list = grpc_model.UnitTestModelListResponse
        fields = "__all__"

class UnitTestModelListExtraArgsSerializer(proto_serializers.ProtoSerializer):
    count = serializers.IntegerField()
    query_fetched_datetime = serializers.DateTimeField()
    results = UnitTestModelSerializer(many=True)

    class Meta:
        proto_class = grpc_model.UnitTestModelListExtraArgs
        

class ManyManyModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = ManyManyModel
        proto_class = grpc_model.ManyManyModel
        fields = "__all__"


class RelatedFieldModelSerializer(proto_serializers.ModelProtoSerializer):

    foreign_obj = ForeignModelSerializer(read_only=True)
    many_many_obj = ManyManyModelSerializer(read_only=True, many=True)

    custom_field_name = serializers.CharField()

    class Meta:
        model = RelatedFieldModel
        proto_class = grpc_model.RelatedFieldModel
        proto_class_list = grpc_model.RelatedFieldModelListResponse
        message_list_attr = "list_custom_field_name"
        fields = "__all__"

class SpecialFieldsModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = SpecialFieldsModel
        proto_class = grpc_model.SpecialFieldsModel
        proto_class_list = grpc_model.SpecialFieldsModelListResponse
        fields = "__all__"

class ImportStructEvenInArrayModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = ImportStructEvenInArrayModel
        proto_class = grpc_model.ImportStructEvenInArrayModel
        fields = "__all__"

class CustomRetrieveResponseSpecialFieldsModelSerializer(proto_serializers.ModelProtoSerializer):

    default_method_field = serializers.SerializerMethodField()

    custom_method_field = serializers.SerializerMethodField(method_name="custom_method")

    def get_default_method_field(self, obj) -> int:
        return 3

    def custom_method(self, obj) -> List[Dict]:
        return [{"test": "test"}]

    class Meta:
        model = SpecialFieldsModel
        proto_class = grpc_model.RelatedFieldModel
        fields = ["uuid", "default_method_field", "custom_method_field"]