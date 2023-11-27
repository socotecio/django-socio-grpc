import inspect
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django_socio_grpc.services.servicer_proxy import GRPCRequestContainer


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


async def safe_async_response(fn, request: "GRPCRequestContainer"):
    """Allows to use async generator as response."""
    response = fn(request)

    if inspect.isasyncgen(response):

        async def async_generator():
            async for item in response:
                yield item

        return async_generator()

    return await response


_is_generator = object()


def isgeneratorfunction(fn):
    return (
        inspect.isgeneratorfunction(fn)
        or inspect.isasyncgenfunction(fn)
        or getattr(fn, "_is_generator", False) is _is_generator
    )
