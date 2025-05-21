import types
from typing import TYPE_CHECKING

from rest_framework import serializers

from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.protobuf.proto_classes import get_proto_type
from django_socio_grpc.utils.constants import PARTIAL_UPDATE_FIELD_NAME

if TYPE_CHECKING:
    from django_socio_grpc.generics import GenericService


def get_serializer_class(service: "GenericService", action: str | None = None):
    if action:
        service = service.__class__()
        service.action = action
    return service.get_serializer_class()


def get_serializer_base_name(service: "GenericService", action: str | None = None):
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


def get_partial_update_request_from_serializer_class(serializer_class):
    """
    This metaclass exists so we can set the PARTIAL_UPDATE_FIELD_NAME variable as an attribute name of PartialUpdateMetaClass.
    This can be replaced by just declaring in your serializer:
    _partial_update_fields = serializers.ListField(child=serializers.CharField(), write_only=True)
    but this would not be dynamic if a constant changes or if we want it to be configurable in settings in the future.
    This metaclass should inherit from DRF SerializerMetaclass as serializer has it's own metaclass to add _declared_fields attribute
    Using PartialUpdateRequest.setattr is not enough as _declared_fields is done in metaclass so all fields should be declared before
    """
    # Get the metaclass of the serializer_class (likely SerializerMetaclass)
    base_meta = type(serializer_class)

    # Dynamically create a compatible PartialUpdateMetaClass
    class PartialUpdateMetaClass(base_meta):
        def __new__(cls, name, bases, attrs):
            attrs[PARTIAL_UPDATE_FIELD_NAME] = serializers.ListField(
                child=serializers.CharField()
            )
            for base in bases:
                cls.__annotations__ = {**base.__annotations__, **cls.__annotations__}
            return super().__new__(cls, name, bases, attrs)

    # Dynamically create the inner Meta class
    Meta = type("Meta", (serializer_class.Meta,), {})

    # Prepare the class namespace
    class_dict = {"Meta": Meta}

    # Dynamically create the final PartialUpdateRequest class
    new_class = types.new_class(
        serializer_class.__name__,
        (serializer_class,),
        {"metaclass": PartialUpdateMetaClass},
        lambda ns: ns.update(class_dict),  # Populate the namespace
    )

    # INFO - L.G. - 19/06/2022 - extra field needs to be appended to
    # the serializer.
    if (fields := getattr(new_class.Meta, "fields", None)) and not isinstance(fields, str):
        new_class.Meta.fields = (*fields, PARTIAL_UPDATE_FIELD_NAME)

    return new_class


def get_partial_update_request_from_service(service):
    serializer_class = service.get_serializer_class()
    return get_partial_update_request_from_serializer_class(serializer_class)
