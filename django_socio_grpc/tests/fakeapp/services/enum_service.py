from typing import Annotated

from django.db import models
from fakeapp.grpc import fakeapp_pb2

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.tests.fakeapp.models import EnumModel
from django_socio_grpc.tests.fakeapp.serializers import EnumServiceSerializer


class MyGRPCActionEnum(models.TextChoices):
    """
    This is my GRPC Action Enum
    """

    VALUE_1: Annotated[tuple, ["This is value 1"]] = "VALUE_1", "readable 1"
    VALUE_2 = "VALUE_2", "readable 2"


from rest_framework import serializers
class EnumService(generics.GenericService):
    serializer_class = EnumServiceSerializer
    queryset = EnumModel.objects.all()

    @grpc_action(
        request=[{"name": "enum_example", "type": MyGRPCActionEnum}],
        response=[{"name": "value", "type": "string"}],
    )
    async def BasicEnumRequest(self, request, context):
        return fakeapp_pb2.EnumBasicEnumRequestResponse(value="test")

    @grpc_action(
        request=EnumServiceSerializer,
        response=EnumServiceSerializer,
    )
    async def BasicEnumRequestWithSerializer(self, request, context):
        serializer = EnumServiceSerializer(message=request)
        serializer.is_valid(raise_exception=True)
        return serializer.message
