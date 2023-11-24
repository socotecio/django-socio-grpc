import logging

from .services.servicer_proxy import *  # noqa

logger = logging.getLogger("django_socio_grpc.internal")

logger.warning(
    f"This module ({__name__}) is deprecated. Please "
    "use `django_socio_grpc.services.servicer_proxy` instead."
)
