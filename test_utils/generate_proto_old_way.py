from boot_django import boot_django
from django.core.management import call_command

# call the django setup routine
boot_django()

args = []
opts = {"app": "fakeapp"}
call_command("generate_proto_old_way", *args, **opts)
