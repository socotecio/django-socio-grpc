from django_socio_grpc.protobuf.proto_classes import FieldCardinality, ProtoField, EmptyMessage

class BaseGenerationPlugin:

    def __init__(self, service, base_name, appendable_name, prefix):
        error_message = "You try to instanciate a class that inherit from BaseGenerationPlugin. to do that you need to specify a %s attribute"

        assert self.field_name is not None, error_message.format("field_name")
        assert self.field_cardinality is not None, error_message.format("field_cardinality")
        assert self.field_type is not None, error_message.format("field_type")

    def check_condition(self, service, proto_message) -> bool:
        return True
    
    def transform_if_emtpy(self, service, proto_message, base_name, appendable_name, prefix):
        return proto_message

    def transform_proto_message(self, service, proto_message, base_name, appendable_name, prefix):

        if proto_message is EmptyMessage:
            proto_message = self.transform_if_emtpy(service, proto_message, base_name, appendable_name, prefix)

        if not self.check_condition(service, proto_message):
            return proto_message

        proto_message.fields.append(ProtoField.from_field_dict(
            {
                "name": self.field_name,
                "type": self.field_type,
                "cardinality": self.field_cardinality,
            }
        ))
        return proto_message

class BaseAddFieldGenerationPlugin(BaseGenerationPlugin):
    field_name = None
    field_cardinality = None
    field_type = None

class FilterGenerationPlugin(BaseAddFieldGenerationPlugin):
    field_name = "_filters"
    field_type = "google.protobuf.Struct"
    field_cardinality = FieldCardinality.OPTIONAL
    
    
class PaginationGenerationPlugin(BaseAddFieldGenerationPlugin):
    field_name = "_pagination"
    field_type = "google.protobuf.Struct"
    field_cardinality = FieldCardinality.OPTIONAL