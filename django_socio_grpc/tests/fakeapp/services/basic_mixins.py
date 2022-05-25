
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.grpc_action import GRPCActionMixin

class ListIdsMixin(GRPCActionMixin, abstract=True):

    @grpc_action(
        request=[],
        response=[{"name": "ids", "type": "repeated int"}]
    )
    async def ListIds(self, request, context):
      pass


class ListNameMixin(GRPCActionMixin, abstract=True):

    @grpc_action(
        request=[],
        response=[{"name": "name", "type": "repeated string"}]
    )
    async def ListName(self, request, context):
      pass
