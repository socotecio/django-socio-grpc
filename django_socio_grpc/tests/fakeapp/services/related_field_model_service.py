from fakeapp.models import RelatedFieldModel
from fakeapp.serializers import RelatedFieldModelSerializer, SimpleRelatedFieldModelSerializer

from django_socio_grpc import generics


class RelatedFieldModelService(generics.AsyncModelService):
    queryset = RelatedFieldModel.objects.all().order_by("uuid")
    serializer_class = RelatedFieldModelSerializer


class SimpleRelatedFieldModelService(generics.AsyncModelService):
    queryset = RelatedFieldModel.objects.all().order_by("uuid")
    serializer_class = SimpleRelatedFieldModelSerializer
