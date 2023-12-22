.. _sync-vs-async:

Sync VS Async
==============

Introduction
------------

By using DSG you can use both sync and async mode for gRPC. But **sync mode is deprecated** as it can lead to **issue with stream and poor performance**.

Working in sync or async mode makes almost no difference to the way you develop
your APIs. However, there are important differences in the deeper workings of
your API.

Differences
-----------

The main difference is that async mode will allow you to handle many more requests
in some cases. Particularly if you're using streaming, where using sync mode can
block the whole server.

Mixins
------

All mixins classes inherit from the same base class **django_socio_grpc.grpc_actions.actions.GRPCActionMixin**.

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Async Class
     - Sync class
   * - :func:`django_socio_grpc.mixins.AsyncCreateModelMixin`
     - :func:`django_socio_grpc.mixins.CreateModelMixin`
   * - :func:`django_socio_grpc.mixins.AsyncListModelMixin`
     - :func:`django_socio_grpc.mixins.ListModelMixin`
   * - :func:`django_socio_grpc.mixins.AsyncStreamModelMixin`
     - :func:`django_socio_grpc.mixins.StreamModelMixin`
   * - :func:`django_socio_grpc.mixins.AsyncRetrieveModelMixin`
     - :func:`django_socio_grpc.mixins.RetrieveModelMixin`
   * - :func:`django_socio_grpc.mixins.AsyncUpdateModelMixin`
     - :func:`django_socio_grpc.mixins.UpdateModelMixin`
   * - :func:`django_socio_grpc.mixins.AsyncPartialUpdateModelMixin`
     - :func:`django_socio_grpc.mixins.PartialUpdateModelMixin`
   * - :func:`django_socio_grpc.mixins.AsyncDestroyModelMixin`
     - :func:`django_socio_grpcmixins.DestroyModelMixin`


Services
--------

All services classes inherit from the same base class **django_socio_grpc.generics.GenericService**.

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Async Class
     - Sync class
   * - :func:`django_socio_grpc.generics.AsyncCreateService`
     - :func:`django_socio_grpc.generics.CreateService`
   * - :func:`django_socio_grpc.generics.AsyncListService`
     - :func:`django_socio_grpc.generics.ListService`
   * - :func:`django_socio_grpc.generics.AsyncStreamService`
     - :func:`django_socio_grpc.generics.StreamService`
   * - :func:`django_socio_grpc.generics.AsyncRetrieveService`
     - :func:`django_socio_grpc.generics.RetrieveService`
   * - :func:`django_socio_grpc.generics.AsyncDestroyService`
     - :func:`django_socio_grpc.generics.DestroyService`
   * - :func:`django_socio_grpc.generics.AsyncUpdateService`
     - :func:`django_socio_grpc.generics.UpdateService`
   * - :func:`django_socio_grpc.generics.AsyncListCreateService`
     - :func:`django_socio_grpc.generics.ListCreateService`
   * - :func:`django_socio_grpc.generics.AsyncReadOnlyModelService`
     - :func:`django_socio_grpc.generics.ReadOnlyModelService`
   * - :func:`django_socio_grpc.generics.AsyncModelService`
     - :func:`django_socio_grpc.generics.class ModelService`

Async ready methods
-------------------

Since Django 4.1, Django can run Views asynchronously.
Check Django `documentation <https://docs.djangoproject.com/en/4.1/topics/async/>`_ for more information.

If you use version of Django < 4.1 or for all django ORM methods not supported,
you can use `asgiref <https://asgi.readthedocs.io/en/latest>`_ to wrap sync methods in async context.

    .. code-block:: python

        from asgiref.sync import sync_to_async
        from my_app.models import MyModel

        async def aget(self, pk):
            return await sync_to_async(MyModel.objects.get)(pk=pk)

In DSG we provide a lot of async ready methods.

#. :func:`Services<django_socio_grpc.services.base_service.Service>`
    * :func:`acheck_object_permissions<django_socio_grpc.services.base_service.Service.acheck_object_permissions>`
    * :func:`aget_object<django_socio_grpc.services.base_service.Service.aget_object>`
    * :func:`aget_queryset<django_socio_grpc.services.base_service.Service.aget_queryset>`
    * :func:`aget_serializer<django_socio_grpc.services.base_service.Service.aget_serializer>`
#. :func:`Serializers<django_socio_grpc.proto_serializers.BaseProtoSerializer>`
    * :func:`asave<django_socio_grpc.proto_serializers.BaseProtoSerializer.asave>`
    * :func:`ais_valid<django_socio_grpc.proto_serializers.BaseProtoSerializer.ais_valid>`
    * :func:`acreate<django_socio_grpc.proto_serializers.BaseProtoSerializer.acreate>`
    * :func:`aupdate<django_socio_grpc.proto_serializers.BaseProtoSerializer.aupdate>`
    * :func:`adata<django_socio_grpc.proto_serializers.BaseProtoSerializer.adata>`
    * :func:`amessage<django_socio_grpc.proto_serializers.BaseProtoSerializer.amessage>`

Sync support
------------

If you want to use the sync mode, you should know that we are thinking about droping sync support from version 1.0.0 of DSG.
