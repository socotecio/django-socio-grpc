from enum import Enum
from typing import Annotated

from fakeapp.grpc import fakeapp_pb2

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.tests.fakeapp.models import EnumModel
from django_socio_grpc.tests.fakeapp.serializers import EnumServiceSerializer


class MyGRPCActionEnum(Enum):
    """
    This is my GRPC Action Enum
    """

    VALUE_1: Annotated[int, ["This is value 1"]] = 1
    VALUE_2 = 2


class EnumService(generics.AsyncCreateService):
    serializer_class = EnumServiceSerializer
    queryset = EnumModel.objects.all()

    @grpc_action(
        request=[{"name": "enum_example", "type": MyGRPCActionEnum}],
        response=[{"name": "value", "type": "string"}],
    )
    async def TestEnum(self, request, context):
        return fakeapp_pb2.BasicTestEnumResponse(value="test")
