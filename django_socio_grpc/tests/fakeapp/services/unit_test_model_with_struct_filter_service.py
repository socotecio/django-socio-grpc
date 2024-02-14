from django_filters.rest_framework import DjangoFilterBackend
from fakeapp.models import UnitTestModel
from fakeapp.serializers import UnitTestModelWithStructFilterSerializer
from google.protobuf import empty_pb2

from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action


class UnitTestModelWithStructFilterService(
    generics.AsyncModelService, mixins.AsyncStreamModelMixin
):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelWithStructFilterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title", "text"]
    use_struct_filter_request = True

    @grpc_action(
        request=[],
        response="google.protobuf.Empty",
    )
    async def EmptyWithFilter(self, request, context):
        return empty_pb2.Empty()
