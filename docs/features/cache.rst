.. _cache:

Cache
=====

Description
-----------

Usually django cache is used to cache page or basic ``GET`` request. However, in the context of gRPC, we use ``POST`` request and there is no `native cache system in gRPC in Python <https://github.com/grpc/grpc/issues/7945>`_.

Fortunately, DSG bring a layer of abstraction between gRPC request and Django request allowing us to use Django cache system.

To enable it follow the `Django instructions <https://docs.djangoproject.com/fr/5.0/topics/cache/#setting-up-the-cache>`_ then use the :ref:`cache_endpoint <cache-endpoint>` decorator or the :ref:`cache_endpoint_with_deleter <cache-endpoint-with-deleter>` to cache your endpoint.

.. _cache-endpoint:

cache_endpoint
--------------

Th :func:`cache_endpoint <django_socio_grpc.decorators.cache_endpoint>` decorator is used to adapt the `cache_page <https://docs.djangoproject.com/fr/5.0/topics/cache/#django.views.decorators.cache.cache_page>`_ decorator to work with grpc.

It took the same parameters and do the exact same things. See :ref:`Use Django decorators in DSG <use-django-decorators-in-dsg>` for more informations.

This decorator will cache response depending on:

* :ref:`Filters <filters>`
* :ref:`Pagination <pagination>`

Meaning that if you have a filter in your request, the cache will be different for each filter.

.. warning::

    If you have request parameters that are not considered as filters or pagination, the cache will not be different for each request.


Example:

.. code-block:: python

    from django_socio_grpc.decorators import cache_endpoint
    ...

    class UnitTestModelWithCacheService(generics.AsyncModelService, mixins.AsyncStreamModelMixin):
        queryset = UnitTestModel.objects.all().order_by("id")
        serializer_class = UnitTestModelWithCacheSerializer

        @grpc_action(
            request=[],
            response=UnitTestModelWithCacheSerializer,
            use_generation_plugins=[
                ListGenerationPlugin(response=True),
            ],
        )
        @cache_endpoint(300)
        async def List(self, request, context):
            return await super().List(request, context)

.. _cache-endpoint-with-deleter:

cache_endpoint_with_deleter
---------------------------

The :func:`cache_endpoint_with_deleter <django_socio_grpc.decorators.cache_endpoint_with_deleter>` decorator work the same :ref:`cache_endpoint <cache-endpoint>` but allow to automatically delete the cache when a django signals is called from the models passed in parameters.

As DSG is an API framework it's logic to add utils to invalidate cache if data is created, updated or deleted.

.. warning::

    The cache will not be deleted if using bulk operations. This also integrate the usage of filter(...).update() method.
    See `caveats of each meathod you wish to use to be sure of the behavior <https://docs.djangoproject.com/en/5.0/ref/models/querysets/#bulk-create>`_

    The cache will also not be deleted if modifying date in an other process that is not gRPC (Django commands, admin, shell, ...).
    You can make your own decorator to handle this case if needed by registering decorator parameter in a global context and then listen to all django event to see if one matching.
    We decide to not integrate it because listening all django events and making check on signals and senders may add an unwanted request overhead.

There is also caveats to understand when usings cache-endpoint-with-deleter. As only Redis cache allow a pattern like deleter, if not using redis cache each specified signals on the specified models of the deleter will delete the entire cache.

To address this issue, you can:

* Use a `redis cache <https://docs.djangoproject.com/fr/5.0/topics/cache/#redis>`_
* Use a cache per model

.. note::

    If you do not follow above advice a warning will show up everytimes you start the server. To disable it use the :ref:`ENABLE_CACHE_WARNING_ON_DELETER <settings-cache-warning-on-deleter>` setting.


Example:

.. code-block:: python


    # SETTINGS
    CACHES = {
        "UnitTestModelCache": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "unit_test_model_cache_table",
        }
    }

    # SERVICES
    from django_socio_grpc.decorators import cache_endpoint_with_deleter
    ...

    class UnitTestModelWithCacheService(generics.AsyncModelService, mixins.AsyncStreamModelMixin):
        queryset = UnitTestModel.objects.all().order_by("id")
        serializer_class = UnitTestModelWithCacheSerializer

        @grpc_action(
            request=[],
            response=UnitTestModelWithCacheSerializer,
            use_generation_plugins=[
                ListGenerationPlugin(response=True),
            ],
        )
        @cache_endpoint_with_deleter(
            300,
            key_prefix="UnitTestModel",
            cache="UnitTestModelCache",
            senders=(UnitTestModel,),
        )
        async def List(self, request, context):
            return await super().List(request, context)


.. _vary-on-metadata:

vary_on_metadata
----------------

Working like django `vary_on_headers <https://docs.djangoproject.com/fr/5.0/topics/cache/#using-vary-headers>`_ it's just a convenient renaming using :ref:`Use Django decorators in DSG <use-django-decorators-in-dsg>`.

It allow the cache to also `vary on metadata <https://github.com/grpc/grpc/tree/master/examples/python/metadata>`_ and not only filters and paginations.

Example:


.. code-block:: python

    from django_socio_grpc.decorators import cache_endpoint, vary_on_metadata
    ...

    class UnitTestModelWithCacheService(generics.AsyncModelService, mixins.AsyncStreamModelMixin):
        queryset = UnitTestModel.objects.all().order_by("id")
        serializer_class = UnitTestModelWithCacheSerializer

        @grpc_action(
            request=[],
            response=UnitTestModelWithCacheSerializer,
            use_generation_plugins=[
                ListGenerationPlugin(response=True),
            ],
        )
        @cache_endpoint(300)
        @vary_on_metadata("custom-metadata", "another-metadata")
        async def List(self, request, context):
            return await super().List(request, context)


.. _any-other-decorator:

Any other decorator
-------------------

As you can use :ref:`Django decorators in DSG <use-django-decorators-in-dsg>`. You can try to use any django decorators as long as they are wrapped into :func:`http_to_grpc decorator <django_socio_grpc.decorators.http_to_grpc>`.

If the one you are trying to use is not working as expected and it's not listed in the documentation page please fill an issue.
