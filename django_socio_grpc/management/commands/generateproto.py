import asyncio
import os
from pathlib import Path

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
            "--directory",
            "-d",
            default=None,
            help="Directory where the proto files will be generated. Default will be in the apps directories",
        )
        parser.add_argument(
            "--override-fields-number",
            "-ofn",
            action="store_true",
            help="Do not follow old field number when generating. /!\\ this can lead to API breaking change.",
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
        self.directory = options["directory"]
        if self.directory:
            self.directory = Path(self.directory)
            self.directory.mkdir(parents=True, exist_ok=True)

        registry_instance = RegistrySingleton()

        # ----------------------------------------------
        # --- Proto Generation Process               ---
        # ----------------------------------------------
        generator = RegistryToProtoGenerator(
            registry_instance=registry_instance,
            project_name=self.project_name,
            verbose=options["custom_verbose"] or 0,
            override_fields_number=options["override_fields_number"],
        )

        # ------------------------------------------------------------
        # ---- Produce a proto file on current filesystem and Path ---
        # ------------------------------------------------------------
        protos_by_app = generator.get_protos_by_app(directory=self.directory)

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

                if self.directory:
                    file_path = self.directory / f"{app_name}.proto"
                else:
                    file_path = registry.get_proto_path()
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                self.check_or_write(file_path, proto, registry.app_name)

                if self.generate_pb2:
                    if not settings.BASE_DIR:
                        raise ProtobufGenerationException(detail="No BASE_DIR in settings")
                    os.system(
                        f"python -m grpc_tools.protoc --proto_path={settings.BASE_DIR} --python_out=./ --grpc_python_out=./ {file_path}"
                    )

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
