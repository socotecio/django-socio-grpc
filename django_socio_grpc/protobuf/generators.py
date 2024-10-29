import io
import logging
from collections import OrderedDict
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import Enum
from pathlib import Path

from django_socio_grpc.protobuf import RegistrySingleton
from django_socio_grpc.protobuf.proto_classes import ProtoMessage, ProtoService
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

        # INFO - AM - 14/04/2023 - split all the messages in the registry in two categories. Ones is the messages imported from an other proto file and Seconds are the one to write in the current proto file we are going to generate
        for mess in registry.get_all_messages().values():
            if mess.imported_from:
                imports.add(mess.imported_from)
            else:
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

        enums = []

        for message in sorted(messages, key=lambda x: x.name):
            self._generate_message(message)

            # Gather all enums to generate them at the end
            enums += [
                f.field_type
                for f in message.fields
                if isinstance(f.field_type, type) and issubclass(f.field_type, Enum)
            ]

        prev_indices = {}

        generated_enums = []
        for enum in enums:
            if enum.__name__ in generated_enums:
                continue
            generated_enums.append(enum.__name__)

            if previous_messages and previous_messages.get(enum.__name__):
                ex_enum = previous_messages.get(enum.__name__).enums["Enum"]
                prev_indices = {f.name: int(f.number) for f in ex_enum.fields}
            indices = self._get_enum_indices(enum, prev_indices)
            self._generate_enum(enum, indices)

        return self._writer.get_code()

    def _get_enum_indices(self, enum: Enum, prev_indices: dict[str, int]) -> dict[str, int]:
        curr_idx = 0
        indices = {}
        enum_members_name = [el.name for el in enum]
        if prev_indices:
            indices = {
                field: idx for field, idx in prev_indices.items() if field in enum_members_name
            }
            if indices.keys():
                curr_idx = max(prev_indices.values())

        for field in enum_members_name:
            if field not in indices:
                curr_idx += 1
                indices[field] = curr_idx

        return indices

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

    def _generate_message(self, message: ProtoMessage):
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
            # Info - AM - 30/04/2021 - Write all fields as defined in the serializer. Field_name is the name of the field ans field_type the instance of the drf field: https://www.django-rest-framework.org/api-guide/fields
            for field in sorted(message.fields, key=lambda x: x.index):
                self.print(f"GENERATE FIELD: {field.name}", 4)

                # Info - AM - 30/04/2021 - add comment into the proto file
                self.write_comments(field.comments)

                self._writer.write_line(field.field_line)
        self._writer.write_line("}")
        self._writer.write_line("")

    def _generate_enum(self, enum: Enum, indices: dict[str, int]):
        if enum.__doc__:
            self.write_comments(enum.__doc__.strip().splitlines())

        self._writer.write_line(f"message {enum.__name__} {{")
        with self._writer.indent():
            self._writer.write_line("enum Enum {")
            with self._writer.indent():
                self._writer.write_line("ENUM_UNSPECIFIED = 0;")
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
        self._writer.write_line("}")
        self._writer.write_line("")

    def write_comments(self, comments: list[str] | None):
        if not comments:
            return
        for comment in comments:
            self._writer.write_line(f"// {comment}")

    def parse_proto_file(self, proto_path: Path):
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
