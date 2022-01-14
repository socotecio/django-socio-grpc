from django_socio_grpc import generics
from fakeapp.models import SpecialFieldsModel
from fakeapp.serializers import SpecialFieldsModelSerializer


class SpecialFieldsModelService(generics.ModelService):
    queryset = SpecialFieldsModel.objects.all().order_by("uuid")
    serializer_class = SpecialFieldsModelSerializer
