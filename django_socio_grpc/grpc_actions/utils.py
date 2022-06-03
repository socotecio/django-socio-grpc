from typing import TYPE_CHECKING, Optional

from django_socio_grpc.utils.registry_singleton import (
    get_message_name_from_field_or_serializer_instance,
)

if TYPE_CHECKING:
    from django_socio_grpc.generics import GenericService


def get_serializer_class(service: "GenericService", action: Optional[str] = None):
    if action:
        service = service.__class__()
        service.action = action
    return service.get_serializer_class()


def get_serializer_base_name(service: "GenericService", action: Optional[str] = None):
    serializer = get_serializer_class(service, action)()
    return get_message_name_from_field_or_serializer_instance(serializer, append_type=False)
