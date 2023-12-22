.. _streaming:

Streaming
=========

Overview
--------

Server Streaming - ``unary-stream``
-----------------------------------

A streaming RPC is similar to a unary RPC, except that the server returns a stream of messages as response.
After sending all its messages, the server’s status details (status code and optional status message) and optional trailing metadata are sent to the client. This completes processing on the server side.
The client completes once it has all the server’s messages.

Client Streaming - ``stream-unary``
-----------------------------------

A client-streaming RPC is similar to a unary RPC, except that the client sends a stream of messages as request to the server instead of a single message.
The server responds with a single message (along with its status details and optional trailing metadata), typically but not necessarily after it has received all the client’s messages.

Bidirectional Streaming - ``stream-stream``
-------------------------------------------

In a bidirectional streaming RPC, the call is initiated by the client invoking the method and the server receiving the client metadata, method name, and deadline.
The server can choose to send back its initial metadata or wait for the client to start streaming messages.
Client- and server-side stream processing is application specific. Since the two streams are independent, the client and server can read and write messages in any order. For example, a server can wait until it has received all of a client’s messages before writing its messages, or the server and client can play “ping-pong”
the server gets a request, then sends back a response, then the client sends another request based on the response, and so on.

Example
-------

Full example in `Django Socio Grpc Example <https://github.com/socotecio/django-socio-grpc-example>`_

Server code:

.. code-block:: python

    from django_socio_grpc import generics
    from .models import Question
    from .serializers import QuestionProtoSerializer

    from django_socio_grpc.decorators import grpc_action
    from .grpc import app_example_pb2


    class QuestionService(generics.AsyncModelService):
        queryset = Question.objects.all()
        serializer_class = QuestionProtoSerializer

        @grpc_action(
            request=[{"name": "question_text","type": "string",}],
            response=[{"name": "response", "type": "string" }],
            request_stream=True,
            response_stream=True,
        )
        async def Stream(self, request, context):
            async for question in request:
                yield app_example_pb2.QuestionStreamResponse(response=f"{request.question_text}: I don't know i am only a simple stream")


Client code:

.. code-block:: python

    import asyncio
    import grpc
    from app_example.grpc import app_example_pb2_grpc, app_example_pb2

    async def main():
        async with grpc.aio.insecure_channel("localhost:50051") as channel:
            stub = app_example_pb2_grpc.QuestionControllerStub(channel)

            async def generate_requests():
                """
                You can add more complex logic here like user input or async behavior. 
                Please consider usind asyncio.queue if you want to populate message from the main thread.
                """
                yield app_example_pb2.QuestionStreamRequest(question_text="Do you like gRPC ?")
                yield app_example_pb2.QuestionStreamRequest(question_text="Do you work ?")
                yield app_example_pb2.QuestionStreamRequest(question_text="Do you do something ?")

            async for response_message in stub.Stream(generate_requests()):
                print(f"Server responded: {response_message.response}")


    if __name__ == "__main__":
        asyncio.run(main())
