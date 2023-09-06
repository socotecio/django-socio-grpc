GRPCAction
==========

Description
-----------

With Django-Socio-GRPC you can declare a grpc action related to your app service with the decorator grpc_action. 
Once your service registered, it will create a new request and response in your .proto file after the proto generation.$

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
            - optionnal: used when the parameter is optionnal
    - a serializer
    - a ProtoRequest name

The response argument can be:
    - "google.protobuf.Empty" (for an empty response)
    - a list of dict:
        - name: name of the parameter
        - type: type of the parameter (string, int32, float, bool...)
        - cardinality: 
            - repeated: used when the parameter is a list 
            - optionnal: used when the parameter is optionnal
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

.. code-block:: python

    @grpc_action(request=ActionInputProtoSerializer, response=ActionProtoSerializer)
    async def Create(self, request, context):
        return await self._create(request)

.. code-block:: python

    @grpc_action(
        request="ObservationStatementListRequest",
        response=FlatObservationStatementProtoSerializer,
        use_response_list=True,
    )
    async def FlatList(self, request, context):
        return await super().List(request, context)

.. code-block:: python

    @grpc_action(
        request=[
            {"name": "uuid", "type": "string"},
            {"name": "risk_assessment", "type": "string"},
        ],
        response=ObservationAggregateProtoSerializer,
    )
    async def SetRiskLevel(self, request, context):
        observation = await self.aget_object()
        observation.risk_assessment_id = request.risk_assessment
        await observation.asave()
        response_serializer = self.get_serializer(observation)
        return await agetattr(response_serializer, "message")