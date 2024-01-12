from fakeapp.models import DefaultValueModel
from fakeapp.serializers import DefaultValueSerializer

from django_socio_grpc import generics


class DefaultValueService(generics.AsyncModelService):
    queryset = DefaultValueModel.objects.all().order_by("id")
    serializer_class = DefaultValueSerializer
