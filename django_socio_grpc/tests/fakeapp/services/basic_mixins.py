from typing import Dict, List

from asgiref.sync import sync_to_async

from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.grpc_actions.actions import GRPCActionMixin
from django_socio_grpc.grpc_actions.placeholders import AttrPlaceholder


class ListIdsMixin(GRPCActionMixin):
    @grpc_action(request=[], response=[{"name": "ids", "type": "repeated int32"}])
    @sync_to_async
    def ListIds(self, request, context):
        pass


class ListNameMixin(GRPCActionMixin):
    _list_name_response: List[Dict[str, str]]

    @grpc_action(request=[], response=AttrPlaceholder("_list_name_response"))
    async def ListName(self, request, context):
        pass
