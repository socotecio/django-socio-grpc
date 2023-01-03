import inspect
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django_socio_grpc.servicer_proxy import GRPCRequestContainer


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


async def safe_async_response(fn, request: "GRPCRequestContainer", process_exceptions=None):
    """Allows to use async generator as response."""
    response = fn(request)

    if inspect.isasyncgen(response):

        async def async_generator():
            try:
                async for item in response:
                    yield item
            except Exception as e:
                if process_exceptions:
                    await process_exceptions(e, request)
                else:
                    raise e

        return async_generator()

    try:
        return await response
    except Exception as e:
        if process_exceptions:
            await process_exceptions(e, request)
        else:
            raise e


_is_generator = object()


def isgeneratorfunction(fn):
    return (
        inspect.isgeneratorfunction(fn)
        or inspect.isasyncgenfunction(fn)
        or getattr(fn, "_is_generator", False) is _is_generator
    )
