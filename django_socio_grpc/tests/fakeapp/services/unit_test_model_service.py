from datetime import datetime

from asgiref.sync import sync_to_async
from django_filters.rest_framework import DjangoFilterBackend
from fakeapp.models import UnitTestModel
from fakeapp.serializers import UnitTestModelListExtraArgsSerializer, UnitTestModelSerializer

from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action


class UnitTestModelService(generics.AsyncModelService, mixins.AsyncStreamModelMixin):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title", "text"]

    @sync_to_async
    def _make(self, queryset, count):
        # INFO - AM - 14/01/2022 - query_fetched_datetime is an extra args in the custom request
        serializer = UnitTestModelListExtraArgsSerializer(
            {"results": queryset, "query_fetched_datetime": datetime.now(), "count": count}
        )
        return serializer.message

    @grpc_action(
        request=[{"name": "archived", "type": "bool"}],
        response=UnitTestModelListExtraArgsSerializer,
    )
    async def ListWithExtraArgs(self, request, context):
        # INFO - AM - 14/01/2022 - archived is an extra args in the custom request
        print(request.archived)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        count = 0
        if page is not None:
            queryset = page
            count = self.paginator.page.paginator.count

        return await self._make(queryset, count)
