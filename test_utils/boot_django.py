# File sets up the django environment, used by other scripts that need to
# execute in django land
import os
import sys

import django
from django.conf import settings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FAKE_APP_DIR = os.path.join(BASE_DIR, "django_socio_grpc", "tests")

sys.path.append(BASE_DIR)
sys.path.append(FAKE_APP_DIR)

os.environ["DJANGO_SETTINGS_MODULE"] = "fakeproject.settings"


def boot_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
    settings.configure(
        BASE_DIR=BASE_DIR,
        DEBUG=True,
        GRPC_FRAMEWORK={
            "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
            "ROOT_HANDLERS_HOOK": "fakeapp.handlers.grpc_handlers",
        },
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.environ.get("DB_NAME", "test"),
                "USER": os.environ.get("DB_USER", "test"),
                "PASSWORD": os.environ.get("DB_PASSWORD", "test_pw"),
                "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
                "PORT": os.environ.get("DB_PORT", 5532),
            }
        },
        INSTALLED_APPS=(
            "rest_framework",
            "django.contrib.contenttypes",
            "django_filters",
            "django_socio_grpc",
            "fakeapp",
        ),
        TIME_ZONE="UTC",
        USE_TZ=True,
    )
    django.setup()
