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

import time
from typing import TYPE_CHECKING, Optional

from django.core.cache import caches
from django.utils.cache import (
    get_cache_key,
    get_max_age,
    has_vary_header,
    learn_cache_key,
    patch_response_headers,
)
from django.utils.http import parse_http_date_safe
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
    if key_prefix is None:
        key_prefix = grpc_settings.GRPC_CACHE_KEY_PREFIX
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
    if key_prefix is None:
        key_prefix = grpc_settings.GRPC_CACHE_KEY_PREFIX
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
    if key_prefix is None:
        key_prefix = grpc_settings.GRPC_CACHE_KEY_PREFIX
    cache = get_dsg_cache(cache_alias=cache_alias)
    cache_key = get_dsg_cache_key(request, key_prefix=key_prefix, method=method, cache=cache)
    print("cache key to get: ", cache_key)
    if cache_key is None:
        return None
    response = cache.get(cache_key)
    if response is None:
        return None
    response.set_current_context(request.grpc_context)

    max_age_seconds = get_max_age(response)

    expires_timestamp = parse_http_date_safe(response.get("Expires"))
    if expires_timestamp is not None and max_age_seconds is not None:
        now_timestamp = int(time.time())
        remaining_seconds = expires_timestamp - now_timestamp
        response["Age"] = max(0, max_age_seconds - remaining_seconds)

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
    # Don't cache responses that set a user-specific (and maybe security
    # sensitive) cookie in response to a cookie-less request.
    if not request.COOKIES and response.cookies and has_vary_header(response, "Cookie"):
        return

    if "private" in response.get("Cache-Control", ()):
        return

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
    print("cahce key to put: ", cache_key)

    timeout = get_max_age(response)
    print("timeout: ", timeout)
    # if the max_age_seconds is None, we will use the default cache_timeout
    if timeout is None:
        timeout = cache_timeout
    # if the max_age_seconds is 0, we will not cache the response
    elif timeout == 0:
        return

    patch_response_headers(response, timeout)

    return cache.set(key=cache_key, value=response, timeout=timeout)
