.. _grpc_action:
GRPCAction
==========

Description
-----------

With Django-Socio-GRPC you can declare custom gRPC actions related to your app service with the decorator grpc_action.
Once your service registered, it will create the RPC and its messages in your .proto file after the proto generation.

A gRPC action is a representation of an RPC inside the service where it's declared.
It is composed of a request and a response definitions.

!! mind: The corresponding proto code will be **automatically generated** by the ``generateproto`` command. Do not do it manually :


Example of a basic RPC command of a generated .proto file:
.. code-block:: proto

    rpc BasicList(BasicRequest) returns (BasicResponse) {}

It can also use a stream as a request/response.

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

    grpc_action(
        request: RequestResponseType | None = None,
        response: RequestResponseType | None = None,
        request_name: str | None = None,
        response_name: str | None = None,
        request_stream: bool = False,
        response_stream: bool = False,
        use_request_list: bool = False,
        use_response_list: bool = False,
    )

========================
``request`` ``response``
========================

The ``request`` and ``response`` arguments can be:
    - a `list` of ``FieldDict``: the fields of the message,
      if empty, the message will of type ``google.protobuf.Empty``.
    - a ``Serializer``: the serializer describing the message.
    - a ``str``: the name of the message if already defined in the proto file.
    - a ``Placeholder``: a placeholder to use in the proto file
      (see :ref:`placeholder`).



# :TODO: please explain this example better ( I think, it's not clear - maybe put it in a full example ? )

.. code-block:: python

    class FieldCardinality(str, Enum):
        NONE = ""
        OPTIONAL = "optional"
        REPEATED = "repeated"

    class FieldDict(TypedDict):
        name: str
        type: str
        cardinality: NotRequired[FieldCardinality]
        comment: NotRequired[Union[str, List[str]]]

    RequestResponseType = Union[List[FieldDict], Type[BaseSerializer], str, Placeholder]

==================================
``request_name`` ``response_name``
==================================

By default, the name of the request/response message is generated from the name of the action,
the name of the serializer if a serializer is used, and the service name.

# :TODO: please add an example of a generated name here

Those arguments are used to override this name.

======================================
``request_stream`` ``response_stream``
======================================

Those arguments are used to mark the RPC request/response as a stream.

==========================================
``use_request_list`` ``use_response_list``
==========================================

Those arguments are used to encapsulate the message inside a List message.
It is useful when returning a list of object with a serializer.

Use Cases
---------

=========================================
Basic ``FieldDict`` request and response:
=========================================

Example:
This ExampleService has a Retrieve action (RPC)  
that takes a uuid as argument and returns a username and a list of items:

.. code-block:: python

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


=======================
Serializers as messages
=======================


Serializers can be used to generate the response message as shown in the example below:
Here the ``UserProtoSerializer`` is used to generate the response message.

# :TODO: add the right imports in this example that the users can immediately copy/paste it

.. code-block:: python

    class UserProtoSerializer(BaseSerializer):
        username = serializers.CharField()

    class ExampleService(GenericService):
        ...

        pagination_class = PageNumberPagination

        @grpc_action(
            request=[],
            response=UserProtoSerializer,
            use_response_list=True,
        )
        async def List(self, request, context):
            ...

This is equivalent to:

.. code-block:: proto

    service ExampleService {
        rpc List(google.protobuf.Empty) returns (ListResponse) {}
    }

    message UserResponse {
        repeated string uuids = 1;
    }

    message UserListResponse {
        repeated UserResponse results = 1;
        int32 count = 2;
    }

Note that in the ``UserListResponse`` message, the ``results`` field is a ``UserResponse`` message,
it is the message generated from the ``UserProtoSerializer``.
There is also a ``count`` field which is the total number of results, it is present only
if the pagination is enabled.



=========
Streaming
=========

You can use the ``request_stream`` and ``response_stream`` arguments to mark the RPC as a stream,
as shown in the following example:

.. code-block:: python

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

Placeholders are objects that will be replaced in the service registration step.
They are useful when you want to use arguments that you want to override in subclasses.

They define a ``resolve`` method that will be called with
the service instance as argument.

.. code-block:: python

    # This placeholder always resolves to "MyRequest"
    class RequestNamePlaceholder(Placeholder):
        def resolve(self, service: GenericService):
            return "MyRequest"


In a service class, you can use placeholders in any of the ``grpc_action`` arguments:

# :TODO: please add the right imports in this example that the users can immediately copy/paste it

.. code-block:: python

    class ExampleSuperService(GenericService):

        @grpc_action(
            request=AttrPlaceholder("_request"),
            request_name=RequestNamePlaceholder,
            response=SelfSerializer,
            response_name = "MyResponse",
        )
        def Route(self, request, context):
            raise NotImplementedError

    class ExampleSubService(ExampleSuperService):

        serializer_class = MySerializer
        _request = []

        def Route(self, request, context):
            ...


This is equivalent to:

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

``FnPlaceholder``
~~~~~~~~~~~~~~~~~

Resolves to the result of a function.

.. code-block:: python

    def fn(service) -> str:
        return "Ok"

    FnPlaceholder(fn) == "Ok"


``AttrPlaceholder``
~~~~~~~~~~~~~~~~~~~

Resolves to a named class attribute of the service.

.. code-block:: python

    AttrPlaceholder("my_attribute") == service.my_attribute

``SelfSerializer``
~~~~~~~~~~~~~~~~~~

Resolves to the serializer_class of the service.


.. code-block:: python

    SelfSerializer == service.serializer_class


``StrTemplatePlaceholder``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Resolves to a string template with either service attributes names or
functions as parameter. It uses ``str.format`` to inject the values.

.. code-block:: python

    def fn(service) -> str:
        return "Ok"

    StrTemplatePlaceholder("{}Request{}", "My", fn) == "MyRequestOk"


``LookupField``
~~~~~~~~~~~~~~~

Resolves to the service lookup field message.

# :TODO: please explain the concept of a lookup field here (beginners will have not idea, what this is about)

.. code-block:: python

    class Serializer(BaseSerializer):
        uuid = serializers.CharField()

    class Service(GenericService):
        serializer_class = Serializer
        lookup_field = "uuid"

    LookupField == [{
        "name": "uuid",
        "type": "string", # This is the type of the field in the serializer
    }]

=============================
Force Message for Know Method
=============================

You can use the :ref:`grpc action <grpc_action>` decorator on the ``known`` method to override the default message that comes from :ref:`mixins <Generic Mixins>`.

.. code-block:: python

    class ExampleService(generics.AsyncModelService):
        queryset = SpecialFieldsModel.objects.all().order_by("uuid")
        serializer_class = SpecialFieldsModelSerializer

        @grpc_action(
            request=[{"name": "my_example_request", "type": "string"}],
            response=[{"name": "my_example_response", "type": "string"}],
        )
        async def Retrieve(self, request, context):
            pass

This will result in the following proto code after the proto generation with the ``generateproto`` command:

.. code-block:: proto

    import "google/protobuf/empty.proto";

    service ExampleController {
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

    class Service(GenericService):
        ...

        @grpc_action(
            request=[],
            response=[
                {
                    "name": "username",
                    "type": "string",
                    "comment": "This is a comment",
                },
            ],
        )
        async def Retrieve(self, request, context):
            ...


This is equivalent to:

.. code-block:: proto

    service Service {
        rpc Retrieve(RetrieveRequest) returns (RetrieveResponse) {}
    }

    message RetrieveRequest {
    }

    message RetrieveResponse {
        // This is another comment
        string username = 1;
    }
