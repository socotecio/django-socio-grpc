from django.core.cache import caches
from django_filters.rest_framework import DjangoFilterBackend
from fakeapp.models import UnitTestModel
from fakeapp.serializers import UnitTestModelWithCacheSerializer
from rest_framework.pagination import PageNumberPagination

from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import (
    cache_endpoint,
    cache_endpoint_with_deleter,
    grpc_action,
    vary_on_metadata,
)
from django_socio_grpc.protobuf.generation_plugin import (
    FilterGenerationPlugin,
    ListGenerationPlugin,
    PaginationGenerationPlugin,
)

second_cache = caches["second"]


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 100


# INFO - AM - 20/02/2024 - This is just for testing the override of FilterGenerationPlugin in proto generation. This filter will not work if FILTER_BEHAVIOR settings not correctly set.
class FilterGenerationPluginForce(FilterGenerationPlugin):
    def check_condition(self, *args, **kwargs) -> bool:
        return True


# INFO - AM - 20/02/2024 - This is just for testing the override of PaginationGenerationPlugin in proto generation. This pagination will not work if PAGINATION_BEHAVIOR settings not correctly set.
class PaginationGenerationPluginForce(PaginationGenerationPlugin):
    def check_condition(self, *args, **kwargs) -> bool:
        return True


class UnitTestModelWithCacheService(generics.AsyncModelService, mixins.AsyncStreamModelMixin):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelWithCacheSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title", "text"]

    def custom_function_not_called_when_cached(self, *args, **kwargs):
        pass

    @grpc_action(
        request=[],
        response=UnitTestModelWithCacheSerializer,
        use_generation_plugins=[
            ListGenerationPlugin(response=True),
        ],
    )
    @cache_endpoint(300)
    @vary_on_metadata("CUSTOM_HEADER")
    async def List(self, request, context):
        self.custom_function_not_called_when_cached(self)
        return await super().List(request, context)

    @grpc_action(
        request=[{"name": "id", "type": "int32"}],
        response=UnitTestModelWithCacheSerializer,
        request_name="UnitTestModelWithCacheRetrieveRequest",
    )
    @cache_endpoint(1000, key_prefix="second", cache="second")
    async def Retrieve(self, request, context):
        return await super().Retrieve(request, context)

    @grpc_action(
        request=[],
        response=UnitTestModelWithCacheSerializer,
        use_generation_plugins=[
            ListGenerationPlugin(response=True),
            FilterGenerationPluginForce(),
            PaginationGenerationPluginForce(),
        ],
    )
    @cache_endpoint(300)
    async def ListWithStructFilter(self, request, context):
        return await super().List(request, context)

    @grpc_action(
        request=[],
        response=UnitTestModelWithCacheSerializer,
        use_generation_plugins=[
            ListGenerationPlugin(response=True),
        ],
    )
    @cache_endpoint(None)
    async def ListWithPossibilityMaxAge(self, request, context):
        """
        Test that if timeout default setting max-age=0 disable cache
        """
        self.custom_function_not_called_when_cached(self)
        return await super().List(request, context)

    @cache_endpoint_with_deleter(300, cache="second")
    @grpc_action(
        request=[],
        response=UnitTestModelWithCacheSerializer,
        use_generation_plugins=[
            ListGenerationPlugin(response=True),
        ],
    )
    async def ListWithAutoCacheCleanOnSaveAndDelete(self, request, context):
        """
        Test the cache_endpoint_with_deleter work well
        """
        self.custom_function_not_called_when_cached(self)
        return await super().List(request, context)

    @cache_endpoint_with_deleter(300, cache="fake_redis")
    @grpc_action(
        request=[],
        response=UnitTestModelWithCacheSerializer,
        use_generation_plugins=[
            ListGenerationPlugin(response=True),
        ],
    )
    async def ListWithAutoCacheCleanOnSaveAndDeleteRedis(self, request, context):
        """
        Test the cache_endpoint_with_deleter work well
        """
        self.custom_function_not_called_when_cached(self)
        return await super().List(request, context)


class UnitTestModelWithCacheInheritService(UnitTestModelWithCacheService):
    pass
