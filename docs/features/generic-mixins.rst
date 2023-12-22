.. _Generic Mixins:

Generic Mixins
==============


Description
-----------

DSG has built-in mixins for actions. Those mixins are either sync or async.

.. note:: 
    
    We recommend using the async mixins as they are more performant and will be the only ones supported in the future.

Usage
-----

============
Requirements
============

In order to correctly use the different mixins, you will need to use :func:`django_socio_grpc.generics.GenericService`.
This class will let you define multiple attributes which will be used in the different mixins:

- ``queryset``
- ``serializer_class``
- ``lookup_field``
- ``lookup_request_field``
- ``filter_backends``
- ``pagination_class``
- ``service_name``

========================================
CreateModelMixin / AsyncCreateModelMixin
========================================

- **Purpose:** This mixin provides functionality for creating a new model instance.
- Methods:
    - **Create:** Handles the creation of a new model instance. It takes a proto message as a request, validates it, saves the object, and returns the created object as a proto message.

====================================
ListModelMixin / AsyncListModelMixin
====================================

- **Purpose:** This mixin provides functionality for listing/querying model instances.
- Methods:
    - **List:** Retrieves a queryset, optionally paginates it, serializes the queryset into a list of proto messages, and returns the list. This method is a server-streaming RPC.

============================================
RetrieveModelMixin / AsyncRetrieveModelMixin
============================================

- **Purpose:** This mixin provides functionality for retrieving a single model instance by its unique identifier.
- Methods:
    - **Retrieve:** Retrieves a specific model instance based on a lookup field (e.g., primary key), serializes it, and returns the serialized instance as a proto message.

========================================
UpdateModelMixin / AsyncUpdateModelMixin
========================================

- **Purpose:** This mixin provides functionality for updating an existing model instance.
- Methods:
    - **Update:** Takes a proto message as a request, validates it, updates the object, and returns the updated object as a proto message.

======================================================
PartialUpdateModelMixin / AsyncPartialUpdateModelMixin
======================================================

- **Purpose:** This mixin provides functionality for partially updating an existing model instance.
- Methods:
    - **PartialUpdate:** Similar to UpdateModelMixin, but performs a partial update based on the fields specified in the request message.

==========================================
DestroyModelMixin / AsyncDestroyModelMixin
==========================================

- **Purpose:** This mixin provides functionality for deleting a model instance.
- Methods:
    - **Destroy:** Deletes a specific model instance based on a lookup field (e.g., primary key) and returns an empty response.

.. note::
    All the mixins above are included, if you use :func:`AsyncModelService<django_socio_grpc.generics.AsyncModelService>` as the base class for your service.
    The following mixins are not included by defautl but can be added.

========================================
StreamModelMixin / AsyncStreamModelMixin
========================================

- **Purpose:** Similar to ListModelMixin, but streams the queryset's results one by one to the client.
- Methods:
    - **Stream:** Retrieves a queryset, optionally paginates it, serializes the queryset into proto messages, and streams them to the client. This method is a server-streaming RPC.


These mixins are designed to be used with **Django models** to facilitate the creation of **gRPC services for performing CRUD** (Create, Read, Update, Delete) operations on those models in an API.

Example
-------

First import the mixins:

.. code-block:: python

    from django_socio_grpc import generics, mixins

Then you can add the mixins you want to use in your service class.

.. code-block:: python

    class TestService(
        mixins.AsyncListModelMixin,
        mixins.AsyncRetrieveModelMixin,
        generics.GenericService,
    ):
        queryset = MyObject.objects.all()
        serializer_class = MyObjectProtoSerializer
        pagination_class = StandardResultsSetPagination
        permission_classes = (IsAuthenticated, IsSocotecUser | IsServiceAccount)
        filter_backends = [DjangoFilterBackend]

This will generate the following service and RPCs:

.. code-block:: proto

    service TestService {
        rpc List (ListRequest) returns (MyObjectProto) {}
        rpc Retrieve (RetrieveRequest) returns (MyObjectProto) {}
    }
