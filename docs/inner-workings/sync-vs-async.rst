.. _sync-vs-async:

Sync VS Async
==============

Introduction
------------

By using Django Socio gRPC you can use both sync and async mode for gRPC.

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
   * - ``django_socio_grpc.mixins.AsyncCreateModelMixin``
     - ``django_socio_grpc.mixins.CreateModelMixin``
   * - ``django_socio_grpc.mixins.AsyncListModelMixin``
     - ``django_socio_grpc.mixins.ListModelMixin``
   * - ``django_socio_grpc.mixins.AsyncStreamModelMixin``
     - ``django_socio_grpc.mixins.StreamModelMixin``
   * - ``django_socio_grpc.mixins.AsyncRetrieveModelMixin``
     - ``django_socio_grpc.mixins.RetrieveModelMixin``
   * - ``django_socio_grpc.mixins.AsyncUpdateModelMixin``
     - ``django_socio_grpc.mixins.UpdateModelMixin``
   * - ``django_socio_grpc.mixins.AsyncPartialUpdateModelMixin``
     - ``django_socio_grpc.mixins.PartialUpdateModelMixin``
   * - ``django_socio_grpc.mixins.AsyncDestroyModelMixin``
     - ``django_socio_grpcmixins.DestroyModelMixin``


Services
--------

All services classes inherit from the same base class **django_socio_grpc.generics.GenericService**.

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Async Class
     - Sync class
   * - ``django_socio_grpc.generics.AsyncCreateService``
     - ``django_socio_grpc.generics.CreateService``
   * - ``django_socio_grpc.generics.AsyncListService``
     - ``django_socio_grpc.generics.ListService``
   * - ``django_socio_grpc.generics.AsyncStreamService``
     - ``django_socio_grpc.generics.StreamService``
   * - ``django_socio_grpc.generics.AsyncRetrieveService``
     - ``django_socio_grpc.generics.RetrieveService``
   * - ``django_socio_grpc.generics.AsyncDestroyService``
     - ``django_socio_grpc.generics.DestroyService``
   * - ``django_socio_grpc.generics.AsyncUpdateService``
     - ``django_socio_grpc.generics.UpdateService``
   * - ``django_socio_grpc.generics.AsyncListCreateService``
     - ``django_socio_grpc.generics.ListCreateService``
   * - ``django_socio_grpc.generics.AsyncReadOnlyModelService``
     - ``django_socio_grpc.generics.ReadOnlyModelService``
   * - ``django_socio_grpc.generics.AsyncModelService``
     - ``django_socio_grpc.generics.class ModelService``

Async ready methods
-------------------

Since Django 4.1, Django can run ORM queries asynchronously.
Check Django `documentation <https://docs.djangoproject.com/en/4.1/topics/async/>`_ for more information.

If you use version of Django < 4.1 or for all django ORM methods not supported,
you can use `asgiref <https://asgi.readthedocs.io/en/latest>`_ to wrap sync methods in async context.

    .. code-block:: python

        from asgiref.sync import sync_to_async
        from buildings.models import Building

        async def a_get(self, pk):
            return await sync_to_async(Building.objects.get)(pk=pk)

In Django Socio gRPC we provide a lot of async ready methods.

#. Services
    * acheck_object_permissions
    * aget_object
    * aget_queryset
    * aget_serializer
#. Serializers
    * asave
    * ais_valid
    * acreate
    * aupdate
    * adata
    * amessage

Sync support
------------

If you want to use the sync mode, you should know that we will no longer support this mode from version 1.0.0 of Django Socio gRPC.