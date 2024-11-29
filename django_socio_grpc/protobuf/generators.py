import io
import logging
import re
from collections import OrderedDict
from contextlib import nullcontext
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import Enum
from pathlib import Path

from django_socio_grpc.protobuf import RegistrySingleton
from django_socio_grpc.protobuf.proto_classes import (
    ProtoEnum,
    ProtoEnumLocations,
    ProtoMessage,
    ProtoService,
)
from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry

from .protoparser import protoparser

MAX_SORT_NUMBER = 9999

logger = logging.getLogger("django_socio_grpc.generation")


@dataclass
class RegistryToProtoGenerator:
    registry_instance: RegistrySingleton
    project_name: str
    verbose: int = 0
    only_messages: list[str] = dataclass_field(default_factory=list)
    override_fields_number: bool = False

    def print(self, message, verbose_level=0):
        # INFO - AM - 07/01/2022 - This is used to debug only one message. This is manual code.
        if self.only_messages and self.current_message not in self.only_messages:
            return
        if verbose_level <= self.verbose:
            logger.log(verbose_level, message)

    def get_protos_by_app(self, directory: Path | None = None):
        proto_by_app = {}
        for app_name, registry in self.registry_instance.registered_apps.items():
            proto_path = registry.get_proto_path()
            if directory:
                proto_path = directory / f"{app_name}.proto"
            self.print("\n\n--------------------------------\n\n", 1)
            self.print(f"GENERATE APP {app_name}", 1)

            previous_proto_data = self.parse_proto_file(proto_path)
            previous_messages = {}
            if not self.override_fields_number:
                previous_messages = previous_proto_data.messages if previous_proto_data else {}

            proto_by_app[app_name] = self.get_proto(registry, previous_messages)

        return OrderedDict(sorted(proto_by_app.items()))

    def get_proto(
        self,
        registry: AppHandlerRegistry,
        previous_messages: dict[str, protoparser.Message],
    ):
        self._writer = _CodeWriter()

        messages: list[ProtoMessage] = []
        imports = set()

        global_scope_enums = []

        # INFO - AM - 14/04/2023 - split all the messages in the registry in two categories. Ones is the messages imported from an other proto file and Seconds are the one to write in the current proto file we are going to generate
        for mess in registry.get_all_messages().values():
            if mess.imported_from:
                imports.add(mess.imported_from)
            else:
                # Get enums in Global scope
                for field in mess.fields:
                    if (
                        isinstance(field.field_type, ProtoEnum)
                        and field.field_type.location == ProtoEnumLocations.GLOBAL
                    ):
                        global_scope_enums.append(field.field_type)

                messages.append(mess)
                # INFO - AM - 14/04/2023 - indices is used to keep the same field number between two proto generation to avoid breaking changes
                indices = {}
                if previous_messages and (ex_message := previous_messages.get(mess.name)):
                    indices = {f.number: f.name for f in ex_message.fields}
                mess.set_indices(indices)

        imports = sorted(imports)

        self._writer.write_line('syntax = "proto3";')
        self._writer.write_line("")
        self._writer.write_line(f"package {self.project_name}.{registry.app_name};")
        self._writer.write_line("")

        for imp in imports:
            self._writer.write_line(f'import "{imp}";')

        if imports:
            self._writer.write_line("")

        for service in sorted(registry.proto_services, key=lambda x: x.name):
            self._generate_service(service)

        for message in sorted(messages, key=lambda x: x.name):
            self._generate_message(message, previous_messages)

        # list(dict.fromkeys()) is used to remove duplicates while keeping the order
        for proto_enum in list(dict.fromkeys(global_scope_enums)):
            self._generate_enum_and_indices(proto_enum, previous_messages)

        return self._writer.get_code()

    def _generate_service(self, service: ProtoService):
        self._writer.write_line(f"service {service.name} {{")
        with self._writer.indent():
            for rpc in sorted(service.rpcs, key=lambda x: x.name):
                request_name = (
                    rpc.request.name if isinstance(rpc.request, ProtoMessage) else rpc.request
                )
                request_str = f"stream {request_name}" if rpc.request_stream else request_name
                response_name = (
                    rpc.response.name
                    if isinstance(rpc.response, ProtoMessage)
                    else rpc.response
                )
                response_str = (
                    f"stream {response_name}" if rpc.response_stream else response_name
                )

                self._writer.write_line(
                    f"rpc {rpc.name}({request_str}) returns ({response_str}) {{}}"
                )
        self._writer.write_line("}")
        self._writer.write_line("")

    def _generate_message(
        self, message: ProtoMessage, previous_messages: dict[str, protoparser.Message]
    ):
        assert not message.imported_from, "Cannot generate message from imported message"

        # Info - AM - 14/01/2022 - This is used to simplify debugging in large project. See self.print
        self.current_message = message.name

        self.print("\n------\n", 2)
        self.print(f"GENERATE MESSAGE: {message.name}", 2)
        if message.comments:
            self.print(message.comments, 2)
        self.print(message.fields, 3)

        # Info - NS - 16/09/2022 - Write whole message comment if exists
        self.write_comments(message.comments)

        # Info - AM - 30/04/2021 - Write the name of the message
        self._writer.write_line(f"message {message.name} {{")
        with self._writer.indent():
            # Get enums to print
            message_enums = []
            for field in message.fields:
                if (
                    isinstance(field.field_type, ProtoEnum)
                    and field.field_type.location == ProtoEnumLocations.MESSAGE
                ):
                    message_enums.append(field.field_type)
            # list(dict.fromkeys()) is used to remove duplicates while keeping the order
            for proto_enum in list(dict.fromkeys(message_enums)):
                self._generate_enum_and_indices(proto_enum, previous_messages)
            # Info - AM - 30/04/2021 - Write all fields as defined in the serializer. Field_name is the name of the field ans field_type the instance of the drf field: https://www.django-rest-framework.org/api-guide/fields
            for field in sorted(message.fields, key=lambda x: x.index):
                self.print(f"GENERATE FIELD: {field.name}", 4)

                # Info - AM - 30/04/2021 - add comment into the proto file
                self.write_comments(field.comments)

                self._writer.write_line(field.field_line)
        self._writer.write_line("}")
        self._writer.write_line("")

    def _generate_enum_and_indices(
        self, proto_enum: ProtoEnum, previous_messages: dict[str, protoparser.Message]
    ):
        enum = proto_enum.enum
        prev_indices = {}

        if previous_messages and previous_messages.get(enum.__name__):
            ex_enum = previous_messages.get(enum.__name__).enums["Enum"]
            prev_indices = {f.name: int(f.number) for f in ex_enum.fields}

        indices = self._get_enum_indices(enum, prev_indices)
        self._generate_enum(proto_enum, indices)

    def _get_enum_indices(self, enum: Enum, prev_indices: dict[str, int]) -> dict[str, int]:
        curr_idx = 0
        indices = {}
        enum_members_name = [el.name for el in enum]
        # If there are previous indices, we want to keep the same index for the same field name
        if prev_indices:
            indices = {
                field: idx for field, idx in prev_indices.items() if field in enum_members_name
            }
            # We need to start at the current maximum indice when adding new fields to avoid conflicts
            if indices.keys():
                curr_idx = max(prev_indices.values())

        for field in enum_members_name:
            if field not in indices:
                curr_idx += 1
                indices[field] = curr_idx

        return indices

    def _generate_enum(self, proto_enum: ProtoEnum, indices: dict[str, int]):
        enum = proto_enum.enum
        wrap_in_message = proto_enum.wrap_in_message

        # We don't want to write the __doc__ if it is the default one (in python 3.10)
        if enum.__doc__ and enum.__doc__ != "An enumeration.":
            self.write_comments(enum.__doc__.strip().splitlines())

        # Only indent if we are wrapping the enum in a message
        indent_context = self._writer.indent() if wrap_in_message else nullcontext()

        if wrap_in_message:
            self._writer.write_line(f"message {enum.__name__} {{")

        with indent_context:
            self._writer.write_line(f"enum {'Enum' if wrap_in_message else enum.__name__} {{")
            with self._writer.indent():
                # The first value is used by proto3 to represent an unspecified value : ENUM_NAME_UNSPECIFIED
                # See : https://protobuf.dev/programming-guides/dos-donts/#unspecified-enum
                if wrap_in_message:
                    self._writer.write_line("ENUM_UNSPECIFIED = 0;")
                else:
                    screaming_case_enum_name = re.sub(
                        r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", enum.__name__
                    ).upper()
                    self._writer.write_line(f"{screaming_case_enum_name}_UNSPECIFIED = 0;")

                for el in sorted(indices, key=indices.get):
                    el = enum[el]

                    if el.name in enum.__annotations__:
                        comments = enum.__annotations__[el.name].__metadata__[0]
                        if isinstance(comments, str):
                            comments = [comments]
                    else:
                        comments = None

                    self.write_comments(comments)
                    self._writer.write_line(f"{el.name} = {indices[el.name]};")
            self._writer.write_line("}")

        if wrap_in_message:
            self._writer.write_line("}")

        self._writer.write_line("")

    def write_comments(self, comments: list[str] | None):
        if not comments:
            return
        for comment in comments:
            self._writer.write_line(f"// {comment}")

    @staticmethod
    def parse_proto_file(proto_path: Path):
        if not proto_path.exists():
            return None

        return protoparser.parse_from_file(proto_path)


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
        for _i in range(self._indent):
            self.buffer.write("    ")
        print(line, file=self.buffer)

    def get_code(self):
        return self.buffer.getvalue()
