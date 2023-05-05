from django_filters.rest_framework import DjangoFilterBackend
from fakeapp.models import RecursiveTestModel
from fakeapp.serializers import RecursiveTestModelSerializer

from django_socio_grpc import generics


class RecursiveTestModelService(generics.AsyncModelService):
    queryset = RecursiveTestModel.objects.all()
    serializer_class = RecursiveTestModelSerializer
    filter_backends = [DjangoFilterBackend]
