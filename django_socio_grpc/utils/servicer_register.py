import logging

logger = logging.getLogger("django_socio_grpc.registration")

logger.warning(
    f"This module ({__name__}) is deprecated. Please "
    "use `django_socio_grpc.services.app_handler_registry` instead."
)

from django_socio_grpc.services.app_handler_registry import *  # noqa
