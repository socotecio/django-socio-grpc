.. _grpc_action:

GRPCAction
==========

Description
-----------

With **DSG** you can declare custom gRPC actions related to your app service with the **decorator grpc_action**.
Once your service registered, it will create the RPC and its messages in your ``.proto`` file after the proto generation.

A gRPC action is a representation of an RPC inside the service where it's declared.
It is composed of a **request and a response definitions**.

.. note::
    The corresponding proto code extracted from the decorator will be **automatically generated** by the `generateproto command <commands-generate-proto>`_. Do not do it manually.


Example of a basic RPC command of a generated .proto file:

.. code-block:: proto

    rpc BasicList(BasicRequest) returns (BasicResponse) {}

It can also use a **stream** as a request/response.

Usage
-----

======
Import
======

First of all, you need to import the ``grpc_action`` decorator:

.. code-block:: python

    from django_socio_grpc.decorators import grpc_action

This decorator can now be used for each action of your service.

Before looking at each argument of this decorator let see its definition:

.. code-block:: python

    from typing import List, Type
    from django_socio_grpc.protobuf.generation_plugin import BaseGenerationPlugin
    from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor

    grpc_action(
        request: RequestResponseType | None = None,
        response: RequestResponseType | None = None,
        request_name: str | None = None,
        response_name: str | None = None,
        request_stream: bool = False,
        response_stream: bool = False,
        use_request_list: bool = False,
        use_response_list: bool = False,
        message_name_constructor_class: Type[
            MessageNameConstructor
        ] = grpc_settings.DEFAULT_MESSAGE_NAME_CONSTRUCTOR
        use_generation_plugins: List[BaseGenerationPlugin] = field(
            default_factory=grpc_settings.DEFAULT_GENERATION_PLUGINS
        )
    )

.. _grpc-action-request-response:

========================
``request`` ``response``
========================

The ``request`` and ``response`` arguments can be:
    - a `list` of :func:`FieldDict <django_socio_grpc.protobuf.typing.FieldDict>`: the fields of the message,
      if the list is empty, the message will be of type ``google.protobuf.Empty``. (:ref:`See example<grpc-action-basic-example>`)
    - a ``Serializer``: the serializer describing the message. (See :ref:`proto-serializers`)
    - a ``str``: the name of the message if already defined in the proto file.
    - a ``Placeholder``: a placeholder to use in the proto file
      (See :ref:`placeholder`).

This 4 possibilies are typed like this (to help you understand where the different options and class come from. To see examples refer to :ref:`Use Cases section<grpc-action-use-cases>`):

.. code-block:: python

    from typing import List, Optional, TypedDict, Union
    from django_socio_grpc.protobuf.typing import FieldDict
    from django_socio_grpc.proto_serializers import BaseProtoSerializer
    from django_socio_grpc.grpc_actions.placeholders import Placeholder

    RequestResponseType = Union[List[FieldDict], Type[BaseProtoSerializer], str, Placeholder]


.. _grpc-action-request-name-response-name:

==================================
``request_name`` ``response_name``
==================================

By default, the name of the request/response message is generated from the name of the action,
the name of the serializer if a serializer is used, and the service name.

Those arguments are used to override this name. Example: :ref:`grpc-action-overriding-request-and-response-proto-name`.

If not set will use the :ref:`message_name_constructor_class argument <grpc-action-message-name-constructor>` as :ref:`specified in doc <proto-generation-message-name-constructor>`

======================================
``request_stream`` ``response_stream``
======================================

Those arguments are used to mark the RPC request/response as a stream. Example: :ref:`grpc-action-streaming`.

==========================================
``use_request_list`` ``use_response_list``
==========================================

.. warning::

    Both of these arguments are deprecated and will be removed in version 1.0.0.
    They are replaced by the :ref:`GenerationPlugin mechanism <proto-generation-plugins>` combined with
    :func:`ListGenerationPlugin <django_socio_grpc.protobuf.generation_plugin.ListGenerationPlugin>`

Those arguments are used to encapsulate the message inside a List message.
It is useful when returning a list of object with a serializer. Example: :ref:`grpc-action-use-request-and-response-list`


.. _grpc-action-message-name-constructor:

============================
``message_name_constructor``
============================

This argument allows you to customize the proto message names generated when no ``request_name`` and/or ``response_name`` are specified. It expect a class with specific method and behavior and its instance is passed as arguments in the :ref:`generation plugin mechanism <proto-generation-plugins>`.
For more information, please read :ref:`the specified documentation <proto-generation-message-name-constructor>`.

Defaulting to the :ref:`DEFAULT_MESSAGE_NAME_CONSTRUCTOR setting <settings-default-message-name-constructor>`


.. _grpc-action-use-generation-plugins:

==========================
``use_generation_plugins``
==========================

This argument allows to customize the proto generated dynamically by DSG to match your needs.
It accepts a list of instances of :func:`BaseGenerationPlugin <django_socio_grpc.protobuf.generation_plugin.BaseGenerationPlugin>`.

For more information, please read :ref:`the generation plugin documentation <proto-generation-plugins>`


.. _grpc-action-use-cases:

Use Cases
---------

.. _grpc-action-basic-example:

===========================================================================================
Basic :func:`FieldDict <django_socio_grpc.protobuf.typing.FieldDict>` request and response:
===========================================================================================

This ExampleService has a Retrieve action (RPC)
that takes a uuid as argument and returns a username and a list of items:

.. code-block:: python

    from django_socio_grpc.decorators import grpc_action
    from django_socio_grpc.generics import GenericService

    class ExampleService(GenericService):
        ...

        @grpc_action(
            request=[
                {
                    "name": "uuid",
                    "type": "string",
                }
            ],
            response=[
                {
                    "name": "username",
                    "type": "string",
                },
                {
                    "name": "items",
                    "type": "string",
                    "cardinality": "repeated",
                },
            ],
        )
        async def Retrieve(self, request, context):
            ...

This results in the following proto code after the proto generation with the ``generateproto`` command:

.. code-block:: proto

    service ExampleService {
        rpc Retrieve(RetrieveRequest) returns (RetrieveResponse) {}
    }

    message RetrieveRequest {
        string uuid = 1;
    }

    message RetrieveResponse {
        string username = 1;
        repeated string items = 2;
    }

.. _grpc-action-overriding-request-and-response-proto-name:

===============================================
Overriding the request and response proto name
===============================================

This ExampleService has a Retrieve action (RPC). By default the name of the proto message will be ``RetrieveRequest`` and ``RetrieveResponse``.
It is possible to change it by using ``request_name`` and ``response_name`` arguments:


.. code-block:: python

    from django_socio_grpc.decorators import grpc_action
    from django_socio_grpc.generics import GenericService

    class ExampleService(GenericService):
        ...

        @grpc_action(
            request=[
                {
                    "name": "uuid",
                    "type": "string",
                }
            ],
            response=[
                {
                    "name": "username",
                    "type": "string",
                },
                {
                    "name": "items",
                    "type": "string",
                    "cardinality": "repeated",
                },
            ],
            request_name= "CustomRetrieveRequest",
            response_name= "CustomRetrieveResponse"
        )
        async def Retrieve(self, request, context):
            ...

This results in the following proto code after the proto generation with the ``generateproto`` command:

.. code-block:: proto

    service ExampleService {
        rpc Retrieve(CustomRetrieveRequest) returns (CustomRetrieveResponse) {}
    }

    message CustomRetrieveRequest {
        string uuid = 1;
    }

    message CustomRetrieveResponse {
        string username = 1;
        repeated string items = 2;
    }

=======================
Serializers as messages
=======================


Serializers can be used to generate the response message as shown in the example below:
Here the ``UserProtoSerializer`` is used to generate the response message.

.. code-block:: python

    from django_socio_grpc.decorators import grpc_action
    from django_socio_grpc.proto_serializers import ModelProtoSerializer
    from django_socio_grpc.generics import GenericService
    from rest_framework import serializers
    from rest_framework.pagination import PageNumberPagination
    from django.contrib.auth.models import User
    from django_socio_grpc.protobuf.generation_plugin import ListGenerationPlugin

    class UserProtoSerializer(ModelProtoSerializer):
        username = serializers.CharField()

        class Meta:
            model = User
            fields = ("username",)

    class ExampleService(GenericService):
        ...

        # This is used to have the `count` field in the message. Not needed if set by default in the settings
        pagination_class = PageNumberPagination

        @grpc_action(
            request=[],
            response=UserProtoSerializer,
            use_generation_plugins=[ListGenerationPlugin(response=True)],
        )
        async def List(self, request, context):
            ...

This is corresponds to the following proto code after the proto generation with the ``generateproto`` command:

.. code-block:: proto

    service ExampleService {
        rpc List(google.protobuf.Empty) returns (UserListResponse) {}
    }

    message UserResponse {
        string username = 1;
    }

    message UserListResponse {
        repeated UserResponse results = 1;
        int32 count = 2;
    }

.. note::
    In the ``UserListResponse`` message, the ``results`` field is a ``UserResponse`` message,
    it is the message generated from the ``UserProtoSerializer``.
    This field name can be changed using :ref:`Serializer Meta attr<customizing-the-name-of-the-field-in-the-listresponse>` or :ref:`serializer kwargs<proto-serializer-extra-kwargs-options>`.
    There is also a ``count`` field which is the total number of results, it **is present only
    if the pagination is enabled**.


.. _grpc-action-use-request-and-response-list:

===================================
Usage of Request And Response List
===================================

.. code-block:: python


    from rest_framework import serializers
    from django_socio_grpc.decorators import grpc_action
    from django_socio_grpc.proto_serializers import ModelProtoSerializer
    from django_socio_grpc.protobuf.generation_plugin import ListGenerationPlugin

    class UserProtoSerializer(ModelProtoSerializer):
        uuid = serializers.UUIDField(read_only=True)
        username = serializers.CharField()
        password = serializers.CharField(write_only=True)

        class Meta:
            model = User
            fields = ("uuid", "username", "password")

    @grpc_action(
        request=UserProtoSerializer,
        response=UserProtoSerializer,
        use_generation_plugins=[ListGenerationPlugin(request=True, response=True)]
    )
    async def BulkCreate(self, request, context):
        return await self._bulk_create(request, context)


This corresponds to the generated proto code:

.. code-block:: proto

    service ExampleService {
        rpc List(UserListRequest) returns (UserListResponse) {}
    }

    message UserRequest {
        string username = 1;
        string password = 1;
    }

    message UserListRequest {
        repeated UserRequest results = 1;
        int32 count = 2;
    }

    message UserResponse {
        string uuid = 1;
        string username = 1;
    }

    message UserListResponse {
        repeated UserResponse results = 1;
        int32 count = 2;
    }


.. note::
    In the ``UserListResponse`` and ``UserListRequest`` message, the ``results`` field is a ``UserResponse`` or ``UserRequest`` message,
    it is the message generated from the ``UserProtoSerializer``.
    This field name can be changed using :ref:`Serializer Meta attr<customizing-the-name-of-the-field-in-the-listresponse>` or :ref:`serializer kwargs<proto-serializer-extra-kwargs-options>`.
    It is not possible to change them separately `for now <https://github.com/socotecio/django-socio-grpc/issues/241>`_.
    There is also a ``count`` field which is the total number of results, it **is present only
    if the pagination is enabled**. This field is not used for ``Request``.


.. _grpc-action-streaming:

=========
Streaming
=========

You can use the ``request_stream`` and ``response_stream`` arguments to mark the RPC as a stream,
as shown in the following example (See :ref:`Streaming doc for implementation<streaming>` ):

.. code-block:: python

    from django_socio_grpc.decorators import grpc_action

    @grpc_action(
        request="google.protobuf.Empty",
        response=[{"name": "str", "type": "string"}],
        response_stream=True,
    )
    async def Stream(self, request, context):
        ...

This is equivalent to:

.. code-block:: proto

    rpc Stream(google.protobuf.Empty) returns (stream StreamResponse) {}


.. _placeholder:

============
Placeholders
============

Placeholders are objects that will be replaced in the :ref:`service registration<services-registry>` step.
They are useful when you want to use arguments that should be overwritten in subclasses (**Meaning when you are coding your own Mixins**).

They define a ``resolve`` method that will be called with
the service instance as argument.

.. code-block:: python

    # service.py
    from django_socio_grpc.grpc_actions.placeholders import Placeholder

    # This placeholder always resolves to "MyRequest"
    class RequestNamePlaceholder(Placeholder):
        def resolve(self, service: GenericService):
            return "MyRequest"


In a service class, you can use placeholders in any of the ``grpc_action`` arguments:

.. code-block:: python

    # service.py
    from django_socio_grpc.generics import GenericService
    from django_socio_grpc.grpc_actions.placeholders import AttrPlaceholder, SelfSerializer

    class ExampleSuperService(GenericService):

        @grpc_action(
            request=AttrPlaceholder("_request"),
            request_name=RequestNamePlaceholder, # RequestNamePlaceholder comes from the doc code just above
            response=SelfSerializer,
            response_name = "MyResponse",
        )
        def Route(self, request, context):
            ...

    class ExampleSubService(ExampleSuperService):

        serializer_class = MySerializer
        _request = []

        def Route(self, request, context):
            ...


This is gets transformed into the following proto code after the proto generation with the ``generateproto`` command:

.. code-block:: proto

    service ExampleSubService {
        rpc Route(MyRequest) returns (MyResponse) {}
    }

    // The name of the message is "MyRequest" because of the placeholder
    message MyRequest {
        // This message is empty because _request is an empty list
    }

    message MyResponse {
        ...
        // Defined by MySerializer
    }


There are a few predefined placeholders:

:func:`FnPlaceholder<django_socio_grpc.grpc_actions.placeholders.FnPlaceholder>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolves to the result of a function.

.. code-block:: python

    # django_socio_grpc.grpc_actions.placeholders.FnPlaceholder

    def fn(service) -> str:
        return "Ok"

    FnPlaceholder(fn) == "Ok"


:func:`AttrPlaceholder<django_socio_grpc.grpc_actions.placeholders.AttrPlaceholder>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolves to a named class attribute of the service.

.. code-block:: python

    # django_socio_grpc.grpc_actions.placeholders.AttrPlaceholder

    AttrPlaceholder("my_attribute") == service.my_attribute


:func:`SelfSerializer<django_socio_grpc.grpc_actions.placeholders.SelfSerializer>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolves to the serializer_class of the service.


.. code-block:: python

    # django_socio_grpc.grpc_actions.placeholders.SelfSerializer

    SelfSerializer == service.serializer_class


:func:`StrTemplatePlaceholder<django_socio_grpc.grpc_actions.placeholders.StrTemplatePlaceholder>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolves to a string template with either service attributes names or
functions as parameter. It uses ``str.format`` to inject the values.

.. code-block:: python

    # django_socio_grpc.grpc_actions.placeholders.StrTemplatePlaceholder

    def fn(service) -> str:
        return "Ok"

    StrTemplatePlaceholder("{}Request{}", "My", fn) == "MyRequestOk"


:func:`LookupField<django_socio_grpc.grpc_actions.placeholders.LookupField>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolves to the service lookup field message. For for information about lookup_field or it's implementation see :ref:`make-a-custom-retrieve`

.. code-block:: python

    from django_socio_grpc.generics import GenericService

    class Serializer(BaseSerializer):
        """
        This is only for LookupField. Use a proto serializer imported from django_socio_grpc.proto_serializer in real code.
        """
        uuid = serializers.CharField()

    # If declaring a service like this
    class Service(GenericService):
        serializer_class = Serializer
        lookup_field = "uuid"

    # Then if using LookupField placeholder in grpc_action's request or response parameter it will transform at runtime to

    # django_socio_grpc.grpc_actions.placeholders.LookupField
    LookupField == [{
        "name": "uuid",
        "type": "string", # This is the type of the field in the serializer
    }]

===============================
Force Message for Known Method
===============================

You can use the :ref:`grpc action <grpc_action>` decorator on the ``known`` method to override the default message that comes from :ref:`mixins <Generic Mixins>`.

.. code-block:: python

    # service.py
    from django_socio_grpc.decorators import grpc_action
    from django_socio_grpc.generics import AsyncModelService
    from my_app.models import MyModel # Replace by your model
    from my_app.serializers import MyModelProtoSerializer # Replace by your serializer

    class MyModelService(AsyncModelService):
        queryset = MyModel.objects.all().order_by("uuid")
        serializer_class = MyModelProtoSerializer

        @grpc_action(
            request=[{"name": "my_example_request", "type": "string"}],
            response=[{"name": "my_example_response", "type": "string"}],
        )
        async def Retrieve(self, request, context):
            pass

This will result in the following proto code after the proto generation with the ``generateproto`` command:

.. code-block:: proto

    import "google/protobuf/empty.proto";

    service MyModelController {
        ...
        rpc Retrieve(ExampleRetrieveRequest) returns (ExampleRetrieveResponse) {}
        ...
    }

    ...

    message ExampleRetrieveRequest {
        string my_example_request = 1;
    }

    message ExampleRetrieveResponse {
        string my_example_response = 1;
    }


========
Comments
========

You can add comments to your request/response fields by using the
``comment`` key when using a ``FieldDict`` as shown in the following example.
The comment will be added to the corresponding field in the proto file.


.. code-block:: python

    from django_socio_grpc.generics import GenericService
    from django_socio_grpc.decorators import grpc_action

    class Service(GenericService):
        ...

        @grpc_action(
            request=[],
            response=[
                {
                    "name": "username",
                    "type": "string",
                    "comment": "This is my proto comment",
                },
            ],
        )
        async def Retrieve(self, request, context):
            ...


This will result in the following generated proto code:

.. code-block:: proto

    service Service {
        rpc Retrieve(RetrieveRequest) returns (RetrieveResponse) {}
    }

    message RetrieveRequest {
    }

    message RetrieveResponse {
        // This is my proto comment
        string username = 1;
    }
