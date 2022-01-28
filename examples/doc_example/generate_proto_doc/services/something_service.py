from django_socio_grpc import generics

from ..models import Something
from ..serializers import SomethingProtoSerializer


class SomethingService(generics.AsyncModelService):
    queryset = Something.objects.all()
    serializer_class = SomethingProtoSerializer
