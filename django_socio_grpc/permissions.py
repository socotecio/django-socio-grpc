from typing import TYPE_CHECKING

from rest_framework.permissions import BasePermission

if TYPE_CHECKING:
    from django_socio_grpc.request_transformer.grpc_socio_proxy_context import (
        GRPCSocioProxyContext,
    )
    from django_socio_grpc.services import Service


class GRPCActionBasePermission(BasePermission):
    """
    Base class from which all GRPC action permissions should inherit.
    """

    def has_permission(self, context: "GRPCSocioProxyContext", service: "Service"):
        return True

    def has_object_permission(self, context: "GRPCSocioProxyContext", service: "Service", obj):
        return True
