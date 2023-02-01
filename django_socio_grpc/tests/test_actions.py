from asgiref.sync import sync_to_async
from django.test import TestCase

from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.services import Service


class MyService(Service):
    @grpc_action(
        request=[],
        response=[],
    )
    @sync_to_async
    def Action(self, request, context):
        return 1


class TestActions(TestCase):
    async def test_sync_to_async_action(self):
        service = MyService()
        assert (await service.Action(None, None)) == 1
