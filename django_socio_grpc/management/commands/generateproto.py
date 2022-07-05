import errno
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from django_socio_grpc.exceptions import ProtobufGenerationException
from django_socio_grpc.protobuf.generators import RegistryToProtoGenerator
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.registry_singleton import RegistrySingleton


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
            "--generate-python",
            "-gp",
            action="store_true",
            default=True,
            help="generate python file too",
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

    def handle(self, *args, **options):

        # ------------------------------------------
        # ---- extract protog Gen Parameters     ---
        # ------------------------------------------
        grpc_settings.ROOT_HANDLERS_HOOK(None)
        self.project_name = options["project"]
        if not self.project_name and os.environ.get("DJANGO_SETTINGS_MODULE"):
            self.project_name = os.environ.get("DJANGO_SETTINGS_MODULE").split(".")[0]
        else:
            raise ProtobufGenerationException(
                detail="Can't automatically found the correct project name. Set DJANGO_SETTINGS_MODULE or specify the --project option",
            )
        self.dry_run = options["dry_run"]
        self.generate_python = options["generate_python"]
        self.check = options["check"]

        registry_instance = RegistrySingleton()

        # ----------------------------------------------
        # --- Proto Generation Process               ---
        # ----------------------------------------------
        generator = RegistryToProtoGenerator(
            registry_instance=registry_instance,
            project_name=self.project_name,
            verbose=options["custom_verbose"],
        )

        # ------------------------------------------------------------
        # ---- Produce a proto file on current filesystem and Path ---
        # ------------------------------------------------------------
        path_used_for_generation = None
        protos_by_app = generator.get_protos_by_app()

        if self.dry_run and not self.check:
            self.stdout.write(protos_by_app)
        # if no filepath specified we create it in a grpc directory in the app
        else:

            if not protos_by_app.keys():
                raise ProtobufGenerationException(
                    detail="No Service registered. You should use ROOT_HANDLERS_HOOK settings and register Service using AppHandlerRegistry."
                )
            for app_name, proto in protos_by_app.items():
                auto_file_path = generator.get_proto_path_for_app_name(app_name)
                self.create_directory_if_not_exist(auto_file_path)
                self.check_or_write(auto_file_path, proto, app_name)
                path_used_for_generation = auto_file_path

                if self.generate_python:
                    if not settings.BASE_DIR:
                        raise ProtobufGenerationException(detail="No BASE_DIR in settings")
                    os.system(
                        f"python -m grpc_tools.protoc --proto_path={settings.BASE_DIR} --python_out=./ --grpc_python_out=./ {path_used_for_generation}"
                    )

    def check_or_write(self, file_path, proto, app_name):
        """
        Write the new generated proto to the corresponding file
        If option --check is used verify if the new content is identical to one already there
        """
        if self.check and not os.path.exists(file_path):
            raise ProtobufGenerationException(
                app_name=app_name,
                detail="Check fail ! You doesn't have a proto file to compare to",
            )

        if self.check:
            with open(file_path) as f:
                content = f.read()
                self.check_proto_generation(content, proto, app_name)
        else:
            with open(file_path, "w+") as f:
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
            print("Check Success ! File are identical")

    def create_directory_if_not_exist(self, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
