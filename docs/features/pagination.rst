.. _pagination:

Pagination
==========


Description
-----------

**Pagination** is used to split data across several pages. It is a well known pattern to optimise performance on large dataset.

DSG works with pagination the same way `DRF Pagination <https://www.django-rest-framework.org/api-guide/pagination/>`_ does. It uses the `Django Pagination system <https://docs.djangoproject.com/en/5.0/topics/pagination/>`_ and its `Paginator` class.

That means DSG supports the default pagination class from DRF like `PageNumberPagination <https://www.django-rest-framework.org/api-guide/pagination/#pagenumberpagination>`_, `LimitOffsetPagination <https://www.django-rest-framework.org/api-guide/pagination/#limitoffsetpagination>`_ and `CursorPagination <https://www.django-rest-framework.org/api-guide/pagination/#cursorpagination>`_. It also supports creating your `own Pagination <https://www.django-rest-framework.org/api-guide/pagination/#custom-pagination-styles>`_ for advanced pagination functionalities.

Pagination can be :ref:`enabled globally<pagination-using-it-globally>` for the all the project or for :ref:`only some services <pagination-using-it-by-service>`.

To use pagination you may use metadata or request depending on the :ref:`PAGINATION_BEHAVIOR setting<settings-pagination-behavior>`, See :ref:`example for how to use it<pagination-using-it>`.


.. _pagination-using-it-globally:

Using it globally on all List and Stream actions
------------------------------------------------

To enable pagination globally you need to set the :ref:`DEFAULT_PAGINATION_CLASS settings<default_pagination_class_settings>` to the pagination class you want to use.


.. code-block:: python

    # settings.py
    GRPC_FRAMEWORK = {
        ...
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination"
        ...
    }


.. _pagination-using-it-by-service:

Using it by service on List action
----------------------------------

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


.. _pagination-using-it-by-action:

Using it on specific action when using filter in message
--------------------------------------------------------

If your :ref:`PAGINATION_BEHAVIOR setting<settings-pagination-behavior>` is set to ``REQUEST_STRUCT_STRICT`` or ``METADATA_AND_REQUEST_STRUCT``
and you want to use filtering for your custom action by message and not metadata (:ref:`See Using It section <pagination-using-it>`)
you need to use the :func:`PaginationGenerationPlugin <django_socio_grpc.protobuf.generation_plugin.PaginationGenerationPlugin>`
as demonstrated below (:ref:`See Generation Plugin documentation <proto-generation-plugins>`):

.. code-block:: python

    # server
    # quickstart/services.py
    from django_socio_grpc import generics
    from quickstart.models import Post
    from quickstart.serializer import PostProtoSerializer
    from rest_framework.pagination import PageNumberPagination
    from django_socio_grpc.decorators import grpc_action
    from django_socio_grpc.protobuf.generation_plugin import ListGenerationPlugin, PaginationGenerationPlugin


    # This service will have all the CRUD actions
    class PostService(generics.GenericService):
        queryset = Post.objects.all()
        serializer_class = PostProtoSerializer
        pagination_class = PageNumberPagination

        @grpc_action(
            request=[],
            response=PostProtoSerializer,
            use_generation_plugins=[ListGenerationPlugin(request=True), PaginationGenerationPlugin()],
        )
        async def CustomListWithPagination(self, request, context):
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                if hasattr(serializer.message, "count"):
                    serializer.message.count = self.paginator.page.paginator.count
                return serializer.message
            else:
                serializer = self.get_serializer(queryset, many=True)
                return serializer.message

.. _pagination-using-it:

Using it
--------

You can use metadata or ``_pagination`` request field to make the filters work out of the box.

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
            pagination_as_dict = {"page": 2}
            metadata = (("pagination", (json.dumps(pagination_as_dict))),)

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

.. _pagination-with-page-size:

Using page size
---------------

As specified in the `DRF Pagination <https://www.django-rest-framework.org/api-guide/pagination/#pagination>`_ documentation, you need to override the ``PageNumberPagination`` class to use page size.

.. code-block:: python

    # server
    # quickstart/pagination.py
    from rest_framework.pagination import PageNumberPagination

    class CustomPageNumberPagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = 'page_size'
        max_page_size = 1000

    # quickstart/services.py
    ...
    from quickstart.pagination import CustomPageNumberPagination
    ...

    class PostService(generics.GenericService):
        ...
        pagination_class = CustomPageNumberPagination
        ...


.. _pagination-web-usage:

Web Example
-----------

For web usage of the client see :ref:`How to web: Using JS client<using_js_client>`


.. code-block:: javascript
    import { Struct } from "@bufbuild/protobuf";
    // See web usage to understand how to use the client.
    const postClient = createPromiseClient(PostController, transport);

    const paginationStruct = Struct.fromJson({page: 2});
    const res = await postClient.list({ _pagination: paginationStruct });
    console.log(res)


.. warning::
    The following example is the deprecated way of using pagination. Please use the example above.
    Note that the examples work depending on the :ref:`PAGINATION_BEHAVIOR setting<settings-pagination-behavior>` settings.


.. code-block:: javascript
    // See web usage to understand how to use the client.
    const postClient = createPromiseClient(PostController, transport);

    headers = {pagination: JSON.stringify({page: 2})}

    const res = await postClient.list({}, {headers})
    console.log(res)
