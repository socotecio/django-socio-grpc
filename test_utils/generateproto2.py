from django.core.management import call_command

from boot_django import boot_django

# call the django setup routine
boot_django()

args = []
opts = {}
call_command("generateproto2", *args, **opts)
