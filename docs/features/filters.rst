Filters
==========

**Filters** are used to filter the queryset of your service. You can use built-in filters from django-filters or create your own filters.


Description
-----------

This page will explain how to set up filters in your app services.

Usage
-----

To enable queryset filtering, you need to import generics from Django-Socio-GRPC.

.. code-block:: python

    from django_socio_grpc import generics, mixins

You can now create your own filter class.
You can also import another module from `django_filters <https://django-filter.readthedocs.io/en/stable/guide/install.html>`_ as it works with Django rest_framework.

# :TODO: please mention, that the *DjangoFilterBackend* can also be globally set in the settings.py file 

.. code-block:: python

    from django_filters.rest_framework import DjangoFilterBackend

Now, you can set the filter_backends attribute:

.. code-block:: python

    class MyObjectService(
        mixins.AsyncListModelMixin,
        mixins.AsyncRetrieveModelMixin,
        generics.GenericService,
    ):
        filter_backends = [DjangoFilterBackend]

By using DjangoFilterBackend as filter_backends, you can set a new attribute called filterset_class. This attribute should be equal to your filterset class. In this filterset class, you should declare your different filters. Django-filters already provides multiple built-in filter types, but you can also write your own filters.

In order to use the filters, you will need to set a "FILTERS" key in your request's metadata.

Example
-------

Let's look at a service example:


.. code-block:: python

    class MyObjectService(
        generics.AsyncModelService,
    ):
        queryset = MyObject.objects.all()
        filter_backends = [DjangoFilterBackend]
        filterset_class = MyObjectFilterSet
        lookup_field = "uuid"

In this case, the filter_set class corresponds to MyObjectFilterSet.

# :TODO: please explain the PerimeterFilterMixin  

.. code-block:: python

    
    # filters.py
    from django_filters.rest_framework import UUIDInFilterSet (?) PerimeterFilterMixin (?)


    class MyObjectFilterSet(PerimeterFilterMixin, UUIDInFilterSet):
        foo = UUIDFilter(field_name="foo__uuid")

        class Meta:
            model = MyObject
            fields = ("action_ref",)

As you can see in this example, we are using UUIDFilter as a built-in filter from django-filters



Filters can also be specified with a FieldDict, like shown in the example below:

:TODO: please explain the FieldDict and explain, what constraints are available, e.g. "exact", "contains", "lt", "gt" etc.

.. code-block:: python
    # filters.py
    from django_filters.rest_framework import FilterSet, CharFilter, DateRangeFilter

    from .models import Data

    class MyObjectFilterSet(FilterSet):
   
        class Meta:
            model = MyModel
            fields = {
                'name': ['exact', 'contains'],
                'title': ['exact', 'contains'],
                'description': ['exact', 'contains'],
                'datetime_created': ['lt', 'gt'],
            }


# :TODO: add also "search" example, since it is also supported 


: TODO: add also example for the client side, how to use the filter functionality:

# This is an example of how to use the filter functionality of the backend.

import asyncio
import grpc
import json

from example_bib_app.grpc import example_bib_app_pb2_grpc, example_bib_app_pb2

async def main():
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        author_client = example_bib_app_pb2_grpc.AuthorControllerStub(channel)
        publisher_client = example_bib_app_pb2_grpc.PublisherControllerStub(channel)
        book_client = example_bib_app_pb2_grpc.BookControllerStub(channel)

        # we recommend to start with an dictionary and convert it into a string, whenever this 
        filter_as_dict = {"name_last": "Doe"}
        metadata = (("filters", (json.dumps(filter_as_dict))),)
        response = await author_client.List(example_bib_app_pb2.AuthorListRequest(), metadata=metadata)

        print("Filter as dict:--------------------\n", filter_as_dict)
        print("Response (from JSON string) received :\n", response)

        # although one could use a filter string (in JSON format) to send a filter like:
        filter_as_str = '{"name_last": "Doe"}'
        metadata = (("filters", (filter_as_str)),) 
        response = await author_client.List(example_bib_app_pb2.AuthorListRequest(), metadata=metadata)

        print("Filter as string:----------------\n", filter_as_str)
        print("Response (from string) received :\n", response)

        # publisher filter
        print("Publisher filter:----------------\n")
        filter_as_dict = {"name": "Doe"}
        metadata = (("filters", (json.dumps(filter_as_dict))),)
        response = await publisher_client.List(example_bib_app_pb2.PublisherListRequest(), metadata=metadata)

        print("Response (from JSON string) received :\n", response)

        # book search
        print("Book search:----------------\n")
        search_as_dict = {"title": "book 1"}
        metadata = (("search", (json.dumps(search_as_dict))),)
        response = await book_client.List(example_bib_app_pb2.BookListRequest(), metadata=metadata)

        print("Response (from JSON string) received :\n", response)


    
            
if __name__ == "__main__":
    asyncio.run(main())
