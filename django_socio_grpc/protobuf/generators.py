import io
import json
import logging
import os
from collections import OrderedDict

import protoparser
from django.apps import apps

from django_socio_grpc.utils.tools import ProtoComment

MAX_SORT_NUMBER = 9999

logger = logging.getLogger("django_socio_grpc")


class RegistryToProtoGenerator:
    def __init__(self, registry_instance, project_name, verbose=0, only_messages=None):
        self.registry_instance = registry_instance
        self.project_name = project_name
        self.verbose = verbose if verbose is not None else 0
        self.only_messages = only_messages if only_messages is not None else []
        self.current_message = ""

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

            self.current_existing_proto_data = self.parse_existing_proto_file(
                self.get_proto_path_for_app_name(app_name)
            )
            proto_by_app[app_name] = self.get_proto(app_name, registered_items)

        return OrderedDict(sorted(proto_by_app.items()))

    def get_proto_path_for_app_name(self, app_name):
        return os.path.join(apps.get_app_config(app_name).path, "grpc", f"{app_name}.proto")

    def get_proto(self, app_name, registered_items):
        self._writer = _CodeWriter()

        self._writer.write_line('syntax = "proto3";')
        self._writer.write_line("")
        self._writer.write_line(f"package {self.project_name}.{app_name};")
        self._writer.write_line("")
        self._writer.write_line("IMPORT_PLACEHOLDER")
        for grpc_controller_name, grpc_methods in sorted(
            registered_items["registered_controllers"].items()
        ):
            self._generate_controller(
                grpc_controller_name, OrderedDict(sorted(grpc_methods.items()))
            )

        for grpc_message_name, grpc_message in sorted(
            registered_items["registered_messages"].items()
        ):
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

        # Info - AM - 14/01/2022 - This is used to simplify debugging in large project. See self.print
        self.current_message = grpc_message_name

        self.print("\n------\n", 2)
        self.print(f"GENERATE MESSAGE: {grpc_message_name}", 2)
        self.print(grpc_message_fields, 3)
        self.print("not ordered yet", 4)

        # Info - AM - 30/04/2021 - Write the name of the message
        self._writer.write_line(f"message {grpc_message_name} {{")
        with self._writer.indent():
            number = 0

            # Info - AM - 14/01/2022 - this is used to try to keep the same order of field in the protofile to avoid breaking change
            grpc_message_fields = self.order_message_by_existing_number(
                grpc_message_name, grpc_message_fields
            )

            # Info - AM - 30/04/2021 - Write all fields as defined in the serializer. Field_name is the name of the field ans field_type the instance of the drf field: https://www.django-rest-framework.org/api-guide/fields
            for field_name, proto_type, comment in grpc_message_fields:

                self.print(f"GENERATE FIELD: {field_name}", 4)
                number += 1

                if "google.protobuf.Empty" in proto_type:
                    self._writer.import_empty = True
                if "google.protobuf.Struct" in proto_type:
                    self._writer.import_struct = True

                # Info - AM - 30/04/2021 - add comment into the proto file
                if comment and isinstance(comment, ProtoComment):
                    for part_of_comment in comment:
                        self.write_comment_line(part_of_comment)

                self._writer.write_line(f"{proto_type} {field_name} = {number};")
        self._writer.write_line("}")
        self._writer.write_line("")

    def write_comment_line(self, comment):
        self._writer.write_line(f"//{comment}")

    def find_existing_number_for_field(self, grpc_message_name, field_name):
        """
        Find if the field for this grpc message was already existing and return its number
        """
        if not self.current_existing_proto_data:
            return MAX_SORT_NUMBER

        if grpc_message_name not in self.current_existing_proto_data.get("messages", {}):
            return MAX_SORT_NUMBER

        for parsed_field in self.current_existing_proto_data["messages"][grpc_message_name][
            "fields"
        ]:
            if parsed_field["name"] == field_name:
                return parsed_field["number"]

        return MAX_SORT_NUMBER

    def order_message_by_existing_number(self, grpc_message_name, grpc_message_fields):
        # INFO - AM - 14/01/2022 - grpc_message_fields is a list of tuple. Tuple of two element first is field_name second is field prototype
        grpc_message_fields.sort(
            key=lambda field: self.find_existing_number_for_field(grpc_message_name, field[0])
        )
        return grpc_message_fields

    def check_if_existing_proto_file(self, existing_proto_path):
        """
        This method is here only to help mocking test because os.path.exists is call multiple time
        """
        return os.path.exists(existing_proto_path)

    def parse_existing_proto_file(self, existing_proto_path):
        if not self.check_if_existing_proto_file(existing_proto_path):
            return None

        proto_data = protoparser.serialize2json_from_file(existing_proto_path)

        return json.loads(proto_data)


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
