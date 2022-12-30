from boot_django import boot_django
from django.core.management import call_command
from django.test import override_settings

from django_socio_grpc.protobuf.registry_singleton import RegistrySingleton
from django_socio_grpc.tests.test_proto_generation import OVERRIDEN_SETTINGS

# call the django setup routine
boot_django()

args = []
opts = {}
call_command("generateproto", *args, **opts)

for name, grpc_settings in OVERRIDEN_SETTINGS.items():
    RegistrySingleton.clean_all()
    settings = {}
    if grpc_settings:
        settings = {
            "GRPC_FRAMEWORK": grpc_settings,
        }
    with override_settings(**settings):
        call_command(
            "generateproto",
            no_generate_pb2=True,
            directory=f"./django_socio_grpc/tests/protos/{name}",
            project="myproject",
        )
