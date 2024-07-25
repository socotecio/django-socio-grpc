"""
This file provide tools to enable caching feature into django-socio-grpc.

This is not an easy deal as gRPC use POST request. There is open discussion about supporting it directly in gRPC but in low priority. See:
https://github.com/grpc/grpc/issues/7945

Connect now support it by using get request but has no python client yet:
https://buf.build/blog/introducing-connect-cacheable-rpcs

Also, there is the django basic way based on the cache system, But only working with GET or HEAD request.
Also second, the basic django cache middleware are used to cache django page and not gRPC response
https://docs.djangoproject.com/fr/5.0/topics/cache/

Waiting for an integrated gRPC solution, we will use a custom cache system based on django cache system.
This implementation is limited as it is not working correctly with Cache-Control header.
Also as gRPC as no meaning to cache all it's endpoint, we decided to just implement a simple decorator and avoid a middleware that need to be transformed as decorator.
This file implement the tools that use the cache decorator.

Django code to cache middleware and decorators:
https://github.com/django/django/blob/main/django/middleware/cache.py
https://github.com/django/django/blob/main/django/views/decorators/cache.py
https://github.com/django/django/blob/main/django/utils/cache.py
"""

from typing import TYPE_CHECKING, Optional

from django.core.cache import caches
from django.utils.cache import get_cache_key, learn_cache_key

from django_socio_grpc.settings import grpc_settings

if TYPE_CHECKING:
    from django.core.cache import BaseCache

    from django_socio_grpc.request_transformer import (
        GRPCInternalProxyContext,
        GRPCInternalProxyResponse,
    )


def get_dsg_cache(cache_alias: Optional[str] = None) -> "BaseCache":
    """
    Get a cache instance by name.
    """
    if cache_alias is None:
        cache_alias = grpc_settings.GRPC_CACHE_ALIAS
    return caches[cache_alias]


def get_dsg_cache_key(
    request: "GRPCInternalProxyContext",
    key_prefix: Optional[str] = None,
    method: str = "POST",
    cache: Optional["BaseCache"] = None,
) -> str:
    """
    Return a cache key based on the request information.
    To understand the format please read the desription of the learn_dsg_cache_key function.
    """
    if cache is None:
        cache = get_dsg_cache()
    cache_key = get_cache_key(
        request,
        key_prefix=key_prefix,
        method=method,
        cache=cache,
    )
    return cache_key


def learn_dsg_cache_key(
    request: "GRPCInternalProxyContext",
    response: "GRPCInternalProxyResponse",
    cache_timeout: Optional[int] = None,
    key_prefix: Optional[str] = None,
    cache: Optional["BaseCache"] = None,
) -> str:
    """
    Learn a cache key for the request and response.

    return a string looking like:
    views.decorators.cache.cache_page..POST.2ce1478f6873a3f0e477c7f91a4aeee0.d41d8cd98f00b204e9800998ecf8427e.en-us.UTC
    which is explained like:
    <origin: Fix>.<middleware or method: Fixed>.<cache: Fixed>.<cache_page: Fixed>.<key_prefix: Dynamic>.<method: Dynamic>.<url hexdigest: dynamic>.<headers hexdigest: dynamic>.<accept-language: dynamic>.<timezone: dynamic>
    """
    if cache is None:
        cache = get_dsg_cache()
    cache_key = learn_cache_key(
        request,
        response,
        cache_timeout=cache_timeout,
        key_prefix=key_prefix,
        cache=cache,
    )

    return cache_key


def get_response_from_cache(
    request: "GRPCInternalProxyContext",
    key_prefix: Optional[str] = None,
    method: str = "POST",
    cache_alias: Optional[str] = None,
) -> "GRPCInternalProxyResponse":
    """
    Get the cache key from the request and return the response stored with this key in
    """
    cache = get_dsg_cache(cache_alias=cache_alias)
    cache_key = get_dsg_cache_key(request, key_prefix=key_prefix, method=method, cache=cache)
    if cache_key is None:
        return None
    response = cache.get(cache_key)
    if response is None:
        return None

    return response


def put_response_in_cache(
    request: "GRPCInternalProxyContext",
    response: "GRPCInternalProxyResponse",
    cache_timeout: Optional[int] = None,
    key_prefix: Optional[str] = None,
    cache_alias: Optional[str] = None,
) -> None:
    """
    Persist a response in the cache.
    """
    cache = get_dsg_cache(cache_alias=cache_alias)
    if cache_timeout is None:
        cache_timeout = grpc_settings.GRPC_CACHE_SECONDS
    if key_prefix is None:
        key_prefix = grpc_settings.GRPC_CACHE_KEY_PREFIX
    cache_key = learn_dsg_cache_key(
        request,
        response,
        cache_timeout=cache_timeout,
        key_prefix=key_prefix,
        cache=cache,
    )

    return cache.set(cache_key, response, cache_timeout)
