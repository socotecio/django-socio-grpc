from django_socio_grpc import generics, mixins
from fakeapp.models import ImportStructEvenInArrayModel
from fakeapp.serializers import ImportStructEvenInArrayModelSerializer


class ImportStructEvenInArrayModelService(
    generics.GenericService, mixins.AsyncCreateModelMixin
):
    queryset = ImportStructEvenInArrayModel.objects.all().order_by("uuid")
    serializer_class = ImportStructEvenInArrayModelSerializer
