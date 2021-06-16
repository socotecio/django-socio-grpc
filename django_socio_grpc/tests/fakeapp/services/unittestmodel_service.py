from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action
from fakeapp.models import UnitTestModel
from fakeapp.serializers import UnitTestModelSerializer


class UnitTestModelService(generics.ModelService, mixins.StreamModelMixin):
    queryset = UnitTestModel.objects.all().order_by("id")
    serializer_class = UnitTestModelSerializer

    @grpc_action(params="test test")
    def List(self, request, context):
        """
        List a queryset.  This sends a message array of
        ``serializer.Meta.proto_class`` to the client.

        .. note::

            This is a server streaming RPC.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            if hasattr(serializer.message, "count"):
                serializer.message.count = self.paginator.page.paginator.count
            return serializer.message
        else:
            serializer = self.get_serializer(queryset, many=True)
            return serializer.message
