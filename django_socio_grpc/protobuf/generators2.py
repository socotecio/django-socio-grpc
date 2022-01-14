import io
import logging

from django_socio_grpc.exceptions import ProtobufGenerationException


logger = logging.getLogger("django_socio_grpc")


class ModelProtoGenerator:

    def __init__(self, registry_instance, project_name, verbose=0, only_messages=None):
        self.registry_instance = registry_instance
        self.project_name = project_name
        self.verbose = verbose
        self.only_messages = only_messages if only_messages is not None else []
        self.current_message = ""


        # TODO for debug remove this after
        # self.verbose = 4
        # self.only_messages = ["SpecialFieldsModel"]

    def print(self, message, verbose_level=0):
        # INFO - AM - 07/01/2022 - This is used to debug only one message. This is manual code. 
        if self.only_messages and self.current_message not in self.only_messages:
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
            for field_name, proto_type in grpc_message_fields:

                self.print(f"GENERATE FIELD: {field_name}", 4)
                number += 1

                if "google.protobuf.Empty" in proto_type:
                    self._writer.import_empty = True
                if "google.protobuf.Struct" in proto_type:
                    self._writer.import_struct = True

                self._writer.write_line(f"{proto_type} {field_name} = {number};")
        self._writer.write_line("}")
        self._writer.write_line("")

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
