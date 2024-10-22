from enum import Enum

from fakeapp.grpc import fakeapp_pb2

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.protobuf.proto_classes import ProtoEnum
from django_socio_grpc.tests.fakeapp.serializers import EnumServiceSerializer


class EnumService(generics.AsyncCreateService):
    serializer_class = EnumServiceSerializer

    @grpc_action(
        request=[
            {
                "name": "enum_example",
                "type": ProtoEnum(
                    Enum(
                        "TestEnum",
                        [("VALUE_1", (1, ["This is", "my first value"])), ("VALUE_2", 2)],
                    ),
                    comments=["Test enum comment"],
                ),
            }
        ],
        response=[{"name": "value", "type": "string"}],
    )
    async def TestEnum(self, request, context):
        return fakeapp_pb2.BasicTestEnumResponse(value="test")
