from datetime import datetime

from asgiref.sync import sync_to_async
from django_filters.rest_framework import DjangoFilterBackend
from fakeapp.models import UnitTestModel
from fakeapp.serializers import (
    UnitTestModelAdminOnlySerializer,
    UnitTestModelListExtraArgsSerializer,
    UnitTestModelSerializer,
)

from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.filters import OrderingFilter
from django_socio_grpc.grpc_actions.utils import (
    get_partial_update_request_from_serializer_class,
)


class UnitTestModelService(generics.AsyncModelService, mixins.AsyncStreamModelMixin):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["title", "text"]
    ordering_fields = [
        "title",
    ]
    ordering = ["-id"]

    def get_serializer_class(self):
        if self.action == "AdminOnlyPartialUpdate":
            return UnitTestModelAdminOnlySerializer
        return self.serializer_class

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
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        count = 0
        if page is not None:
            queryset = page
            count = self.paginator.page.paginator.count

        return await self._make(queryset, count)

    @grpc_action(
        request=get_partial_update_request_from_serializer_class(
            UnitTestModelAdminOnlySerializer
        ),  # this is onlly a tool you can also juste add a _partial_update_fields  = serializers.ListField(child=serializers.CharField(), write_only=True) in the serializer and it will work fine
        response=UnitTestModelAdminOnlySerializer,
    )
    async def AdminOnlyPartialUpdate(self, request, context):
        # BE CAREFUL HERE, IF USING INHERITANCE THE CLASS RETURNED BY get_serializer_class MUST BE THE SAME FOR REQUEST AND RESPONSE
        # Need an other way to differentiate the request and response serializer in DSG that doesn't break DRF compatibility
        # If you really need an other response serializer you can just copy the PartialUpdate method and change the response serializer manually
        return await self.PartialUpdate(request, context)
