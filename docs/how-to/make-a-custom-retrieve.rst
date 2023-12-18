Make a custom retrieve
=======================

# :TODO: contet missing

Description
-----------

A custom retrieve is a request to get an object by searching on one or several fields. 

1 - Updating the lookup_field
-----

the lookup_field is the field where the retrieve will automaticaly search, the original field is the pk field. 
You can updating this field in the service

Example
-------

.. code-block:: python

    class ForeignModelService(
    generics.GenericService, mixins.AsyncListModelMixin, mixins.AsyncRetrieveModelMixin
    ):
    queryset = ForeignModel.objects.all().order_by("uuid")
    serializer_class = ForeignModelSerializer
    lookup_field = "name"


2 - Overriding the retrieve 
-----

Another way to make a custom retrieve is to override the Retrieve action.

Example
-------

.. code-block:: python

    class SpecialFieldsModelService(generics.AsyncModelService):
    queryset = SpecialFieldsModel.objects.all().order_by("uuid")
    serializer_class = SpecialFieldsModelSerializer

    @sync_to_async
    def format_custom_message(self, instance):
        serializer = SpecialFieldsModelSerializer(instance)
        return serializer.message

    @grpc_action(
        request=[{"name": "uuid", "type": "string"}],
        response=SpecialFieldsModelSerializer,
    )
    async def Retrieve(self, request, context):
        instance = self.get_object()
        return await self.format_custom_message(instance)


3 - Retrieve a custom object
-----

If you need a custom object to get more or less field on the object you can pass a custom serializer on the response.

Example
-------

.. code-block:: python

    class SpecialFieldsModelService(generics.AsyncModelService):
    queryset = SpecialFieldsModel.objects.all().order_by("uuid")
    serializer_class = SpecialFieldsModelSerializer

    @sync_to_async
    def format_custom_message(self, instance):
        serializer = CustomRetrieveResponseSpecialFieldsModelSerializer(instance)
        return serializer.message

    @grpc_action(
        request=[{"name": "uuid", "type": "string"}],
        response=CustomRetrieveResponseSpecialFieldsModelSerializer,
    )
    async def Retrieve(self, request, context):
        instance = self.get_object()
        return await self.format_custom_message(instance)


4 - Using lookup_request_field
-----

You can use the lookup_request_field in a request to override the lookup_field only on one request. This would be useful if the original lookup_field is needed in another fonction
