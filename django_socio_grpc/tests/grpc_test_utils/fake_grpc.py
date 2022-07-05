"""
# this file is inspirated by pytest-grpc to be able to use django TestCase
# https://github.com/kataev/pytest-grpc/blob/master/pytest_grpc/plugin.py
"""
import asyncio
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


class FakeRpcError(RuntimeError, grpc.RpcError):
    def __init__(self, code, details):
        self._code = code
        self._details = details

    def code(self):
        return self._code

    def details(self):
        return self._details


class FakeContext:
    def __init__(self):
        self.stream_pipe = []
        self._invocation_metadata = []
        self.last_index_called = -1

    def abort(self, code, details):
        raise FakeRpcError(code, details)

    def invocation_metadata(self):
        return self._invocation_metadata

    def write(self, data):
        self.stream_pipe.append(data)

    def read(self):
        new_index = self.last_index_called + 1
        self.last_index_called = new_index
        if new_index >= len(self.stream_pipe):
            return grpc.aio.EOF
        return self.stream_pipe[new_index]


class FakeAsyncContext(FakeContext):
    async def abort(self, code, details):
        await sync_to_async(super().abort)(code, details)

    async def write(self, data):
        await sync_to_async(super().write)(data)

    async def read(self):
        return await sync_to_async(super().read)()


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
        self.context = FakeContext()

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


class FakeAioCall(grpc.aio.Call):
    def __init__(self, context=None, call_type=None, real_method=None, metadata=None):
        self._call_type = call_type
        self._context = context
        self._real_method = real_method

        if metadata:
            self._grpc_channel.context._invocation_metadata.extend(
                (_Metadatum(k, v) for k, v in metadata)
            )

    def __call__(self, request=None):
        self._request = request
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


class FakeAIOChannel(FakeChannel):
    def fake_method(self, method_name, uri, *args, **kwargs):
        handler = self.server.handlers[uri]
        real_method = getattr(handler, method_name)
        self.context = FakeAsyncContext()

        return FakeAioCall(
            context=self.context, call_type=method_name, real_method=real_method
        )


class FakeAIOGRPC(FakeGRPC):
    def get_fake_channel(self):
        return FakeAIOChannel(self.grpc_server)
