from django_socio_grpc.protobuf.json_format import message_to_dict
from django_socio_grpc.protobuf.tests.protos import test_proto_pb2


def test_message_to_dict_include_optional_not_one_of():
    message = test_proto_pb2.MyMessage(string_field="test")

    result = message_to_dict(message)
    assert len(result) == 2
    assert result["string_field"] == "test"
    assert result["optional_string_field"] is None

    message = test_proto_pb2.MyMessage(string_field="test", optional_string_field="test")

    result = message_to_dict(message)
    assert len(result) == 2
    assert result["string_field"] == "test"
    assert result["optional_string_field"] == "test"
