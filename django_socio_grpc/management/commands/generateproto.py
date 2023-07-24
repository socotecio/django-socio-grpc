import asyncio
import os
import logging
from pathlib import Path
from grpc_tools import protoc

from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.management.base import BaseCommand

from django_socio_grpc.exceptions import ProtobufGenerationException
from django_socio_grpc.protobuf import RegistrySingleton
from django_socio_grpc.protobuf.generators import RegistryToProtoGenerator
from django_socio_grpc.settings import grpc_settings


class Command(BaseCommand):
    help = "Generates proto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--project",
            "-p",
            help="specify Django project. Use DJANGO_SETTINGS_MODULE by default",
        )
        parser.add_argument(
            "--dry-run",
            "-dr",
            action="store_true",
            help="print proto data without writing them",
        )
        parser.add_argument(
            "--no-generate-pb2",
            "-nopb2",
            action="store_true",
            default=False,
            help="Do not generate PB2 python files",
        )
        parser.add_argument(
            "--check",
            "-c",
            action="store_true",
            help="Return an error if the file generated is different from the file existent",
        )
        parser.add_argument(
            "--custom-verbose",
            "-cv",
            type=int,
            help="Number from 1 to 4 indicating the verbose level of the generation",
        )
        parser.add_argument(
            "--proto-path",
            default=None,
            help="Directory where the proto files are located. Default will be in the apps directories",
        )
        parser.add_argument(
            "--proto-output-directory",
            "-o",
            default=None,
            help="Directory where the proto files will be generated. Default will be in the apps directories",
        )

    def handle(self, *args, **options):
        if asyncio.iscoroutinefunction(grpc_settings.ROOT_HANDLERS_HOOK):
            async_to_sync(grpc_settings.ROOT_HANDLERS_HOOK)(None)
        else:
            grpc_settings.ROOT_HANDLERS_HOOK(None)
        self.project_name = options["project"]
        if not self.project_name:
            if not os.environ.get("DJANGO_SETTINGS_MODULE"):
                raise ProtobufGenerationException(
                    detail="Can't automatically find the correct project name. Set DJANGO_SETTINGS_MODULE or specify the --project option",
                )
            self.project_name = os.environ.get("DJANGO_SETTINGS_MODULE").split(".")[0]

        self.dry_run = options["dry_run"]
        self.generate_pb2 = not options["no_generate_pb2"]
        self.check = options["check"]

        self.protoc_output_directory = options["proto_output_directory"]
        if self.protoc_output_directory is not None:
            self.protoc_output_directory = Path(self.protoc_output_directory)
            self.protoc_output_directory.mkdir(parents=True, exist_ok=True)

        self.proto_path = options["proto_path"]

        registry_instance = RegistrySingleton()

        # ----------------------------------------------
        # --- Proto Generation Process               ---
        # ----------------------------------------------
        generator = RegistryToProtoGenerator(
            registry_instance=registry_instance,
            project_name=self.project_name,
            verbose=options["custom_verbose"] or 0,
        )

        # ------------------------------------------------------------
        # ---- Produce a proto file on current filesystem and Path ---
        # ------------------------------------------------------------
        protos_by_app = generator.get_protos_by_app(directory=self.protoc_output_directory)

        if self.dry_run and not self.check:
            self.stdout.write(protos_by_app)
        # if no filepath specified we create it in a grpc directory in the app
        else:
            if not protos_by_app.keys():
                raise ProtobufGenerationException(
                    detail="No Service registered. You should use "
                    "ROOT_HANDLERS_HOOK settings and register Service using AppHandlerRegistry."
                )
            for app_name, proto in protos_by_app.items():
                registry = RegistrySingleton().registered_apps[app_name]

                if self.protoc_output_directory:
                    
                    protoc_output_path = self.protoc_output_directory
                else:
                   
                    protoc_output_path = registry.get_grpc_folder()
                    proto_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                if self.proto_path is None:
                     proto_file_path = registry.get_proto_path()
                else:
                    proto_file_path = Path(self.proto_path) / f"{app_name}.proto"

                

                self.check_or_write(proto_file_path, proto, registry.app_name)

                if self.generate_pb2:
                    if not settings.BASE_DIR:
                        raise ProtobufGenerationException(detail="No BASE_DIR in settings")
                    
                    command = ['grpc_tools.protoc']
                    command.append(f'--proto_path={str(self.proto_path)}')
                    command.append(f'--python_out={str( protoc_output_path)}')
                    command.append(f'--grpc_python_out={str(protoc_output_path)}')
                    command.append(str(proto_file_path))  #   The proto file

                    if protoc.main(command) != 0:
                        logging.error(
                            f'Failed to compile .proto code for from file "{proto_file_path}" using the command `{command}`'
                        )
                        return False
                    else:
                        logging.info(
                            f'Successfully compiled "{proto_file_path}"'
                        )

                    # correcting protoc rel. import bug 
                    (pb2_files, _) = os.path.splitext(os.path.basename(proto_file_path))
                    pb2_file = pb2_files + '_pb2.py'
                    pb2_module = pb2_files + '_pb2'

                    pb2_grpc_file = pb2_files + '_pb2_grpc.py'
                    
                    pb2_file_path = os.path.join(proto_path, pb2_file)
                    pb2_grpc_file_path = os.path.join(proto_path, pb2_grpc_file)
                    
                    with open(pb2_grpc_file_path, 'r', encoding='utf-8') as file_in:
                        print(f'Correcting imports of {pb2_grpc_file_path}')
                        
                        replaced_text = file_in.read()

                        replaced_text = replaced_text.replace(f'import {pb2_module}',
                                                                f'from . import {pb2_module}')
                        
                    with open(pb2_grpc_file_path, 'w', encoding='utf-8') as file_out:
                        file_out.write(replaced_text)

    def check_or_write(self, file: Path, proto, app_name):
        """
        Write the new generated proto to the corresponding file
        If option --check is used verify if the new content is identical to one already there
        """
        if self.check and not file.exists():
            raise ProtobufGenerationException(
                app_name=app_name,
                detail="Check fail ! You don't have a proto file to compare to",
            )

        if self.check:
            self.check_proto_generation(file.read_text(), proto, app_name)
        else:
            with file.open("w+") as f:
                f.write(proto)

    def check_proto_generation(self, original_file, new_proto_content, app_name):
        """
        If option --check activated allow to verify that the new generated content is identical to the content of the actual file
        If not raise a ProtobufGenerationException
        """
        if original_file != new_proto_content:
            raise ProtobufGenerationException(
                app_name=app_name,
                detail="Check fail ! Generated proto mismatch",
            )
        else:
            print("Check Success ! Files are identical")
