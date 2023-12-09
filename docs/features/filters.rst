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