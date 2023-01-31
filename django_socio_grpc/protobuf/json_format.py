from google.protobuf import descriptor
from google.protobuf.json_format import MessageToDict, ParseDict


def message_to_dict(message, **kwargs):
    kwargs.setdefault("including_default_value_fields", True)
    kwargs.setdefault("preserving_proto_field_name", True)

    result_dict = MessageToDict(message, **kwargs)
    optional_fields = {
        field.name: None
        for field in message.DESCRIPTOR.fields
        if field.label == descriptor.FieldDescriptor.LABEL_OPTIONAL
    }

    return {**optional_fields, **result_dict}


def parse_dict(js_dict, message, **kwargs):
    kwargs.setdefault("ignore_unknown_fields", True)
    return ParseDict(js_dict, message, **kwargs)
