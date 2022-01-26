from django_socio_grpc import proto_serializers

from .models import Something

# import testgrpc.grpc.testgrpc_pb2 as testgrpc_pb2



class SomethingProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = Something
        # proto_class = testgrpc_pb2.Something
        # proto_class_list = testgrpc_pb2.SomethingListResponse
        fields = ["uuid", "start_date", "rate"]
