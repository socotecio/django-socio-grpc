from datetime import datetime
from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action
from fakeapp.models import UnitTestModel
from fakeapp.serializers import UnitTestModelSerializer, UnitTestModelListExtraArgsSerializer
from django_filters.rest_framework import DjangoFilterBackend


class UnitTestModelService(generics.ModelService, mixins.StreamModelMixin):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title", "text"]

    @grpc_action(request=[{"name": "archived", "type": "bool"}], response=UnitTestModelListExtraArgsSerializer)
    def ListWithExtraArgs(self, request, context):
        # INFO - AM - 14/01/2022 - archived is an extra args in the custom request
        print(request.archived)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            # INFO - AM - 14/01/2022 - query_fetched_datetime is an extra args in the custom request
            serializer = UnitTestModelListExtraArgsSerializer(data={"results": page, "query_fetched_datetime": datetime.now(), "count": self.paginator.page.paginator.count})
            return serializer.message
        else:
            serializer = self.get_serializer(data={"results": page, "query_fetched_datetime": datetime.now(), "count": 0})
            return serializer.message

class AsyncUnitTestModelService(generics.AsyncModelService, mixins.AsyncStreamModelMixin):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title", "text"]

    @grpc_action(request=[{"name": "archived", "type": "bool"}], response=UnitTestModelListExtraArgsSerializer)
    async def ListWithExtraArgs(self, request, context):
        # INFO - AM - 14/01/2022 - archived is an extra args in the custom request
        print(request.archived)
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            # INFO - AM - 14/01/2022 - query_fetched_datetime is an extra args in the custom request
            serializer = UnitTestModelListExtraArgsSerializer(data={"results": page, "query_fetched_datetime": datetime.now(), "count": self.paginator.page.paginator.count})
            return serializer.message
        else:
            serializer = self.get_serializer(data={"results": page, "query_fetched_datetime": datetime.now(), "count": 0})
            return serializer.message