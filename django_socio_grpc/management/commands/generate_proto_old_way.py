import errno
import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from django_socio_grpc.exceptions import ProtobufGenerationException
from django_socio_grpc.protobuf.generators_old_way import ModelProtoGeneratorOldWay
from django_socio_grpc.utils.model_extractor import is_app_in_installed_app, is_model_exist


class Command(BaseCommand):
    help = "Generates proto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            "-m",
            help="dotted path to a model class",
        )
        parser.add_argument("--file", "-f", help="the generated proto file path")
        parser.add_argument("--app", "-a", help="specify Django Application")
        parser.add_argument(
            "--project", "-p", help="specify Django project. Use path by default"
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

    def handle(self, *args, **options):
        # ------------------------------------------
        # ---- extract protog Gen Parameters     ---
        # ------------------------------------------
        self.app_name = options["app"]
        self.model_name = options["model"]
        if self.model_name:
            self.model_name = self.model_name.lower()
        self.project_name = options["project"]
        if not self.project_name and os.environ.get("DJANGO_SETTINGS_MODULE"):
            self.project_name = os.environ.get("DJANGO_SETTINGS_MODULE").split(".")[0]
        else:
            raise ProtobufGenerationException(
                app_name=self.app_name,
                model_name=self.model_name,
                detail="Can't automatically found the correct project name. Set DJANGO_SETTINGS_MODULE or specify the --project option",
            )
        self.file_path = options["file"]
        self.dry_run = options["dry_run"]
        self.generate_python = options["generate_python"]
        self.check = options["check"]

        self.check_options()

        # ----------------------------------------------
        # --- Getting the proto path               ---
        # ----------------------------------------------
        if self.file_path:
            path_used_for_generation = self.file_path
        # if no filepath specified we create it in a grpc directory in the app
        else:
            auto_file_path = os.path.join(
                apps.get_app_config(self.app_name).path, "grpc", f"{self.app_name}.proto"
            )
            path_used_for_generation = auto_file_path

        # ----------------------------------------------
        # --- Proto Generation Process               ---
        # ----------------------------------------------
        generator = ModelProtoGeneratorOldWay(
            project_name=self.project_name,
            app_name=self.app_name,
            model_name=self.model_name,
            existing_proto_path=path_used_for_generation,
        )

        # ------------------------------------------------------------
        # ---- Produce a proto file on current filesystem and Path ---
        # ------------------------------------------------------------
        proto = generator.get_proto()

        if self.dry_run and not self.check:
            self.stdout.write(proto)
        else:
            self.create_directory_if_not_exist(path_used_for_generation)
            self.check_or_write(path_used_for_generation, proto)

        if self.generate_python:
            os.system(
                f"python -m grpc_tools.protoc --proto_path={settings.BASE_DIR} --python_out=./ --grpc_python_out=./ {path_used_for_generation}"
            )

    def check_or_write(self, file_path, proto):
        """
        Write the new generated proto to the corresponding file
        If option --check is used verify if the new content is identical to one already there
        """
        if self.check and not os.path.exists(file_path):
            raise ProtobufGenerationException(
                app_name=self.app_name,
                model_name=self.model_name,
                detail="Check fail ! You doesn't have a proto file to compare to",
            )
        if self.check:
            with open(file_path, "r+") as f:
                self.check_proto_generation(f.read(), proto)
        else:
            with open(file_path, "w+") as f:
                f.write(proto)

    def check_proto_generation(self, original_file, new_proto_content):
        """
        If option --check activated allow to verify that the new generated content is identical to the content of the actual file
        If not raise a ProtobufGenerationException
        """
        if original_file != new_proto_content:
            raise ProtobufGenerationException(
                app_name=self.app_name,
                model_name=self.model_name,
                detail="Check fail ! Generated proto mismatch",
            )
        else:
            print("Check Success ! File are identical")

    def check_options(self):
        """
        Verify the user input
        """
        if not self.app_name and not self.model_name:
            raise ProtobufGenerationException(
                detail="You need to specify at least one app or one model"
            )

        # INFO - AM - 19/04 - Find if the app passed as argument is correct
        if self.app_name and not is_app_in_installed_app(self.app_name):
            raise ProtobufGenerationException(
                app_name=self.app_name, model_name=self.model_name, detail="Invalid Django app"
            )

        # INFO - AM - 19/04 - Find if the model passed as argument is correct
        if self.model_name and not is_model_exist(self.model_name):
            raise ProtobufGenerationException(
                app_name=self.app_name,
                model_name=self.model_name,
                detail="Invalid Django model",
            )

    def create_directory_if_not_exist(self, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
