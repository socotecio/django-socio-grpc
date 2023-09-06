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

The generics.Generic class allows you to declare multiple attributes for your service class:
    - queryset: Specifies the initial queryset used for data retrieval.
    - serializer_class: Determines the serializer class used for data serialization and deserialization.
    - lookup_field and lookup_request_field: Define the fields used for object lookup in detail services.
    - filter_backends: Specifies the filter backend classes for queryset filtering.
    - pagination_class: Defines the pagination style for querysets.

You will also need to import another module from djang_filters (https://django-filter.readthedocs.io/en/stable/guide/install.html).

.. code-block:: python

    from django_filters.rest_framework import DjangoFilterBackend

Now, you can set the filter_backends attribute:


.. code-block:: python

    class PeriodicityService(
        mixins.AsyncListModelMixin,
        mixins.AsyncRetrieveModelMixin,
        generics.GenericService,
    ):
        queryset = Periodicity.objects.all()
        serializer_class = PeriodicityProtoSerializer
        pagination_class = StandardResultsSetPagination
        permission_classes = (IsAuthenticated, IsSocotecUser | IsServiceAccount)
        filter_backends = [DjangoFilterBackend]

By using DjangoFilterBackend as filter_backends, you can set a new attribute called filterset_class. This attribute should be equal to your filterset class. In this filterset class, you should declare your different filters. Django-filters already provides multiple built-in filter types, but you can also write your own filters.

Example
-------

Let's look at a service example:
 

.. code-block:: python

    class ActionService(
        ExternalAccessMixin,
        generics.AsyncModelService,
        AsyncDestroyIfNotExistInReportMixin,
    ):
        authorized_actions = [*ExternalAccessMixin.authorized_actions, "ListWithAggregates"]
        queryset = Action.objects.all()
        serializer_class = ActionProtoSerializer
        pagination_class = StandardResultsSetPagination
        permission_classes = (IsAuthenticated, IsSocotecUser | IsServiceAccount)
        filter_backends = [DjangoFilterBackend, ActionAosPrefilterBackend]
        filterset_class = ActionFilterSet
        lookup_field = "uuid"

In this case, the filter_set class corresponds to ActionFilterSet. This service also use another filter_backends class: ActionAosPrefilterBackend

.. code-block:: python

    from django_filters.rest_framework import UUIDFilter

    class ActionAosPrefilterBackend(BaseAosPrefilterBackend):
        lookup_prefix = "observations__perimeter__aos_observables"


    class ActionFilterSet(PerimeterFilterMixin, UUIDInFilterSet):
        observations__in = UUIDInFilter(field_name="observations")
        observable__in = UUIDInFilter(field_name="observations__perimeter__aos_observables__uuid")
        aos_item_uuid__in = UUIDInFilter(
            field_name="observations__perimeter__aos_observables__aos_item_uuid"
        )
        action_ref = UUIDFilter(field_name="action_ref__uuid")
        priority__in = UUIDInFilter(field_name="priority__uuid")
        ventilation__in = UUIDInFilter(field_name="ventilation__uuid")
        status__in = CharInFilter(field_name="status")
        contributors__in = UUIDInFilter(field_name="contributors__contributor_uuid")
        total_amount__comp = CompNumberFilter(field_name="total_amount")
        date__year__comp = CompNumberFilter(field_name="date__year")
        analytical_axes = UUIDInFilter(field_name="observations__analytical_axis__uuid")

        class Meta:
            model = Action
            fields = ("action_ref",)

As you can see in this example, we are using UUIDFilter as a built-in filter from django-filters