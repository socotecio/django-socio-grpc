Filters
==========

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

.. code-block:: python

    from django_filters.rest_framework import UUIDFilter


    class MyObjectFilterSet(PerimeterFilterMixin, UUIDInFilterSet):
        foo = UUIDFilter(field_name="foo__uuid")

        class Meta:
            model = MyObject
            fields = ("action_ref",)

As you can see in this example, we are using UUIDFilter as a built-in filter from django-filters
