import asyncio
import logging
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from django.db.models.query import QuerySet
from google.protobuf.message import Message

from django_socio_grpc.exceptions import PermissionDenied, Unauthenticated
from django_socio_grpc.grpc_actions.actions import GRPCActionMixin
from django_socio_grpc.request_transformer.grpc_socio_proxy_context import (
    GRPCSocioProxyContext,
)
from django_socio_grpc.servicer_proxy import ServicerProxy
from django_socio_grpc.settings import grpc_settings

if TYPE_CHECKING:
    from django_socio_grpc.utils.servicer_register import AppHandlerRegistry

logger = logging.getLogger("django_socio_grpc")


class Service(GRPCActionMixin):

    authentication_classes = grpc_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = grpc_settings.DEFAULT_PERMISSION_CLASSES

    action: str = None
    request: Message = None
    context: GRPCSocioProxyContext = None

    _app_handler: "AppHandlerRegistry" = None

    def __init__(self, **kwargs):
        """
        Set kwargs as self attributes.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_service_name(self):
        return self.__class__.__name__

    def get_controller_name(self):
        return f"{self.get_service_name()}Controller"

    def perform_authentication(self):
        user_auth_tuple = None
        try:
            user_auth_tuple = self.resolve_user()
        except Exception as e:
            raise Unauthenticated(detail=e)
        if not user_auth_tuple:
            self.context.user = None
            self.context.auth = None
            return

        self.context.user = user_auth_tuple[0]
        self.context.auth = user_auth_tuple[1]

    def resolve_user(self):
        auth_responses = [
            auth().authenticate(self.context) for auth in self.authentication_classes
        ]
        if auth_responses:
            return auth_responses[0]
        return None

    def check_permissions(self):
        if grpc_settings.GRPC_ASYNC:

            async def check_permissions():
                for permission in self.get_permissions():
                    has_permission = permission.has_permission
                    if not asyncio.iscoroutinefunction(permission.has_permission):
                        has_permission = sync_to_async(permission.has_permission)
                    if not await has_permission(self.context, self):
                        raise PermissionDenied(detail=getattr(permission, "message", None))

            return check_permissions()

        for permission in self.get_permissions():
            if not permission.has_permission(self.context, self):
                raise PermissionDenied(detail=getattr(permission, "message", None))

    def check_object_permissions(self, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(self.context, self, obj):
                raise PermissionDenied(detail=getattr(permission, "message", None))

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def before_action(self):
        """
        Runs anything that needs to occur prior to calling the method handler.
        """
        if grpc_settings.GRPC_ASYNC:

            async def before_action():
                await sync_to_async(self.perform_authentication)()
                await self.check_permissions()

            return before_action()

        self.perform_authentication()
        self.check_permissions()

    @classmethod
    def as_servicer(cls, **initkwargs):
        """
        Returns a gRPC servicer instance::

            servicer = PostService.as_servicer()
            add_PostControllerServicer_to_server(servicer, server)
        """
        for key in initkwargs:
            if not hasattr(cls, key):
                raise TypeError(
                    "%s() received an invalid keyword %r. as_servicer only "
                    "accepts arguments that are already attributes of the "
                    "class." % (cls.__name__, key)
                )
        if isinstance(getattr(cls, "queryset", None), QuerySet):

            def force_evaluation():
                raise RuntimeError(
                    "Do not evaluate the `.queryset` attribute directly, "
                    "as the result will be cached and reused between requests."
                    " Use `.all()` or call `.get_queryset()` instead."
                )

            cls.queryset._fetch_all = force_evaluation

        return ServicerProxy(cls)
