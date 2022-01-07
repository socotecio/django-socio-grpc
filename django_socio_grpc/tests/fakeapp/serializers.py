import fakeapp.grpc.fakeapp_pb2 as grpc_model
from django_socio_grpc import proto_serializers

from .models import UnitTestModel, ForeignModel, RelatedFieldModel, ManyManyModel

from rest_framework import serializers


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

class ManyManyModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = ManyManyModel
        # proto_class = grpc_model.ManyManyModel
        # proto_class_list = grpc_model.ManyManyModelListResponse
        fields = "__all__"


class RelatedFieldModelSerializer(proto_serializers.ModelProtoSerializer):

    foreign_obj = ForeignModelSerializer(read_only=True)
    many_many_obj = ManyManyModelSerializer(read_only=True, many=True)

    class Meta:
        model = RelatedFieldModel
        # proto_class = grpc_model.RelatedFieldModel
        # proto_class_list = grpc_model.RelatedFieldModelListResponse
        fields = "__all__"