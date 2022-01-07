import io
import logging

from django.db import models
from django.db.models.query_utils import select_related_descend
from rest_framework.relations import ManyRelatedField, RelatedField
from rest_framework.serializers import BaseSerializer, ListSerializer

from django_socio_grpc.exceptions import ProtobufGenerationException
from django_socio_grpc.proto_serializers import ModelProtoSerializer, BaseProtoSerializer, ListProtoSerializer

from django_socio_grpc.utils import model_meta

logger = logging.getLogger("django_socio_grpc")


class ModelProtoGenerator:
    type_mapping = {
        # Special
        models.JSONField.__name__: "google.protobuf.Struct",
        # Numeric
        models.AutoField.__name__: "int32",
        models.SmallIntegerField.__name__: "int32",
        models.IntegerField.__name__: "int32",
        models.BigIntegerField.__name__: "int64",
        models.PositiveSmallIntegerField.__name__: "int32",
        models.PositiveIntegerField.__name__: "int32",
        models.FloatField.__name__: "float",
        models.DecimalField.__name__: "string",
        # Boolean
        models.BooleanField.__name__: "bool",
        models.NullBooleanField.__name__: "bool",
        # Date and time
        models.DateField.__name__: "string",
        models.TimeField.__name__: "string",
        models.DateTimeField.__name__: "string",
        models.DurationField.__name__: "string",
        # String
        models.CharField.__name__: "string",
        models.TextField.__name__: "string",
        models.EmailField.__name__: "string",
        models.SlugField.__name__: "string",
        models.URLField.__name__: "string",
        models.UUIDField.__name__: "string",
        models.GenericIPAddressField.__name__: "string",
        models.FilePathField.__name__: "string",
        # Default
        models.Field.__name__: "string",
    }

    def __init__(self, registry_instance, project_name, verbose=0, only_messages=None):
        self.registry_instance = registry_instance
        self.project_name = project_name
        self.verbose = verbose
        self.only_messages = only_messages if only_messages is not None else []
        self.current_message = ""


        # TODO for debug remove this after
        self.verbose = 4
        self.only_messages = ["RelatedFieldModel"]

    def print(self, message, verbose_level=0):
        # INFO - AM - 07/01/2022 - This is used to debug only one message. This is manual code. 
        if self.current_message not in self.only_messages:
            return
        if verbose_level <= self.verbose:
            print(message)

    def get_protos_by_app(self):
        proto_by_app = {}
        for app_name, registered_items in self.registry_instance.registered_app.items():
            self.print("\n\n--------------------------------\n\n", 1)
            self.print(f"GENERATE APP {app_name}", 1)
            proto_by_app[app_name] = self.get_proto(app_name, registered_items)

        return proto_by_app

    def get_proto(self, app_name, registered_items):
        self._writer = _CodeWriter()

        self._writer.write_line('syntax = "proto3";')
        self._writer.write_line("")
        self._writer.write_line(f"package {self.project_name}.{app_name};")
        self._writer.write_line("")
        self._writer.write_line("IMPORT_PLACEHOLDER")
        for grpc_controller_name, grpc_methods in registered_items[
            "registered_controllers"
        ].items():
            self._generate_controller(grpc_controller_name, grpc_methods)

        for grpc_message_name, grpc_message in registered_items["registered_messages"].items():
            self._generate_message(grpc_message_name, grpc_message)

        return self._writer.get_code()

    def _generate_controller(self, grpc_controller_name, grpc_methods):

        if not grpc_methods:
            return

        self._writer.write_line(f"service {grpc_controller_name} {{")
        with self._writer.indent():
            for method_name, method_data in grpc_methods.items():
                request_message = self.construct_method_message(
                    method_data.get("request", dict())
                )
                response_message = self.construct_method_message(
                    method_data.get("response", dict())
                )
                self._writer.write_line(
                    f"rpc {method_name}({request_message}) returns ({response_message}) {{}}"
                )
        self._writer.write_line("}")
        self._writer.write_line("")

    def construct_method_message(self, method_info):
        """
        transform a method_info of type {is_stream: <boolean>, message: <string>} to a rpc parameter or return value.

        return value example: "stream MyModelRetrieveRequest"
        """
        # Default to google.protobuf.Empty
        grpc_message = method_info.get("message", "google.protobuf.Empty")
        if grpc_message == "google.protobuf.Empty":
            self._writer.import_empty = True
        return f"{'stream ' if method_info.get('is_stream', False) else ''}{grpc_message}"

    def _generate_message(self, grpc_message_name, grpc_message_fields):
        """
        Take a model and smartly decide why messages and which field for each message to write in the protobuf file.
        It use the model._meta.grpc_messages if exist or use the default configurations
        """

        self.current_message = grpc_message_name

        self.print("\n------\n", 2)
        self.print(f"GENERATE MESSAGE: {grpc_message_name}", 2)
        self.print(grpc_message_fields, 3)

        # if len(grpc_message_fields) > 0:
        #     print("lalalaal ", grpc_message_fields[0][1])
        #     print("lalalaal ", grpc_message_fields[0][1].__class__.__name__)

        self._writer.write_line(f"message {grpc_message_name} {{")
        with self._writer.indent():
            number = 0
            # Info - AM - 30/04/2021 - Write all fields as defined in the serializer. Field_name is the name of the field ans field_type the instance of the drf field: https://www.django-rest-framework.org/api-guide/fields
            for field_name, field_type in grpc_message_fields:

                self.print(f"GENERATE FIELD: {field_name}", 4)
                number += 1

                proto_type = self.get_proto_type(field_type)

                if "google.protobuf.Empty" in proto_type:
                    self._writer.import_empty = True
                if "google.protobuf.Struct" in proto_type:
                    self._writer.import_struct = True

                self._writer.write_line(f"{proto_type} {field_name} = {number};")
        self._writer.write_line("}")
        self._writer.write_line("")

        # We support the possibility to use "__all__" as parameter for fields
        # if grpc_message_fields_name == "__all__":

        #     # TODO - AM - 22/04/2021 - Add global settings or model settings or both to change this default behavior
        #     # Could be by default to include m2m or reverse relaiton
        #     # then should use `get_model_fields(model)`
        #     grpc_message_fields_name = [
        #         field_info.name for field_info in model._meta.concrete_fields
        #     ]

        # elif grpc_message_fields_name == "__pk__":
        #     grpc_message_fields_name = [model._meta.pk.name]

        # self._generate_one_message(model, grpc_message_name, grpc_message_fields_name)

    def get_proto_type(self, field_type):
        """
        Return a proto_type  to use in the proto file from a field_name and a model.

        this method is the magic method that tranform custom attribute like __repeated-link-- to correct proto buff file
        """

        # If field type is a str that mean we use a custom field
        if isinstance(field_type, str):
            return field_type

        proto_type = self.type_mapping.get(field_type.__class__.__name__, "string")
        
        # INFO - AM - 07/01/2022 - If the field type inherit of ListProtoSerializer that mean we have  
        if issubclass(field_type.__class__, ListProtoSerializer):
            proto_type = f"repeated {field_type.child.__class__.__name__.replace('Serializer', '')}"
        # INFO - AM - 07/01/2022 - else if the field type inherit from proto serializer that mean that it is generated as a message in the proto file
        elif issubclass(field_type.__class__, BaseProtoSerializer):
            proto_type = field_type.__class__.__name__.replace("Serializer", "")
        elif issubclass(field_type.__class__, ManyRelatedField):
            # print("ciicicic")
            # print(field_type.child_relation)
            proto_type = f"repeated {self.get_pk_from_related_field(field_type.child_relation)}"
        elif issubclass(field_type.__class__, RelatedField):
            proto_type = self.get_pk_from_related_field(field_type)
        elif issubclass(field_type.__class__, ListSerializer):
            proto_type = "repeated google.protobuf.Struct"
        # INFO - AM - 07/01/2022 - Else if the field type inherit from the BaseSerializer that mean it's a Struct
        elif issubclass(field_type.__class__, BaseSerializer):
            proto_type = "google.protobuf.Struct"

        self.print(f"class is : {field_type.__class__}", 4)
        self.print(f"is subclas of BaseSerializer: {issubclass(field_type.__class__, BaseSerializer)}", 4)
        self.print(f"is subclas of BaseProtoSerializer: {issubclass(field_type.__class__, BaseProtoSerializer)}", 4)
        self.print(f"is subclas of ModelProtoSerializer: {issubclass(field_type.__class__, ModelProtoSerializer)}", 4)
        self.print(f"is subclas of ListProtoSerializer: {issubclass(field_type.__class__, ListProtoSerializer)}", 4)
        self.print(f"is subclas of RelatedField: {issubclass(field_type.__class__, RelatedField)}", 4)
        self.print(
            f"is subclas of ManyRelatedField: {issubclass(field_type.__class__, ManyRelatedField)}", 4
        )

        # if field_type.many:
        #     proto_type = f"repeated {proto_type}"

        return proto_type

    def get_pk_from_related_field(self, related_field):
        if related_field.pk_field:
            return related_field.pk_field
        else:
            type_name = model_meta.get_model_pk(related_field.queryset.model).__class__.__name__
            return self.type_mapping.get(type_name, "related_not_found")

    def get_custom_item_type_and_name(self, field_name):
        """
        Get the Message name we want to inject to an other message to make nested serializer, repeated serializer or just custom message
        field_name should look like:
        __custom__[proto_type]__[proto_field_name]__
        and the method will return proto_type, proto_field_name
        """
        try:
            field_name_splitted = field_name.split("__")
            item_type = field_name_splitted[2]
            item_name = field_name_splitted[3]
            return item_type, item_name
        except Exception:
            raise ProtobufGenerationException(
                self.app_name,
                self.model_name,
                detail=f"Wrong formated custom field name {field_name}",
            )


class _CodeWriter:
    def __init__(self):
        self.buffer = io.StringIO()
        self._indent = 0
        self.import_empty = False
        self.import_struct = False

    def indent(self):
        return self

    def __enter__(self):
        self._indent += 1
        return self

    def __exit__(self, *args):
        self._indent -= 1

    def write_line(self, line):
        for i in range(self._indent):
            self.buffer.write("    ")
        print(line, file=self.buffer)

    def get_code(self):
        value = self.buffer.getvalue()
        value = value.replace("IMPORT_PLACEHOLDER\n", self.get_import_string())
        return value

    def get_import_string(self):
        import_string = ""
        if self.import_empty:
            import_string += 'import "google/protobuf/empty.proto";\n'
        if self.import_struct:
            import_string += 'import "google/protobuf/struct.proto";\n'

        # Info - AM - 30/04/2021 - if there is at least one import we need to put back the line break replaced by the replace function
        if import_string:
            import_string = import_string + "\n"
        return import_string
