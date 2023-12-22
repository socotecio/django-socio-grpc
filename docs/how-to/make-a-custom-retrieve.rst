.. _make-a-custom-retrieve:

Make a custom retrieve
=======================

Description
-----------

A custom retrieve is a request to get an object by searching on one or several fields instead of just the primary key.

Updating the lookup_field
-------------------------

The ``lookup_field`` is the **field where the retrieve will use to fetch element from database**, the original field is the pk field.
You can update this field in the service

.. code-block:: python

    from django_socio_grpc import generics, mixins

    class MyModelService(
        generics.GenericService, mixins.AsyncListModelMixin, mixins.AsyncRetrieveModelMixin
    ):
        # MyModel is your own model defined in your app
        queryset = MyModel.objects.all().order_by("pk")
        # MyModelSerializer is your own model defined in your app
        serializer_class = MyModelSerializer
        lookup_field = "name"


Overriding the retrieve
-----------------------

Another way to make a custom retrieve is to **override the** ``Retrieve`` **action**.

.. code-block:: python

    from django_socio_grpc import generics
    from django_socio_grpc.decorators import grpc_action

    class MyModelService(generics.AsyncModelService):
        # MyModel is your own model defined in your app
        queryset = MyModel.objects.all().order_by("pk")
        # MyModelSerializer is your own model defined in your app
        serializer_class = MyModelSerializer

        @grpc_action(
            request=[{"name": "uuid", "type": "string"}],
            response=MyModelSerializer,
        )
        async def Retrieve(self, request, context):
            instance = self.get_object()
            return await MyModelSerializer(instance).amessage


Retrieve a custom object
------------------------

If you need a custom object to get more or less field on the object you can pass a **custom serializer on the response**.

.. code-block:: python

    from django_socio_grpc import generics
    from django_socio_grpc.decorators import grpc_action

    class MyModelService(generics.AsyncModelService):
        # MyModel is your own model defined in your app
        queryset = MyModel.objects.all().order_by("pk")
        # MyModelSerializer is your own model defined in your app
        serializer_class = MyModelSerializer

        @grpc_action(
            request=[{"name": "uuid", "type": "string"}],
            # CustomRetrieveResponseMyModelSerializer is your own serializer to specify the field the retrieve should get
            response=CustomRetrieveResponseMyModelSerializer,
        )
        async def Retrieve(self, request, context):
            instance = self.get_object()
            # CustomRetrieveResponseMyModelSerializer is your own serializer to specify the field the retrieve should get
            return await CustomRetrieveResponseMyModelSerializer(instance).amessage


Using lookup_request_field
--------------------------

You can use the ``lookup_request_field`` in a request to override the ``lookup_field`` only on one request. This would be useful if the original ``lookup_field`` is needed in another fonction or external library.
