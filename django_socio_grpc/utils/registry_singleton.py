import logging

logger = logging.getLogger("django_socio_grpc.registration")

logger.warning(
    f"This module ({__name__}) is deprecated. Please "
    "use `django_socio_grpc.protobuf.registry_singleton` instead."
)

from django_socio_grpc.protobuf.registry_singleton import *  # noqa
