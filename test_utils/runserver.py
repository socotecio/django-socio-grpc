from boot_django import boot_django
from django.core.management import call_command

# call the django setup routine
boot_django()

call_command("runserver")
