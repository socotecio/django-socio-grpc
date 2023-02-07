from enum import Enum
from typing import List, Optional, TypedDict, Union


class FieldCardinality(str, Enum):
    NONE = ""
    OPTIONAL = "optional"
    REPEATED = "repeated"
    # TODO: ONEOF = "oneof"
    # TODO: MAP = "map"


class FieldDict(TypedDict):
    name: str
    type: str
    cardinality: FieldCardinality
    comment: Optional[Union[str, List[str]]]
