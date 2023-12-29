from uuid import UUID

from google.protobuf import json_format
from google.protobuf.json_format import MessageToDict, ParseDict


def _is_field_optional(field):
    """
    Checks if a field is optional.

    Under the hood, Optional fields are OneOf fields with only one field with the name of the OneOf
    prefixed with an underscore.
    """

    if not (co := field.containing_oneof):
        return False

    return len(co.fields) == 1 and co.name == f"_{field.name}"


def message_to_dict(message, **kwargs):
    """
    Converts a protobuf message to a dictionary.
    Uses the default `google.protobuf.json_format.MessageToDict` function.
    Adds None values for optional fields that are not set.
    """

    kwargs.setdefault("including_default_value_fields", True)
    kwargs.setdefault("preserving_proto_field_name", True)

    result_dict = MessageToDict(message, **kwargs)
    optional_fields = {
        field.name: None for field in message.DESCRIPTOR.fields if _is_field_optional(field)
    }

    return {**optional_fields, **result_dict}


def parse_dict(js_dict, message, **kwargs):
    kwargs.setdefault("ignore_unknown_fields", True)
    return ParseDict(js_dict, message, **kwargs)


def _ConvertScalarFieldValue(value, *args, **kwargs):
    """
    We patch the json_format module to support UUIDs in ParseDict.
    By default, having a UUID in a message will raise a TypeError.
    """
    if isinstance(value, UUID):
        value = str(value)
    return _BaseConvertScalarFieldValue(value, *args, **kwargs)


# TODO: We'll have to find a better way not relying on private functions
#       to allow UUIDs in conversion.
#       Future rework of Serializers should solve this.

_BaseConvertScalarFieldValue = json_format._ConvertScalarFieldValue
json_format._ConvertScalarFieldValue = _ConvertScalarFieldValue
