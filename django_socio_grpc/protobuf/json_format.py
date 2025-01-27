from inspect import signature
from uuid import UUID

from google.protobuf import json_format
from google.protobuf.json_format import MessageToDict, ParseDict

# Since protobuf>=26 we have to use the "always_print_fields_with_no_presence" argument
if "including_default_value_fields" in signature(MessageToDict).parameters:
    _NO_PRESENCE_ARG = "including_default_value_fields"
else:
    _NO_PRESENCE_ARG = "always_print_fields_with_no_presence"


def message_to_dict(message, **kwargs):
    """
    Converts a protobuf message to a dictionary.
    Uses the default `google.protobuf.json_format.MessageToDict` function.
    Adds None values for optional fields that are not set.
    """
    kwargs.setdefault(_NO_PRESENCE_ARG, True)
    kwargs.setdefault("preserving_proto_field_name", True)

    return MessageToDict(message, **kwargs)


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
