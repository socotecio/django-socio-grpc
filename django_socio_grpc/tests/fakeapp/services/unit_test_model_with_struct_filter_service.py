from django_filters.rest_framework import DjangoFilterBackend
from fakeapp.models import UnitTestModel
from fakeapp.serializers import UnitTestModelWithStructFilterSerializer
from google.protobuf import empty_pb2
from rest_framework.pagination import PageNumberPagination

from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.protobuf.proto_classes import FieldCardinality, ProtoField


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 100


class UnitTestModelWithStructFilterService(
    generics.AsyncModelService, mixins.AsyncStreamModelMixin
):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelWithStructFilterSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["title", "text"]

    # INFO - AM - 20/02/2024 - This is just for testing the override of get_filter_field in proto generation. This filter will not work if FILTER_BEHAVIOR settings not correctly set.
    @classmethod
    def get_filter_field(cls):
        return ProtoField.from_field_dict(
            {
                "name": "_filters",
                "type": "google.protobuf.Struct",
                "cardinality": FieldCardinality.OPTIONAL,
            }
        )

    # INFO - AM - 20/02/2024 - This is just for testing the override of get_pagination_field in proto generation. This pagination will not work if PAGINATION_BEHAVIOR settings not correctly set.
    @classmethod
    def get_pagination_field(cls):
        return ProtoField.from_field_dict(
            {
                "name": "_pagination",
                "type": "google.protobuf.Struct",
                "cardinality": FieldCardinality.OPTIONAL,
            }
        )

    @grpc_action(
        request=[],
        response="google.protobuf.Empty",
    )
    async def EmptyWithFilter(self, request, context):
        return empty_pb2.Empty()
