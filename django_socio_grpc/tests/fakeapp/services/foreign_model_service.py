from django_socio_grpc import generics, mixins
from fakeapp.models import ForeignModel
from fakeapp.serializers import (
    ForeignModelRetrieveCustomProtoSerializer,
    ForeignModelSerializer,
)


class ForeignModelService(
    generics.GenericService, mixins.AsyncListModelMixin, mixins.AsyncRetrieveModelMixin
):
    queryset = ForeignModel.objects.all().order_by("uuid")
    serializer_class = ForeignModelSerializer
    lookup_field = "name"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ForeignModelRetrieveCustomProtoSerializer
        return super().get_serializer_class()
