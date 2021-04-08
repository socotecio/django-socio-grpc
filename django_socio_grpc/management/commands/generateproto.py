import os

from django.core.management.base import BaseCommand, CommandError
from django.utils.module_loading import import_string

from django_socio_grpc.protobuf.generators import ModelProtoGenerator
from django_socio_grpc.utils.model_extractor import getModel, getModelColumn


class Command(BaseCommand):
    help = "Generates proto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            dest="model",
            type=str,
            required=True,
            help="dotted path to a model class",
        )
        parser.add_argument(
            "--fields",
            dest="fields",
            default=None,
            type=str,
            help="specify which fields to include, comma-seperated",
        )
        parser.add_argument(
            "--file", dest="file", default=None, type=str, help="the generated proto file path"
        )
        parser.add_argument(
            "--app", dest="package", default=None, type=str, help="specify Django Application"
        )
        parser.add_argument(
            "--update", dest="update", default="", type=str, help="Replace the proto file"
        )

    def handle(self, *args, **options):

        self.validProto = True
        modelValid = False
        fieldsArray = []

        # ------------------------------------------
        # ---- extract protog Gen Parameters     ---
        # ------------------------------------------
        self.update = options["update"]
        self.package = options["package"]

        try:
            model = import_string(options["model"])
            modelValid = True
        except Exception:
            model = options["model"]
        fields = options["fields"]
        if fields != "*":
            fields = options["fields"].split(",") if options["fields"] else None
        filepath = options["file"]

        # --------------------------------------------------
        # --- Check Path for generating the protbuf file ---
        # --------------------------------------------------
        if filepath and os.path.exists(filepath) and not self.update:
            raise CommandError('File "%s" already exists.' % filepath)

        # -------------------------------------------------------------------------
        # -- if no Django app provided, extract the App from protobuf file path ---
        # -------------------------------------------------------------------------
        if not self.package:
            if filepath:
                self.package = os.path.splitext(os.path.basename(filepath))[0]
            else:
                self.package = None

        # ---------------------------------------------
        # --- extract all available model's Column  ---
        # ---------------------------------------------
        if not modelValid:
            model = getModel(model)

        # --------------------------------------------------------
        # ----  AUTO GENERATION OF ALL DATA MODEL FIELDS LIST  ---
        # ----  Valid Model extract Data Fields definition     ---
        # --------------------------------------------------------
        if model:
            if fields == "*":
                arrayFields = getModelColumn(model)
                if len(arrayFields) > 0:
                    for col in arrayFields:
                        fieldsArray.append(col["name"])
                    fields = fieldsArray
        else:
            self.validProto = False
            print("**** ERROR  : Invalid Data Model [%s]    *****" % model)

        # ----------------------------------------------
        # --- Proto Generation Process               ---
        # ----------------------------------------------
        generator = ModelProtoGenerator(
            model=model, field_names=fields, package=self.package, filepath=filepath
        )
        if not generator.status_proto():
            self.validProto = False
            print("**** ERROR   %s     *****" % generator.message_proto())

        # ------------------------------------------------------------
        # ---- Produce a proto file on current filesystem and Path ---
        # ------------------------------------------------------------
        if self.validProto:
            proto = generator.get_proto()
            if generator.status_proto():
                if filepath:
                    with open(filepath, "w") as f:
                        f.write(proto)
                else:
                    self.stdout.write(proto)
            else:
                print("**** ERROR   %s     *****" % generator.message_proto())
