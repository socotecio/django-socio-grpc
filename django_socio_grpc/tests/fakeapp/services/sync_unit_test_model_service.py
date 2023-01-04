from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from fakeapp.models import UnitTestModel
from fakeapp.serializers import UnitTestModelListExtraArgsSerializer, UnitTestModelSerializer

from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action


class SyncUnitTestModelService(generics.ModelService, mixins.StreamModelMixin):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title", "text"]

    @grpc_action(
        request=[{"name": "archived", "type": "bool"}],
        response=UnitTestModelListExtraArgsSerializer,
    )
    def ListWithExtraArgs(self, request, context):
        # INFO - AM - 14/01/2022 - archived is an extra args in the custom request
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        count = 0
        if page is not None:
            queryset = page
            count = self.paginator.page.paginator.count
        # INFO - AM - 14/01/2022 - query_fetched_datetime is an extra args in the custom request
        serializer = UnitTestModelListExtraArgsSerializer(
            {"results": queryset, "query_fetched_datetime": datetime.now(), "count": count}
        )
        return serializer.message
