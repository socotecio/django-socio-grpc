from enum import Enum
from typing import Annotated

from fakeapp.grpc import fakeapp_pb2

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.tests.fakeapp.models import EnumModel
from django_socio_grpc.tests.fakeapp.serializers import EnumServiceSerializer
from django.db import models

class MyGRPCActionEnum(models.IntegerChoices):
    """
    This is my GRPC Action Enum
    """

    VALUE_1: Annotated[int, ["This is value 1"]] = 1
    VALUE_2 = 2


class EnumService(generics.GenericService):
    serializer_class = EnumServiceSerializer
    queryset = EnumModel.objects.all()

    @grpc_action(
        request=[{"name": "enum_example", "type": MyGRPCActionEnum}],
        response=[{"name": "value", "type": "string"}],
    )
    async def BasicEnumRequest(self, request, context):
        return fakeapp_pb2.BasicEnumRequestResponse(value="test")

    @grpc_action(
        request=EnumServiceSerializer,
        response=EnumServiceSerializer,
    )
    async def BasicEnumRequestWithSerializer(self, request, context):
        serializer = EnumServiceSerializer(message=request)
        serializer.is_valid(raise_exception=True)
        return serializer.message
