import fakeapp.grpc.fakeapp_pb2 as grpc_model
from django_socio_grpc import proto_serializers

from .models import UnitTestModel, ForeignModel

class ForeignModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = ForeignModel
        # proto_class = grpc_model.UnitTestModel
        # proto_class_list = grpc_model.UnitTestModelListResponse
        fields = "__all__"


class UnitTestModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = UnitTestModel
        proto_class = grpc_model.UnitTestModel
        proto_class_list = grpc_model.UnitTestModelListResponse
        fields = "__all__"
