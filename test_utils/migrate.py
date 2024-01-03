import sys

from boot_django import boot_django
from django.core.management import call_command

# call the django setup routine
boot_django()

args = []

if len(sys.argv[1:]) > 0:
    args = sys.argv[1:]

call_command("migrate", *args)
