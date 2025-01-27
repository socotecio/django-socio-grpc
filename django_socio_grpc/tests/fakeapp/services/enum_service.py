from enum import Enum
from typing import Annotated

from django.db.models import TextChoices
from fakeapp.grpc import fakeapp_pb2
from fakeapp.models import EnumModel
from fakeapp.serializers import (
    EnumServiceAnnotatedSerializerSerializer,
    EnumServiceSerializer,
    EnumServiceSerializerOnlyOneField,
)

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.protobuf.generation_plugin import InMessageWrappedEnumGenerationPlugin


class MyGRPCActionEnum(Enum):
    """
    This is my GRPC Action Enum
    """

    VALUE_1: Annotated[tuple, ["This is value 1"]] = "VALUE_1", "readable 1"
    VALUE_2 = "VALUE_2", "readable 2"


class MyGRPCActionTextChoices(TextChoices):
    FIRST_CHOICE = "FIRST_CHOICE", "FIRST_CHOICE"


class EnumService(generics.AsyncCreateService, generics.AsyncRetrieveService):
    serializer_class = EnumServiceSerializer
    queryset = EnumModel.objects.all()

    @grpc_action(
        request=[{"name": "enum", "type": MyGRPCActionEnum}],
        response=[{"name": "enum", "type": MyGRPCActionEnum}],
        use_generation_plugins=[InMessageWrappedEnumGenerationPlugin()],
        override_default_generation_plugins=True,
    )
    async def BasicEnumRequest(self, request, context):
        return fakeapp_pb2.EnumBasicEnumRequestResponse(enum=request.enum)

    @grpc_action(
        request=[{"name": "char_choices", "type": EnumModel.MyTestStrEnum}],
        response=EnumServiceSerializerOnlyOneField,
        use_generation_plugins=[InMessageWrappedEnumGenerationPlugin()],
        override_default_generation_plugins=True,
    )
    async def BasicEnumRequestInSerializerOut(self, request, context):
        data = {"char_choices": request.char_choices}
        # data = {"char_choices": EnumModel.MyTestStrEnum.values[request.char_choices - 1]}
        serializer = EnumServiceSerializerOnlyOneField(data=data)
        serializer.is_valid(raise_exception=True)

        """
        message = EnumServiceOnlyOneFieldResponse(char_choices=request.char_choices)
        return message
        """
        return serializer.message

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
