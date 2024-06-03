from fakeapp.grpc import fakeapp_pb2
from fakeapp.models import UnitTestModel

from django_socio_grpc import generics
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.exceptions import NotFound
from django_socio_grpc.protobuf.generation_plugin import ListGenerationPlugin


class StreamInService(generics.GenericService):
    queryset = UnitTestModel.objects.all().order_by("id")

    @grpc_action(
        request=[{"name": "name", "type": "string"}],
        response=[{"name": "count", "type": "int32"}],
        request_stream=True,
        use_generation_plugins=[ListGenerationPlugin(response=True)],
    )
    async def StreamIn(self, request, context):
        messages = [message async for message in request]

        return fakeapp_pb2.StreamInStreamInResponse(count=len(messages))

    @grpc_action(
        request=[{"name": "name", "type": "string"}],
        response=[{"name": "name", "type": "string"}],
        request_stream=True,
        response_stream=True,
    )
    async def StreamToStream(self, request, context):
        async for message in request:
            name = message.name
            if name == "abort":
                raise NotFound()
            yield fakeapp_pb2.StreamInStreamToStreamResponse(name=f"{name}Response")
            if name == "finish":
                break

    @grpc_action(
        request="StreamInStreamToStreamRequest",
        response="StreamInStreamToStreamRequest",
        request_stream=True,
        response_stream=True,
    )
    async def StreamToStreamReadWrite(self, request, context):
        while message := await context.read():
            name = message.name
            if name == "abort":
                raise NotFound()
            await context.write(
                fakeapp_pb2.StreamInStreamToStreamResponse(name=f"{name}Response")
            )
            if name == "finish":
                break
