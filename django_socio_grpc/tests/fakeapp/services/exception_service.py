import fakeapp.grpc.fakeapp_pb2 as fakeapp_pb2
from fakeapp.serializers import BasicServiceSerializer
from rest_framework.exceptions import ValidationError

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.exceptions import NotFound


class ExceptionService(generics.GenericService):
    serializer_class = BasicServiceSerializer

    @grpc_action(
        request=[],
        response=[],
    )
    async def UnaryRaiseException(self, request, context):
        raise Exception("test")

    @grpc_action(request=[], response=[{"name": "id", "type": "string"}], response_stream=True)
    async def StreamRaiseException(self, request, context):
        response = fakeapp_pb2.ExceptionStreamRaiseExceptionResponse(id="id-test")
        yield response

        raise Exception("test")

    @grpc_action(request=[], response=[])
    async def APIException(self, request, context):
        raise ValidationError({"test": "test"})

    @grpc_action(request=[], response=[])
    async def GRPCException(self, request, context):
        raise NotFound()
