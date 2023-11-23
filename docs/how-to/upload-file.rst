Upload file
===========

Description
-----------
When it comes to file uploads in gRPC, bidirectional or unidirectional streaming can be used. 
With bidirectional, the client and server sends a stream of messages to each other. This means that the client can send chunks of a file to the server as a stream, and the server can process these chunks in real-time.
With unidirectional, the client send a stream to the server. This means that the client send chunks of a file to the server as a stream, and the server can process these chunks when the stream is over.

Usage in unidirectional context
-------------------------------

Define a grpc_action with the ``request_stream=True`` attribute.
The client will sends a stream of messages as request to the server and the server will responds with a single message (along with its status details and optional trailing metadata), after it has received all the client’s messages.

.. code-block:: python

    class FileUploadService(GenericService):
        ...

        @grpc_action(
            request=[{"name": "data", "type": "bytes"}],
            request_name="FileChunk",
            response=[{"name": "success", "type": "bool"}],
            response_name="UploadStatus"
            request_stream=True,
        )
        async def UploadFile(self, request, context):
            ...

This is equivalent to:

.. code-block:: proto

    service FileUploadService {
        rpc UploadFile(stream FileChunk) returns (UploadStatus);
    }

    message FileChunk {
        bytes data = 1;
    }

    message UploadStatus {
        bool success = 1;
    }


Example
-------

On the client side:

.. code-block:: python

    import grpc
    import FileUpload_pb2
    import FileUpload_pb2_grpc

    def upload_file(stub, file_path):
        with open(file_path, 'rb') as file:
            for chunk in read_in_chunks(file):
                # Create a FileChunk message and send it to the server
                response = stub.UploadFile(FileUpload_pb2.FileChunk(data=chunk))
                print(f"Upload status: {response.success}")

    def read_in_chunks(file, chunk_size=1024):
        while True:
            data = file.read(chunk_size)
            if not data:
                break
            yield FileUpload_pb2.FileChunk(data=data)

    if __name__ == '__main__':
        channel = grpc.insecure_channel('localhost:50051')
        stub = FileUpload_pb2_grpc.FileUploadServiceStub(channel)
        upload_file(stub, 'path/to/your/file.txt')

On the server side:

.. code-block:: python

    class FileUploadService(GenericService):
        ...

        @grpc_action(
            request=[{"name": "data", "type": "bytes"}],
            request_name="FileChunk",
            response=[{"name": "success", "type": "bool"}],
            response_name="UploadStatus"
            request_stream="True",
        )
        async def UploadFile(self, request, context):
            result = await context.read()

            if result == aio.EOF:
                return FileUpload_pb2.UploadStatus(success=False)

            try:
                with io.BytesIO() as f:
                    while result != aio.EOF:
                        f.write(result.content)
                        result = await context.read()
                    f.seek(0)

                    # file_content contain the entire content of the BytesIO object
                    file_content=f.getvalue()

                    # process your binary file file_content as you want...

                return FileUpload_pb2.UploadStatus(
                    success=True
                )

            except Exception:
                LOGGER.exception("Document upload has failed…")
                return FileUpload_pb2.UploadStatus(success=False)