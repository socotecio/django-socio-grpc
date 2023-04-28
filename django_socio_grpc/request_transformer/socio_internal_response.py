from dataclasses import dataclass, field
from typing import Dict


@dataclass
class InternalHttpResponse:
    """
    Class mocking django.http.HttpResponse to make some django behavior like middleware still work.
    TODO - AM - Inherit this directly from django.http.HttpResponse ?
    """

    # INFO - AM - 26/04/2023 - This is used by session middleware
    headers: Dict[str, str] = field(default_factory=dict)

    # INFO - AM - 26/04/2023 - This is used by local middleware
    # TODO - AM - 26/04/2023 - Adapt this code from the grpc_response abort details ? Not needed for now.
    status_code: str = "200"

    # INFO - AM - 26/04/2023 - This is used by session middleware
    def has_header(self, header_name):
        return False
