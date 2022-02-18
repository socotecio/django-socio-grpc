"""
# this file is inspirated by pytest-grpc to be able to use django TestCase
# https://github.com/kataev/pytest-grpc/blob/master/pytest_grpc/plugin.py
"""
import asyncio
import socket

import grpc
from asgiref.sync import async_to_sync, sync_to_async
from grpc._cython.cygrpc import _Metadatum

from grpc import aio


class FakeServer(object):
    def __init__(self):
        self.rpc_method_handlers = {}

    def add_generic_rpc_handlers(self, generic_rpc_handlers):
        from grpc._server import _validate_generic_rpc_handlers

        _validate_generic_rpc_handlers(generic_rpc_handlers)

        self.rpc_method_handlers.update(generic_rpc_handlers[0]._method_handlers)

    def _find_method_handler(self, method_full_rpc_name):
        return self.rpc_method_handlers[method_full_rpc_name]

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

class FakeStreamLogic:
    def __init__(self):
        self.stream_pipe = []
        self._invocation_metadata = []
        self.last_index_called = 0

    def write(self, data):
        self.stream_pipe.append(data)

    def read(self):
        new_index = self.last_index_called + 1
        if new_index > len(self.stream_pipe):
            return aio.EOF
        return self.stream_pipe[new_index]
        # for data in self.stream_pipe:
        #     yield data


class FakeContext(FakeStreamLogic):
    def __init__(self):
        self._invocation_metadata = []
        super().__init__()

    def abort(self, code, details):
        raise FakeRpcError(code, details)

    def invocation_metadata(self):
        return self._invocation_metadata


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


class FakeCall(FakeStreamLogic):
    def __init__(self, real_method, request, context ,*args, **kwargs):
        super().__init__()
        real_method(request, context)



class _MultiCallable:
    def __init__(self, channel, method_full_rpc_name, call_type=None, *args, **kwargs):
        print(f"__init__ _MultiCallable : {call_type} - {method_full_rpc_name}")
        assert call_type is not None, "Error in FakeChannel implementation"
        self._call_type = call_type 
        self._handler = channel.server._find_method_handler(method_full_rpc_name)
        super().__init__()
    
    def __call__(self, request=None, timeout=None, metadata=None, *args, **kwargs):
        print("__call__")
        real_method = getattr(self._handler, self._call_type)
        self.context = FakeContext()

        if asyncio.iscoroutinefunction(real_method):
            real_method = async_to_sync(real_method)
            self.context = FakeAsyncContext()

        if metadata:
            self.context._invocation_metadata.extend(
                (_Metadatum(k, v) for k, v in metadata)
            )

        return real_method(request, self.context)

    def with_call(self, *args, **kwargs):
        raise NotImplementedError

    def future(self, *args, **kwargs):
        raise NotImplementedError


class UnaryUnaryMultiCallable(_MultiCallable, grpc.UnaryUnaryMultiCallable):
    pass


class UnaryStreamMultiCallable(_MultiCallable, grpc.UnaryStreamMultiCallable):
    pass


class StreamUnaryMultiCallable(_MultiCallable, grpc.StreamUnaryMultiCallable):
    pass


class StreamStreamMultiCallable(_MultiCallable, grpc.StreamStreamMultiCallable):
    pass


class FakeChannel:
    def __init__(self, fake_server):
        self.server = fake_server
        self.context = FakeContext()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    # def unary_unary(self, *args, **kwargs):
    #     return self.fake_method("unary_unary", *args, **kwargs)

    # def unary_stream(self, *args, **kwargs):
    #     return self.fake_method("unary_stream", *args, **kwargs)

    # def stream_unary(self, *args, **kwargs):
    #     return self.fake_method("stream_unary", *args, **kwargs)

    # def stream_stream(self, *args, **kwargs):
    #     return self.fake_method("stream_stream", *args, **kwargs)


    def unary_unary(self, method, *args, **kwargs):
        print("unary_unary")
        return UnaryUnaryMultiCallable(self, method, call_type="unary_unary", *args, **kwargs)

    def unary_stream(self, method, *args, **kwargs):
        print("unary_stream")
        return UnaryStreamMultiCallable(self, method, call_type="unary_stream", *args, **kwargs)

    def stream_unary(self, method, *args, **kwargs):
        print("stream_unary")
        return StreamUnaryMultiCallable(self, method, call_type="stream_unary", *args, **kwargs)

    def stream_stream(self, method, *args, **kwargs):
        print("stream_stream")
        return StreamStreamMultiCallable(self, method, call_type="stream_stream", *args, **kwargs)


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
