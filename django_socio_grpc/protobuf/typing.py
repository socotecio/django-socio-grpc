from __future__ import annotations

from enum import Enum

try:
    from typing_extensions import NotRequired, TypedDict
except ImportError:
    from typing import Optional as NotRequired
    from typing import TypedDict


class FieldCardinality(str, Enum):
    """
    Enum to use for the ``cardinality`` dictionnary key for grpc_action ``request`` and ``response``
    """

    NONE = ""
    OPTIONAL = "optional"
    REPEATED = "repeated"
    # TODO: ONEOF = "oneof"
    # TODO: MAP = "map"


class FieldDict(TypedDict):
    """
    Typed dict to help format ``request`` and ``response`` params of grpc_action decorator.
    """

    name: str
    type: str
    cardinality: NotRequired[FieldCardinality]
    comment: NotRequired[str | list[str]]
