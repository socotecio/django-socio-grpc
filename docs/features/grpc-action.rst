.. _grpc_action:
GRPCAction
==========

Description
-----------

With Django-Socio-GRPC you can declare a grpc action related to your app service with the decorator grpc_action. 
Once your service registered, it will create a new request and response in your .proto file after the proto generation.$

A gRPC action is a representation of an RPC inside the service wher it's declared which is composed of a request and a response :

.. code-block:: python

    rpc BasicList(BasicProtoListChildListRequest) returns (BasicProtoListChildListResponse) {}

It can also use a stream as a request/response.

The decorator signature is:

.. code-block:: python

    def grpc_action(request=None, response=None, request_name=None, response_name=None, request_stream=False, response_stream=False, use_request_list=False, use_response_list=False)

Usage
-----

======
Import
======

First of all, you need to import grpc_action

.. code-block:: python

    from django_socio_grpc.decorators import grpc_action 

This decorator can now be used for each action of your service.

========================
Request and Response arg
========================

The request argument can be:
    - an empty list if the request is empty
    - a list of dict:
        - name: name of the parameter
        - type: type of the parameter (string, int32, float, bool...)
        - cardinality: 
            - repeated: used when the parameter is a list 
            - optional: used when the parameter is optional
    - a serializer
    - a ProtoRequest name

The response argument can be:
    - "google.protobuf.Empty" (for an empty response) which is equivalent to []
    - a list of dict:
        - name: name of the parameter
        - type: type of the parameter (string, int32, float, bool...)
        - cardinality: 
            - repeated: used when the parameter is a list 
            - optional: used when the parameter is optional
    - a serializer
    - a ProtoResponse name

==================================
request_name and response_name arg
==================================

Those arguments are used to force a name for the request/response message

======================================
request_stream and response_stream arg
======================================

Those arguments are used to mark the request/response as a stream in the protobuf file

==========================================
use_request_list and use_response_list arg
==========================================

Those arguments are used to encapsulate the message inside a List message.
You need to use it if you return a serializer message with many=True at initialisation


Examples
^^^^^^^^

==========
Example 1:
==========

.. code-block:: python

    @grpc_action(request=ActionInputProtoSerializer, response=ActionProtoSerializer)
    async def Create(self, request, context):
        return await self._create(request)

After the proto generation, you will find in yourapp.proto file:

.. code-block:: python

    message MyAppCreateRequest {
        string uuid = 1;
        string foo = 2;
        int32 bar = 3;
    }

    message MyAppCreateResponse {
        string uuid = 1;
        string foo = 2;
        int32 bar = 3;
    }

==========
Example 2:
==========

.. code-block:: python

    @grpc_action(
        request="TestListRequest",
        response=TestListProtoSerializer,
        use_response_list=True,
    )
    async def List(self, request, context):
        return await super().List(request, context)

After the proto generation, you will find in yourapp.proto file:

.. code-block:: python

    message MyAppListRequest {
        repeated string uuids = 1;
    }

    message MyAppListResponse {
        repeated TestListResponse results = 1;
        int32 count = 2;
    }

==========
Example 3:
==========

.. code-block:: python

    @grpc_action(
        request=[
            {"name": "uuid", "type": "string"},
            {"name": "test_data", "type": "string"},
        ],
        response=SetTestDataProtoSerializer,
    )
    async def SetTestData(self, request, context):
        data = await self.aget_object()
        data.test = request.test
        await data.asave()
        response_serializer = self.get_serializer(data)
        return await agetattr(response_serializer, "message")

After the proto generation, you will find in yourapp.proto file:

.. code-block:: python

    message SetTestDataRequest {
        string uuid = 1;
        string test_data = 2:
    }

    message SetTestDataResponse {
        string uuid = 1;
        string test_data = 2:
        int32 foo = 3;
        int32 bar = 4;
        ...
    }