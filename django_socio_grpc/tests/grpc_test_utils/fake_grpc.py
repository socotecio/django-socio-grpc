"""
# this file is inspirated by pytest-grpc to be able to use django TestCase
# https://github.com/kataev/pytest-grpc/blob/master/pytest_grpc/plugin.py
"""
import asyncio
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


class FakeRpcError(RuntimeError, grpc.RpcError):
    def __init__(self, code, details):
        self._code = code
        self._details = details

    def code(self):
        return self._code

    def details(self):
        return self._details


class FakeContext:
    def __init__(self, stream_pipe=None, auto_eof=True):
        self.stream_pipe = queue.Queue()
        if stream_pipe is None:
            pass
        elif not isinstance(stream_pipe, Iterable):
            raise Exception("FakeContext stream pipe must be an iterable")
        else:
            for item in stream_pipe:
                self.stream_pipe.put(item)
        if stream_pipe is not None and auto_eof:
            self.stream_pipe.put(grpc.aio.EOF)

        self._invocation_metadata = []

    def __iter__(self):
        return self

    def __next__(self):
        response = self.read()
        if response == grpc.aio.EOF:
            raise StopIteration
        else:
            return response

    def abort(self, code, details):
        raise FakeRpcError(code, details)

    def invocation_metadata(self):
        return self._invocation_metadata

    def write(self, data):
        self.stream_pipe.put(data)

    def read(self):
        return self.stream_pipe.get_nowait()


class FakeAsyncContext(FakeContext):
    async def abort(self, code, details):
        await sync_to_async(super().abort)(code, details)

    async def write(self, data):
        await sync_to_async(super().write)(data)

    async def read(self):
        try:
            return await sync_to_async(super().read)()
        except queue.Empty:
            return grpc.aio.EOF


def get_brand_new_default_event_loop():
    try:
        old_loop = asyncio.get_event_loop()
        if not old_loop.is_closed():
            old_loop.close()
    except RuntimeError:
        # no default event loop, ignore exception
        pass
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    return _loop


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
        real_method = getattr(handler, method_name)

        def fake_handler(request=None, metadata=None):
            nonlocal real_method
            self.context = FakeContext()

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
        if self._metadata is None and metadata is not None:
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
        if self._metadata is None and metadata is not None:
            self._metadata = metadata
            self._context._invocation_metadata.extend((_Metadatum(k, v) for k, v in metadata))
        # TODO - AM - 18/02/2022 - Need to launch _real_method in a separate thread to be able to work with stream stream object
        self.method_awaitable = asyncio.create_task(
            self._real_method(request=self._request, context=self._context)
        )
        return self


class UnaryResponseMixin:
    def __await__(self):
        # TODO - AM - 10/08/2022 - https://github.com/grpc/grpc/blob/4df74f2b4c3ddc00e6607825b52cf82ee842d820/src/python/grpcio/grpc/aio/_call.py#L268
        # Need to implement CancelledError and EOF response
        response = yield from self.method_awaitable
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
        return await self._context.write(data)

    async def done_writing(self) -> None:
        self._is_done_writing = True


class StreamResponseMixin:
    def __aiter__(self):
        return self

    async def __anext__(self):
        response = await self.read()
        if response == grpc.aio.EOF:
            raise StopAsyncIteration()
        return response

    async def read(self):
        # INFO - AM - 11/08/2022 - while "self.method_awaitable is None" mean while the grpc method has not been call
        # while "not self.method_awaitable.done()" mean while the grpc method is not finish to be executed
        # while "not self._context.stream_pipe.empty()" mean while there is some message that need to be intrepreted from the context
        while (
            self.method_awaitable is None
            or not self.method_awaitable.done()
            or not self._context.stream_pipe.empty()
        ):
            # INFO - AM - 11/08/2022 - Get message in queue without waiting to avoid blocking the current loop
            response = await self._context.read()

            if response == grpc.aio.EOF:
                # INFO - AM - 11/08/2022 - if the queue is not empty no need to wait, just handle the next event.
                if self._context.stream_pipe.empty():
                    await asyncio.sleep(0.1)
            else:
                return response

        return grpc.aio.EOF


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
