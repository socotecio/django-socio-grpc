.. _pagination:

Pagination
==========


Description
-----------

**Pagination** is used to split data across several pages. It is a well known pattern to optimise performance on large dataset.

DSG work with pagination the same way as `DRF Pagination does <https://www.django-rest-framework.org/api-guide/pagination/>`_ that itself is a surcharge from the `Django Pagination system <https://docs.djangoproject.com/en/5.0/topics/pagination/>`_.

That mean that DSG support the default pagination class from DRF as `PageNumberPagination <https://www.django-rest-framework.org/api-guide/pagination/#pagenumberpagination>`_, `LimitOffsetPagination <https://www.django-rest-framework.org/api-guide/pagination/#limitoffsetpagination>`_ and `CursorPagination <https://www.django-rest-framework.org/api-guide/pagination/#cursorpagination>`_. It also support the fact to create your `own class <https://www.django-rest-framework.org/api-guide/pagination/#custom-pagination-styles>`_ for advanced pagination functionnalities

Pagination can be :ref:`enabled globally<pagination-using-it-globally>` for the all project or for :ref:`only some services<pagination-using-it-by-service>`.

To use pagination you could use metadata or request depending on :ref:`PAGINATION_BEHAVIOR settings<settings-pagination-behavior>`, See :ref:`example for how to use it<pagination-using-it>`.


.. _pagination-using-it-globally:

Using it globally
-----------------

To enable pagination gloablly you need to set the :ref:`DEFAULT_PAGINATION_CLASS settings<default_pagination_class_settings>` to the pagination class you want to use.


.. code-block:: python

    # settings.py
    GRPC_FRAMEWORK = {
        ...
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination"
        ...
    }


.. _pagination-using-it-by-service:

Using it by service
-------------------

To enable pagination only for one or some service you can override the :func:`pagination_class <django_socio_grpc.generics.GenericService.pagination_class>` attribute.

.. code-block:: python

    # server
    # quickstart/services.py
    from django_socio_grpc import generics
    from quickstart.models import Post
    from quickstart.serializer import PostProtoSerializer
    from rest_framework.pagination import PageNumberPagination


    # This service will have all the CRUD actions
    class PostService(generics.AsyncModelService):
        queryset = Post.objects.all()
        serializer_class = PostProtoSerializer
        pagination_class = PageNumberPagination

.. _pagination-using-it:

Using it
--------

You can use metadata or ``_pagination`` request field to make the filters works out of the box.

For more example you can see the `client in DSG example repo <https://github.com/socotecio/django-socio-grpc-example/blob/main/backend/bib_example_filter_client.py>`_

.. code-block:: python

    # client
    import asyncio
    import grpc
    import json

    async def main():
        ##########################################################################################################
        # Working if PAGINATION_BEHAVIOR settings is equal to "METADATA_STRICT" or "METADATA_AND_REQUEST_STRUCT" #
        ##########################################################################################################
        async with grpc.aio.insecure_channel("localhost:50051") as channel:
            quickstart_client = quickstart_pb2_grpc.PostControllerStub(channel)

            request = quickstart_pb2.PostListRequest()

            # Getting the 11 to 20 elements following backend ordering
            pagination_as_dict = {"page": 2, "page_size": 10}
            metadata = (("PAGINATION", (json.dumps(pagination_as_dict))),)

            response = await quickstart_client.List(request, metadata=metadata)
        

        ################################################################################################################
        # Working if PAGINATION_BEHAVIOR settings is equal to "REQUEST_STRUCT_STRICT" or "METADATA_AND_REQUEST_STRUCT" #
        ################################################################################################################
        async with grpc.aio.insecure_channel("localhost:50051") as channel:
            quickstart_client = quickstart_pb2_grpc.PostControllerStub(channel)

            # Getting the 11 to 20 elements following backend ordering
            pagination_as_dict = {"page": 2, "page_size": 6}
            pagination_as_struct = struct_pb2.Struct()
            pagination_as_struct.update(pagination_as_dict)

            # _pagination field is only generated if you set PAGINATION_BEHAVIOR to the correct options. Think to regenerate proto after changing it.
            request = quickstart_pb2.PostListRequest(_pagination=pagination_as_struct)

            response = await quickstart_client.List(request)

    if __name__ == "__main__":
        asyncio.run(main())


For web usage see :ref:`How to web: Using js client<using_js_client>`
