"""
# this file is inspirated by pytest-grpc to be able to use django TestCase
# https://github.com/kataev/pytest-grpc/blob/master/pytest_grpc/plugin.py
"""

import asyncio
import inspect
import queue
import socket

import grpc
from asgiref.sync import async_to_sync, sync_to_async
from grpc._cython.cygrpc import _Metadatum


class FakeServer:
    def __init__(self):
        self.handlers = {}

    def add_generic_rpc_handlers(self, generic_rpc_handlers):
        from grpc._server import _validate_generic_rpc_handlers

        _validate_generic_rpc_handlers(generic_rpc_handlers)

        self.handlers.update(generic_rpc_handlers[0]._method_handlers)

    def start(self):
        pass

    def stop(self, grace=None):
        pass

    def add_secure_port(self, target, server_credentials):
        pass

    def add_insecure_port(self, target):
        pass

    def add_registered_method_handlers(self, *args, **kwargs):
        pass


class _InactiveRpcError(grpc.RpcError):
    """
    From `grpc._channel._InactiveRpcError`
    """

    def __init__(self, code, details):
        super().__init__(code, details)
        self._code = code
        self._details = details

    def code(self):
        return self._code

    def details(self):
        return self._details


class _BaseFakeContext:
    def __init__(self):
        # INFO - FB - 11/10/2022 - When you run Stream to Stream, you have to write on different Queue
        # The stream_pip_client,  in which client writes requests and reads by the server
        self.stream_pipe_client = queue.Queue()

        # The stream_pipe_server, in which server writes responses and reads by the client
        self.stream_pipe_server = queue.Queue()

        self._invocation_metadata = ()
        self._trailing_metadata = ()
        self._code = grpc.StatusCode.OK
        self._details = None

    def __iter__(self):
        return self

    def __next__(self):
        response = self.read()
        if response == grpc.aio.EOF:
            raise StopIteration
        else:
            return response

    def invocation_metadata(self):
        return self._invocation_metadata

    def _check_metadata(self, metadata):
        """
        Custom method of _BaseFakeContext to be sure tests match reality because grpc metadata should be a tuple of tuple with first element a lower case string and the second a str or bytes value type
        """
        for k, value in metadata:
            if not k.islower():
                raise ValueError("Metadata keys must be lower case <invocation_metadata>", k)
            if not isinstance(value, str) and not isinstance(value, bytes):
                raise ValueError(
                    f"Metadata values must be str or bytes <invocation_metadata>. Exception for key {k}.",
                    value,
                )

    def set_invocation_metadata(self, metadata):
        self._check_metadata(metadata)
        self._invocation_metadata = tuple(_Metadatum(k, v) for k, v in metadata)

    def trailing_metadata(self):
        return self._trailing_metadata

    def set_trailing_metadata(self, metadata):
        self._check_metadata(metadata)
        self._trailing_metadata = tuple(_Metadatum(k, v) for k, v in metadata)

    def set_code(self, code):
        self._code = code

    def set_details(self, details):
        self._details = details

    def abort(self, code, details):
        self.set_code(code)
        self.set_details(details)
        raise _InactiveRpcError(code=code, details=details)

    def write(self, data):
        self._write_server(data)

    def _write_server(self, data):
        self.stream_pipe_server.put(data)

    def _write_client(self, data):
        self.stream_pipe_client.put(data)

    def read(self):
        return self._read_client()

    def _read_server(self):
        return self.stream_pipe_server.get_nowait()

    def _read_client(self):
        return self.stream_pipe_client.get_nowait()

    def code(self):
        return self._code

    def details(self):
        return self._details


class FakeState:
    aborted = False


class FakeContext(_BaseFakeContext):
    def __init__(self, *args, **kwargs):
        self._state = FakeState()
        super().__init__(*args, **kwargs)

    def abort(self, code, details):
        self._state.aborted = True
        return super().abort(code, details)


class FakeAsyncContext(_BaseFakeContext):
    timeout_count = 100

    async def abort(self, code, details):
        await sync_to_async(super().abort)(code, details)

    async def write(self, data):
        await self._write_server(data)

    async def _write_client(self, data):
        await sync_to_async(super()._write_client)(data)

    async def _write_server(self, data):
        await sync_to_async(super()._write_server)(data)

    async def _read_server(self):
        return await self._read(self.stream_pipe_server)

    async def _read_client(self):
        return await self._read(self.stream_pipe_client)

    async def _read(self, pipe, wait=True):
        count = 0
        while True:
            if count > self.timeout_count:
                raise TimeoutError(
                    "Context read timeout, please make sure you are correctly "
                    "closing your stream with `stream_call.done_writing()`"
                )
            try:
                await asyncio.sleep(0.1)
                return pipe.get_nowait()
            except queue.Empty as e:
                if wait:
                    count += 1
                else:
                    raise e


class FakeChannel:
    def __init__(self, fake_server):
        self.server = fake_server
        self.context = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def fake_method(self, method_name, uri, *args, **kwargs):
        handler = self.server.handlers[uri]

        def fake_handler(request=None, metadata=None):
            self.context = FakeContext()
            real_method = getattr(handler, method_name)

            if asyncio.iscoroutinefunction(real_method):
                real_method = async_to_sync(real_method)
                self.context = FakeAsyncContext()

            if metadata:
                metadata = self.context.invocation_metadata() + tuple(
                    _Metadatum(k, v) for k, v in metadata
                )
                self.context.set_invocation_metadata(metadata)

            return real_method(request, self.context)

        return fake_handler

    def unary_unary(self, *args, **kwargs):
        return self.fake_method("unary_unary", *args, **kwargs)

    def unary_stream(self, *args, **kwargs):
        return self.fake_method("unary_stream", *args, **kwargs)

    def stream_unary(self, *args, **kwargs):
        return self.fake_method("stream_unary", *args, **kwargs)

    def stream_stream(self, *args, **kwargs):
        return self.fake_method("stream_stream", *args, **kwargs)


class FakeGRPC:
    def __init__(self, grpc_add_to_server, grpc_servicer):
        self.grpc_addr = self.get_grpc_addr()

        self.grpc_server = self.get_fake_server()

        grpc_add_to_server(grpc_servicer, self.grpc_server)
        self.grpc_server.add_insecure_port(self.grpc_addr)
        self.grpc_server.start()

        self.grpc_channel = self.get_fake_channel()

    def close(self):
        self.grpc_server.stop(grace=None)

    def get_fake_server(self):
        grpc_server = FakeServer()
        return grpc_server

    def get_fake_channel(self):
        return FakeChannel(self.grpc_server)

    @staticmethod
    def get_grpc_addr():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("localhost", 0))
        return f"localhost:{sock.getsockname()[1]}"

    def get_fake_stub(self, grpc_stub_cls):
        return grpc_stub_cls(self.grpc_channel)


class FakeBaseCall(grpc.aio.Call):
    def add_done_callback(self, *args, **kwargs):
        pass

    def cancel(self, *args, **kwargs):
        pass

    def cancelled(self, *args, **kwargs):
        pass

    def code(self, *args, **kwargs):
        pass

    def details(self, *args, **kwargs):
        pass

    def done(self, *args, **kwargs):
        pass

    def initial_metadata(self, *args, **kwargs):
        return self._context._invocation_metadata

    def time_remaining(self, *args, **kwargs):
        pass

    def trailing_metadata(self, *args, **kwargs):
        return self._context._trailing_metadata

    def wait_for_connection(self, *args, **kwargs):
        pass


class FakeAioCall(FakeBaseCall):
    _is_coroutine = asyncio.coroutines._is_coroutine

    def __init__(self, context=None, call_type=None, real_method=None, metadata=None):
        self._call_type = call_type
        self._context = context
        self._real_method = real_method
        self._metadata = None
        self._request = None
        self.method_awaitable = None

        if metadata:
            self._metadata = metadata
            metadata = self._context.invocation_metadata() + tuple(
                _Metadatum(k, v) for k, v in metadata
            )
            self._context.set_invocation_metadata(metadata)

    def __call__(self, request=None, metadata=None):
        # INFO - AM - 28/07/2022 - request is not None at first call but then at each read is transformed to None. So we only assign it if not None
        if request is not None:
            self._request = request
        if metadata is not None:
            self._metadata = metadata
            metadata = self._context.invocation_metadata() + tuple(
                _Metadatum(k, v) for k, v in metadata
            )
            self._context.set_invocation_metadata(metadata)
        # INFO - AM - 18/02/2022 - Use FakeFullAioCall for stream testing
        self.method_awaitable = self._real_method(request=self._request, context=self._context)
        return self

    def __await__(self):
        response = self.method_awaitable.__await__()
        return response

    def write(self, data):
        async_to_sync(self._context.write)(data)

    def read(self):
        return async_to_sync(self._context.read)()

    def with_call(self, request=None, metadata=None):
        return self.__call__(request, metadata), self


# INFO - AM - 10/08/2022 - FakeFullAioCall use async function where FakeFullAioCall use async_to_sync
class FakeFullAioCall(FakeBaseCall):
    def __init__(self, context=None, call_type=None, real_method=None, metadata=None):
        self._call_type = call_type
        self._context: FakeAsyncContext = context
        self._real_method = real_method
        self._metadata = None
        self._request = None
        self.method_awaitable = None

        if metadata:
            self._metadata = metadata
            metadata = self._context.invocation_metadata() + tuple(
                _Metadatum(k, v) for k, v in metadata
            )
            self._context.set_invocation_metadata(metadata)

    def __call__(self, request=None, metadata=None):
        # INFO - AM - 28/07/2022 - request is not None at first call but then at each read is transformed to None. So we only assign it if not None
        if request is not None:
            self._request = request
        if metadata is not None:
            self._metadata = metadata
            metadata = self._context.invocation_metadata() + tuple(
                _Metadatum(k, v) for k, v in metadata
            )
            self._context.set_invocation_metadata(metadata)

        async def wrapped(*args, **kwargs):
            method = self._real_method(request=self._request, context=self._context)
            try:
                if inspect.isasyncgen(method):
                    async for response in method:
                        await self._context._write_server(response)
                    await self._context._write_server(grpc.aio.EOF)
                    return
                else:
                    response = await method
                    await self._context._write_server(grpc.aio.EOF)
                    return response
            except Exception as e:
                # INFO - AM - 31/01/2023 - Need to write exception to context to have the exception raised in read client for stream response. This has no effect for unary response
                await self._context._write_server(e)
                # INFO - AM - 31/01/2023 - Return are for unary response
                return e

        self.method_awaitable = asyncio.create_task(
            wrapped(request=self._request, context=self._context)
        )
        return self


class UnaryResponseMixin:
    def __await__(self):
        # TODO - AM - 10/08/2022 - https://github.com/grpc/grpc/blob/4df74f2b4c3ddc00e6607825b52cf82ee842d820/src/python/grpcio/grpc/aio/_call.py#L268
        response = yield from self.method_awaitable
        if isinstance(response, Exception):
            raise response
        return response


class StreamRequestMixin:
    _is_done_writing = False
    _request = None
    _context: FakeAsyncContext
    _populator_task = None

    async def _async_context_populater(self, request):
        """
        This method will be launched in an other loop to be able to populate the stream client pipe without blocking the main thread
        If the request is a generator it will also write grpc.aio.EOF to let the test finish correctly
        """
        if inspect.isasyncgen(request):
            async for message in request:
                await self.write(message)

            await self.write(grpc.aio.EOF)

        elif inspect.isgenerator(request):
            for message in request:
                await self.write(message)

            await self.write(grpc.aio.EOF)
        else:
            await self.write(request)

    def __call__(self, request=None, metadata=None):
        # INFO - AM - 05/01/2024 - launch the read of the client stream in an other thread
        self._populator_task = asyncio.create_task(self._async_context_populater(request))
        return super().__call__(
            request=FakeMessageReceiver(request=request, context=self._context),
            metadata=metadata,
        )

    async def write(self, data):
        if self._is_done_writing:
            raise ValueError("write() is called after done_writing()")
        await self._context._write_client(data)

    async def done_writing(self) -> None:
        if not self._is_done_writing:
            await self.write(grpc.aio.EOF)
            self._is_done_writing = True


class StreamResponseMixin:
    _context: FakeAsyncContext

    def __aiter__(self):
        return self

    async def __anext__(self):
        response = await self.read()
        if isinstance(response, Exception):
            raise response
        if response == grpc.aio.EOF:
            raise StopAsyncIteration()
        return response

    async def read(self):
        return await self._context._read_server()


class FakeFullAioStreamUnaryCall(
    StreamRequestMixin, FakeFullAioCall, UnaryResponseMixin, grpc.aio.StreamUnaryCall
):
    pass


class FakeFullAioStreamStreamCall(
    StreamRequestMixin, FakeFullAioCall, StreamResponseMixin, grpc.aio.StreamStreamCall
):
    pass


class FakeFullAioUnaryStreamCall(
    FakeFullAioCall, StreamResponseMixin, grpc.aio.UnaryStreamCall
):
    pass


class FakeFullAioUnaryUnaryCall(FakeFullAioCall, UnaryResponseMixin, grpc.aio.UnaryUnaryCall):
    pass


class FakeMessageReceiver:
    """
    From `grpc._cython.cygrpc._MessageReceiver`
    This allow to transform the request in a stream request that is a generator
    into an other generator that read the first one in an other thread to not block the thread when using stream to stream
    """

    def __init__(self, request, context):
        self._request = request
        self._servicer_context: FakeAsyncContext = context
        self._agen = None

    async def _async_message_receiver(self):
        """An async generator that receives messages."""
        while True:
            message = await self._servicer_context.read()
            if message is not grpc.aio.EOF:
                yield message
            else:
                break

    def __aiter__(self):
        if self._agen is None:
            self._agen = self._async_message_receiver()
        return self._agen

    async def __anext__(self):
        return await self.__aiter__().__anext__()


class FakeAIOChannel(FakeChannel):
    def fake_method(self, method_name, uri, *args, **kwargs):
        handler = self.server.handlers[uri]
        real_method = getattr(handler, method_name)
        self.context = FakeAsyncContext()

        return FakeAioCall(
            context=self.context, call_type=method_name, real_method=real_method
        )


# INFO - AM - 10/08/2022 - FakeFullAIOChannel use async function where FakeAIOChannel use async_to_sync
class FakeFullAIOChannel(FakeChannel):
    def fake_method(self, method_name, uri, *args, **kwargs):
        handler = self.server.handlers[uri]
        real_method = getattr(handler, method_name)
        self.context = FakeAsyncContext()

        # INFO - LG - 05/10/2022 - Using the right call type
        # https://github.com/grpc/grpc/blob/abde72280d88c0a0b8e25efc6f810cd702b21f07/src/python/grpcio/grpc/_cython/_cygrpc/aio/server.pyx.pxi#L795

        if handler.request_streaming and not handler.response_streaming:
            return FakeFullAioStreamUnaryCall(
                context=self.context, call_type=method_name, real_method=real_method
            )

        if handler.request_streaming and handler.response_streaming:
            return FakeFullAioStreamStreamCall(
                context=self.context, call_type=method_name, real_method=real_method
            )

        if not handler.request_streaming and handler.response_streaming:
            return FakeFullAioUnaryStreamCall(
                context=self.context, call_type=method_name, real_method=real_method
            )

        return FakeFullAioUnaryUnaryCall(
            context=self.context, call_type=method_name, real_method=real_method
        )


class FakeAIOGRPC(FakeGRPC):
    def get_fake_channel(self):
        return FakeAIOChannel(self.grpc_server)


# INFO - AM - 10/08/2022 - FakeFullAIOGRPC use async function where FakeAIOGRPC use async_to_sync
class FakeFullAIOGRPC(FakeGRPC):
    def get_fake_channel(self):
        return FakeFullAIOChannel(self.grpc_server)
