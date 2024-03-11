from typing import TYPE_CHECKING, Optional

from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.protobuf.proto_classes import get_proto_type

if TYPE_CHECKING:
    from django_socio_grpc.generics import GenericService


def get_serializer_class(service: "GenericService", action: Optional[str] = None):
    if action:
        service = service.__class__()
        service.action = action
    return service.get_serializer_class()


def get_serializer_base_name(service: "GenericService", action: Optional[str] = None):
    serializer = get_serializer_class(service, action)
    return MessageNameConstructor.get_base_name_from_serializer(serializer)


def get_lookup_field_from_serializer(serializer_instance, service_instance):
    """
    Find the field associated to the lookup field
    serializer_instance: instance of the serializer used in this service where the lookup field should be present
    service_instance: the service instance itself where we can introspect for lookupfield

    return: iterable: [str, <drf.serializers.Field>]
    """
    field_name = service_instance.get_lookup_request_field()

    field_proto_type = get_proto_type(
        serializer_instance.fields[field_name],
        "lookup_field_type_not_found",
    )

    return (field_name, field_proto_type)
