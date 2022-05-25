from fakeapp.serializers import (
    BaseProtoExampleSerializer,
    BasicProtoListChildSerializer,
    BasicServiceSerializer,
)

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from .basic_mixins import ListIds


class BasicService(generics.GenericService, ListIds):


    # @grpc_action(
    #     request=[],
    #     response=[{"name": "user_name", "type": "MySerializer"}]
    # )
    # async def FetchDataForUser(self, request, context):
    #     super().FetchDataForUser(request, context)

    # my_serializer = TestSerializer

    # def grpc_dict(self):
    #     for responde_item in self._grpc_dict_from_decorators["FetchDataForUser"]["response"]:
    #         if responde_item["name"] == "ids":
    #             responde_item["type"] = self.my_serializer
        
    #     for responde_item in self._grpc_dict_from_decorators["FetchDataForUser2"]["response"]:
    #         if responde_item["name"] == "ids":
    #             responde_item["type"] = self.my_serializer

    #     return self._grpc_dict_from_decorators
    #     return {
    #     "FetchDataForUser": {
    #         "request":[],
    #         "response":[{"name": "ids", "type": self.my_serializer}]
    #     }, **self._grpc_dict_from_decorators
    # }
    pass
    # @grpc_action(
    #     request=[{"name": "user_name", "type": "string"}],
    #     response=BasicServiceSerializer,
    # )
    # async def FetchDataForUser(self, request, context):
    #     # INFO - AM - 14/01/2022 - Do something here as filter user with the user name
    #     print(request.user_name)

    #     user_data = {
    #         "email": "fake_email@email.com",
    #         "birth_date": "25/01/1996",
    #         "slogan": "Do it better",
    #     }

    #     serializer = BasicServiceSerializer(
    #         {
    #             "user_name": request.user_name,
    #             "user_data": user_data,
    #             "bytes_example": b"test",
    #             "list_of_dict": [{"test": "test"}],
    #         }
    #     )
    #     return serializer.message

    # @grpc_action(
    #     request=[],
    #     response="google.protobuf.Empty",
    # )
    # async def TestEmptyMethod(self, request, context):
    #     print("TestEmptyMethod")

    # @grpc_action(request=[], response=BasicServiceSerializer, use_response_list=True)
    # async def GetMultiple(self, request, context):
    #     # INFO - AM - 14/01/2022 - Do something here as filter user with the user name
    #     print(request.user_name)

    #     user_datas = [
    #         {
    #             "user_name": "fake",
    #             "user_data": {
    #                 "email": "fake_email@email.com",
    #                 "birth_date": "25/01/1996",
    #                 "slogan": "Do it better",
    #             },
    #             "bytes_example": b"test",
    #             "list_of_dict": [],
    #         },
    #         {
    #             "user_name": "fake2",
    #             "user_data": {
    #                 "email": "fake_email2@email.com",
    #                 "birth_date": "25/01/1996",
    #                 "slogan": "Do it better2",
    #             },
    #             "bytes_example": b"test",
    #             "list_of_dict": [],
    #         },
    #     ]

    #     serializer = BasicServiceSerializer(user_datas, many=True)
    #     return serializer.message

    # @grpc_action(
    #     request=[{"name": "user_name", "type": "string"}],
    #     response=[{"name": "user_name", "type": "string"}],
    #     request_name="CustomNameForRequest",
    #     response_name="CustomNameForResponse",
    # )
    # async def MyMethod(self, request, context):
    #     pass

    # @grpc_action(
    #     request=[{"name": "user_name", "type": "string"}],
    #     response=[{"name": "user_name", "type": "string"}],
    #     request_name="CustomMixParamForRequest",
    #     use_request_list=True,
    #     use_response_list=True,
    # )
    # async def MixParam(self, request, context):
    #     pass

    # @grpc_action(
    #     request=BasicServiceSerializer,
    #     response="google.protobuf.Struct",
    #     request_name="BasicParamWithSerializerRequest",
    #     use_request_list=True,
    #     use_response_list=True,
    # )
    # async def MixParamWithSerializer(self, request, context):
    #     pass

    # @grpc_action(
    #     request=BaseProtoExampleSerializer,
    #     response=BaseProtoExampleSerializer,
    #     use_response_list=True,
    # )
    # async def TestBaseProtoSerializer(self, request, context):
    #     pass

    # @grpc_action(
    #     request=BasicProtoListChildSerializer,
    #     response=BasicProtoListChildSerializer,
    #     use_response_list=True,
    #     use_request_list=True,
    # )
    # async def BasicList(self, request, context):
    #     serializer = BasicProtoListChildSerializer(message=request, many=True)
    #     serializer.is_valid(raise_exception=True)
    #     return serializer.message
