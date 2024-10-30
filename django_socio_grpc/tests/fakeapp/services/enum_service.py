from typing import Annotated

from django.db import models
from fakeapp.grpc import fakeapp_pb2
from fakeapp.models import EnumModel
from fakeapp.serializers import (
    EnumServiceAnnotatedSerializerSerializer,
    EnumServiceSerializer,
)

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action


class MyGRPCActionEnum(models.TextChoices):
    """
    This is my GRPC Action Enum
    """

    VALUE_1: Annotated[tuple, ["This is value 1"]] = "VALUE_1", "readable 1"
    VALUE_2 = "VALUE_2", "readable 2"


class EnumService(generics.AsyncCreateService, generics.AsyncRetrieveService):
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
    async def BasicEnumRequestWithAnnotatedModel(self, request, context):
        serializer = EnumServiceSerializer(message=request)
        serializer.is_valid(raise_exception=True)
        return serializer.message

    @grpc_action(
        request=EnumServiceAnnotatedSerializerSerializer,
        response=EnumServiceAnnotatedSerializerSerializer,
    )
    async def BasicEnumRequestWithAnnotatedSerializer(self, request, context):
        serializer = EnumServiceAnnotatedSerializerSerializer(message=request)
        serializer.is_valid(raise_exception=True)
        return serializer.message
