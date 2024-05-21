from django.utils.translation import gettext as _
from fakeapp.grpc import fakeapp_pb2
from fakeapp.serializers import (
    BaseProtoExampleSerializer,
    BasicProtoListChildSerializer,
    BasicServiceSerializer,
    NoMetaSerializer,
)

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.protobuf.generation_plugin import (
    ListGenerationPlugin,
)

from .basic_mixins import ListIdsMixin, ListNameMixin


class BasicService(ListIdsMixin, ListNameMixin, generics.AsyncCreateService):
    serializer_class = BasicServiceSerializer

    def _before_registration(service_class):
        service_class._list_name_response = [
            {"name": "name", "cardinality": "repeated", "type": "string"}
        ]

    @grpc_action(
        request=[{"name": "user_name", "type": "string"}],
        response=BasicServiceSerializer,
    )
    async def FetchDataForUser(self, request, context):
        # INFO - AM - 14/01/2022 - Do something here as filter user with the user name

        user_data = {
            "email": context.user.email if context.user else "fake_email@email.com",
            "birth_date": "25/01/1996",
            "slogan": "Do it better",
        }

        serializer = BasicServiceSerializer(
            {
                "user_name": request.user_name,
                "user_data": user_data,
                "bytes_example": b"test",
                "list_of_dict": [{"test": "test"}],
            }
        )
        return serializer.message

    @grpc_action(
        request=[],
        response="google.protobuf.Empty",
    )
    async def TestEmptyMethod(self, request, context): ...

    @grpc_action(
        request=[],
        response=BasicServiceSerializer,
        use_generation_plugins=[ListGenerationPlugin(response=True)],
    )
    async def GetMultiple(self, request, context):
        # INFO - AM - 14/01/2022 - Do something here as filter user with the user name
        user_datas = [
            {
                "user_name": "fake",
                "user_data": {
                    "email": "fake_email@email.com",
                    "birth_date": "25/01/1996",
                    "slogan": "Do it better",
                },
                "bytes_example": b"test",
                "list_of_dict": [],
            },
            {
                "user_name": "fake2",
                "user_data": {
                    "email": "fake_email2@email.com",
                    "birth_date": "25/01/1996",
                    "slogan": "Do it better2",
                },
                "bytes_example": b"test",
                "list_of_dict": [],
            },
        ]

        serializer = BasicServiceSerializer(user_datas, many=True)
        return serializer.message

    @grpc_action(
        request=[{"name": "user_name", "type": "string", "comment": "@test=in_decorator"}],
        response=[{"name": "user_name", "type": "string"}],
        request_name="CustomNameForRequest",
        response_name="CustomNameForResponse",
    )
    async def MyMethod(self, request, context):
        pass

    @grpc_action(
        request=[{"name": "user_name", "type": "string"}],
        response=[{"name": "user_name", "type": "string"}],
        request_name="CustomMixParamForRequest",
        use_generation_plugins=[ListGenerationPlugin(request=True, response=True)],
    )
    async def MixParam(self, request, context):
        pass

    @grpc_action(
        request=BasicServiceSerializer,
        response="google.protobuf.Struct",
        request_name="BasicParamWithSerializerRequest",
        use_generation_plugins=[ListGenerationPlugin(request=True, response=True)],
    )
    async def MixParamWithSerializer(self, request, context):
        pass

    @grpc_action(
        request=BaseProtoExampleSerializer,
        response=BaseProtoExampleSerializer,
        use_generation_plugins=[ListGenerationPlugin(response=True)],
    )
    async def TestBaseProtoSerializer(self, request, context):
        pass

    @grpc_action(
        request=BasicProtoListChildSerializer,
        response=BasicProtoListChildSerializer,
        use_generation_plugins=[ListGenerationPlugin(request=True, response=True)],
    )
    async def BasicList(self, request, context):
        serializer = BasicProtoListChildSerializer(message=request, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.message

    @grpc_action(
        request=[],
        response=[{"name": "text", "type": "string"}],
    )
    async def FetchTranslatedKey(self, request, context):
        # INFO - AM - 14/04/2023 - Test translation here
        message = fakeapp_pb2.BasicFetchTranslatedKeyResponse(text=_("Test translation"))
        return message

    @grpc_action(
        request=NoMetaSerializer,
        response=[{"name": "value", "type": "string"}],
    )
    async def TestNoMetaSerializer(self, request, context):
        serializer = NoMetaSerializer(message=request)
        serializer.is_valid(raise_exception=True)
        return fakeapp_pb2.BasicTestNoMetaSerializerResponse(value=serializer.data["my_field"])
