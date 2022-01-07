from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action
from fakeapp.models import ForeignModel
from fakeapp.serializers import ForeignModelSerializer


class ForeignModelService(generics.GenericService, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = ForeignModel.objects.all().order_by("uuid")
    serializer_class = ForeignModelSerializer
