.. _use-django-decorators-in-dsg:

Use Django decorators in DSG
=============================

In Django, decorators expect to decorate a function that takes a `django.http.HttpRequest <https://docs.djangoproject.com/en/5.0/ref/request-response/#httprequest-objects>`_ as its first argument and return a `django.http.HttpResponse <https://docs.djangoproject.com/en/5.0/ref/request-response/#httpresponse-objects>`_.

In DSG, decorators expect to decorate a class method that take 2 arguments: a `grpc Message<https://grpc.io/docs/languages/python/quickstart/#update-the-server>`_ as request and the `grpc context <https://grpc.github.io/grpc/python/grpc_asyncio.html#server-side-context>`_, and return a `grpc Message <https://grpc.io/docs/languages/python/quickstart/#update-the-server>`_ as response.

Both are based on HTTP protocol. So it's possible to find similar concept and usage.

By using :ref:`DSG proxy request and proxy response <request-and-response-proxy>` it is possible to simulate django behavior and apply it to gRPC calls.

See :func:`http_to_grpc decorator <django_socio_grpc.decorators.http_to_grpc>` for more detailsa and parameters.

.. _simple-example:

Simple example
--------------


.. code-block:: python

    from django_socio_grpc.decorators import http_to_grpc
    from django.views.decorators.vary import vary_on_headers

    def vary_on_metadata(*headers):
        return http_to_grpc(vary_on_headers(*headers))

.. _example-with-method-decorator-and-data-variance:

Example with method decorator and data variance
------------------------------------------------

In the following example we are transforming a fucntion decorator into a method decorator.
Then we are transforming it to a grpc decorator.
In the same time we specify that for each simulate Django request we want to set the ``method`` attribute to the value ``GET`` (this is because grpc only use POST request and Django only cache GET request)

The ``functools.wraps`` is optional and is used to keep the original function name and docstring.

.. code-block:: python

    from django_socio_grpc.decorators import http_to_grpc
    from django.views.decorators.cache import cache_page


    @functools.wraps(cache_page)
    def cache_endpoint(*args, **kwargs):
        return http_to_grpc(
            method_decorator(cache_page(*args, **kwargs)),
            request_setter={"method": "GET"},
        )
