from fakeapp.models import ForeignModel
from fakeapp.serializers import (
    ForeignModelRetrieveCustomProtoSerializer,
    ForeignModelSerializer,
)

from django_socio_grpc import generics, mixins


class ForeignModelService(
    generics.GenericService, mixins.AsyncListModelMixin, mixins.AsyncRetrieveModelMixin
):
    queryset = ForeignModel.objects.all().order_by("uuid")
    serializer_class = ForeignModelSerializer
    lookup_field = "name"

    def get_serializer_class(self):
        if self.action == "Retrieve":
            return ForeignModelRetrieveCustomProtoSerializer
        return super().get_serializer_class()
