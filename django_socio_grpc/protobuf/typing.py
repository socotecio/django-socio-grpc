from typing import List, Optional, TypedDict, Union


class FieldDict(TypedDict):
    name: str
    type: str
    comment: Optional[Union[str, List[str]]]
