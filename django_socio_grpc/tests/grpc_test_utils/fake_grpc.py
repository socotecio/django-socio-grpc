"""
# this file is inspirated by pytest-grpc to be able to use django TestCase
# https://github.com/kataev/pytest-grpc/blob/master/pytest_grpc/plugin.py
"""
import asyncio
import inspect
import queue
import socket
from collections.abc import Iterable

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
    def __init__(self, stream_pipe=None, auto_eof=True):
        # INFO - FB - 11/10/2022 - When you run Stream to Stream, you have to write on different Queue
        # The stream_pip_client,  in which client writes requests and reads by the server
        self.stream_pipe_client = queue.Queue()

        # The stream_pipe_server, in which server writes responses and reads by the client
        self.stream_pipe_server = queue.Queue()
        if stream_pipe is None:
            pass
        elif not isinstance(stream_pipe, Iterable):
            raise Exception("FakeContext stream pipe must be an iterable")
        else:
            for item in stream_pipe:
                self.stream_pipe_server.put(item)
        if stream_pipe is not None and auto_eof:
            self.stream_pipe_server.put(grpc.aio.EOF)

        self._invocation_metadata = []
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

    def set_code(self, code):
        self._code = code

    def set_details(self, details):
        self._details = details

    def abort(self, code, details):
        self.set_code(code)
        self.set_details(details)
        raise _InactiveRpcError(code=code, details=details)

    def invocation_metadata(self):
        return self._invocation_metadata

    def write(self, data):
        self.stream_pipe_server.put(data)

    def _write_client(self, data):
        self.stream_pipe_client.put(data)

    def read(self):
        return self.stream_pipe_client.get_nowait()

    def _read_client(self):
        return self.stream_pipe_server.get_nowait()

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
    async def abort(self, code, details):
        await sync_to_async(super().abort)(code, details)

    async def write(self, data):
        await sync_to_async(super().write)(data)

    async def _write_client(self, data):
        await sync_to_async(super()._write_client)(data)

    async def read(self):
        return await self._read(self.stream_pipe_client)

    async def _read_client(self):
        return await self._read(self.stream_pipe_server)

    async def _read(self, pipe):
        count = 0
        while True:
            if count > 100:
                raise TimeoutError(
                    "Context read timeout, please make sure you are correctly "
                    "closing your stream with `stream_call.done_writing()`"
                )
            try:
                await asyncio.sleep(0.1)
                return pipe.get_nowait()
            except queue.Empty:
                count += 1


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
                self.context._invocation_metadata.extend(
                    (_Metadatum(k, v) for k, v in metadata)
                )

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
    def add_done_callback(*args, **kwargs):
        pass

    def cancel(*args, **kwargs):
        pass

    def cancelled(*args, **kwargs):
        pass

    def code(*args, **kwargs):
        pass

    def details(*args, **kwargs):
        pass

    def done(*args, **kwargs):
        pass

    def initial_metadata(*args, **kwargs):
        pass

    def time_remaining(*args, **kwargs):
        pass

    def trailing_metadata(*args, **kwargs):
        pass

    def wait_for_connection(*args, **kwargs):
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
            self._context._invocation_metadata.extend((_Metadatum(k, v) for k, v in metadata))

    def __call__(self, request=None, metadata=None):
        # INFO - AM - 28/07/2022 - request is not None at first call but then at each read is transformed to None. So we only assign it if not None
        if request is not None:
            self._request = request
        if metadata is not None:
            self._metadata = metadata
            self._context._invocation_metadata.extend((_Metadatum(k, v) for k, v in metadata))
        # TODO - AM - 18/02/2022 - Need to launch _real_method in a separate thread to be able to work with stream stream object
        self.method_awaitable = self._real_method(request=self._request, context=self._context)
        return self

    def __await__(self):
        response = self.method_awaitable.__await__()
        return response

    def write(self, data):
        async_to_sync(self._context.write)(data)

    def read(self):
        return async_to_sync(self._context.read)()


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
            self._context._invocation_metadata.extend((_Metadatum(k, v) for k, v in metadata))

    def __call__(self, request=None, metadata=None):
        # INFO - AM - 28/07/2022 - request is not None at first call but then at each read is transformed to None. So we only assign it if not None
        if request is not None:
            self._request = request
        if metadata is not None:
            self._metadata = metadata
            self._context._invocation_metadata.extend((_Metadatum(k, v) for k, v in metadata))

        async def wrapped(*args, **kwargs):
            method = self._real_method(request=self._request, context=self._context)
            try:
                if inspect.isasyncgen(method):
                    async for response in method:
                        await self._context.write(response)
                    await self._context.write(grpc.aio.EOF)
                    return
                else:
                    response = await method
                    await self._context.write(grpc.aio.EOF)
                    return response
            except Exception as e:
                # INFO - AM - 31/01/2023 - Need to write exception to context to have the exception raised in read client for stream response. This has no effect for unary response
                await self._context.write(e)
                # INFO - AM - 31/01/2023 - Return are for unary response
                return e

        # TODO - AM - 18/02/2022 - Need to launch _real_method in a separate thread to be able to work with stream stream object
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

    def __call__(self, request=None, metadata=None):
        if request is not None:
            raise ValueError("request must be None for stream calls")
        return super().__call__(request=FakeMessageReceiver(self._context), metadata=metadata)

    async def write(self, data):
        if self._is_done_writing:
            raise ValueError("write() is called after done_writing()")
        await self._context._write_client(data)

    async def done_writing(self) -> None:
        if not self._is_done_writing:
            await self.write(grpc.aio.EOF)
            self._is_done_writing = True


class StreamResponseMixin:
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
        return await self._context._read_client()


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
    """

    def __init__(self, context):
        self._servicer_context = context
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
        # Prevents never awaited warning if application never used the async generator
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
