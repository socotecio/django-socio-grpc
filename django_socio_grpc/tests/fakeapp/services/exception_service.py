import fakeapp.grpc.fakeapp_pb2 as fakeapp_pb2
from fakeapp.serializers import BasicServiceSerializer

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action


class ExceptionService(generics.GenericService):
    serializer_class = BasicServiceSerializer

    @grpc_action(
        request=[],
        response=[],
    )
    async def UnaryRaiseException(self, request, context):
        test_export_local = "var"
        print(test_export_local)
        raise Exception("test")

    @grpc_action(request=[], response=[{"name": "id", "type": "string"}], response_stream=True)
    async def StreamRaiseException(self, request, context):
        test_export_local = "var"
        print(test_export_local)

        response = fakeapp_pb2.ExceptionStreamRaiseExceptionResponse(id="id-test")
        yield response

        raise Exception("test")
