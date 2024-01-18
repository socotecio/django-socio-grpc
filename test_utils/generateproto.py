from boot_django import boot_django

# call the django setup routine
boot_django()


from django.core.management import call_command  # noqa E402
from django.test import override_settings  # noqa E402

from django_socio_grpc.protobuf.registry_singleton import RegistrySingleton  # noqa E402
from django_socio_grpc.tests.test_proto_generation import OVERRIDEN_SETTINGS  # noqa E402

# INFO - AM - 29/12/2023 - Set this to true if you want to reorder proto order without having to delete the proto file.
override_fields_number = False

args = []
opts = {"override_fields_number": override_fields_number}
call_command("generateproto", *args, **opts)

# INFO - AM - 29/12/2023 - This for loop is used to generate proto file used in proto tests to avoid changing them by hand
# for name, grpc_settings in OVERRIDEN_SETTINGS.items():
#     RegistrySingleton.clean_all()
#     settings = {}
#     if grpc_settings:
#         settings = {
#             "GRPC_FRAMEWORK": grpc_settings,
#         }
#     with override_settings(**settings):
#         call_command(
#             "generateproto",
#             no_generate_pb2=True,
#             directory=f"./django_socio_grpc/tests/protos/{name}",
#             project="myproject",
#             override_fields_number=override_fields_number,
#         )
