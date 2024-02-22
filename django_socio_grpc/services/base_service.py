import asyncio
from typing import TYPE_CHECKING, List, Type

from asgiref.sync import sync_to_async
from django.db.models.query import QuerySet
from google.protobuf.message import Message
from rest_framework.permissions import BasePermission

from django_socio_grpc.exceptions import PermissionDenied, Unauthenticated
from django_socio_grpc.grpc_actions.actions import GRPCActionMixin
from django_socio_grpc.request_transformer.grpc_internal_proxy import GRPCInternalProxyContext
from django_socio_grpc.services.servicer_proxy import ServicerProxy
from django_socio_grpc.settings import grpc_settings

if TYPE_CHECKING:
    from django_socio_grpc.protobuf import AppHandlerRegistry

from logging import getLogger

logger = getLogger(__name__)


class Service(GRPCActionMixin):
    authentication_classes = grpc_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = grpc_settings.DEFAULT_PERMISSION_CLASSES

    action: str = None
    request: Message = None
    context: GRPCInternalProxyContext = None

    _app_handler: "AppHandlerRegistry" = None

    _servicer_proxy: Type[ServicerProxy] = ServicerProxy

    _is_auth_performed: bool = False

    def __init__(self, **kwargs):
        """
        Set kwargs as self attributes.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def get_service_name(cls):
        return cls.__name__

    @classmethod
    def get_controller_name(cls):
        return f"{cls.get_service_name()}Controller"

    def perform_authentication(self):
        if self._is_auth_performed:
            return
        user_auth_tuple = None
        try:
            user_auth_tuple = self.resolve_user()
        except Exception as e:
            raise Unauthenticated(detail=e)

        if not user_auth_tuple:
            self.context.user = None
            self.context.auth = None
        else:
            self.context.user = user_auth_tuple[0]
            self.context.auth = user_auth_tuple[1]
        self._is_auth_performed = True

    def resolve_user(self):
        auth_responses = [
            auth().authenticate(self.context) for auth in self.authentication_classes
        ]
        if auth_responses:
            return auth_responses[0]
        return None

    def _check_permissions(self):
        for permission in self.get_permissions():
            if not permission.has_permission(self.context, self):
                raise PermissionDenied(detail=getattr(permission, "message", None))

    async def _async_check_permissions(self):
        for permission in self.get_permissions():
            has_permission = permission.has_permission
            if not asyncio.iscoroutinefunction(permission.has_permission):
                has_permission = sync_to_async(permission.has_permission)
            if not await has_permission(self.context, self):
                raise PermissionDenied(detail=getattr(permission, "message", None))

    def check_permissions(self):
        if grpc_settings.GRPC_ASYNC:
            return self._async_check_permissions()
        return self._check_permissions()

    async def acheck_object_permissions(self, obj):
        for permission in self.get_permissions():
            has_object_permission = permission.has_object_permission
            if not asyncio.iscoroutinefunction(permission.has_object_permission):
                has_object_permission = sync_to_async(permission.has_object_permission)
            if not await has_object_permission(self.context, self, obj):
                raise PermissionDenied(detail=getattr(permission, "message", None))

    def check_object_permissions(self, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(self.context, self, obj):
                raise PermissionDenied(detail=getattr(permission, "message", None))

    def get_permissions(self) -> List[BasePermission]:
        return [permission() for permission in self.permission_classes]

    def _before_action(self):
        self.perform_authentication()
        self.check_permissions()

    async def _async_before_action(self):
        await sync_to_async(self.perform_authentication)()
        await self.check_permissions()

    def before_action(self):
        """
        Runs anything that needs to occur prior to calling the method handler.
        """
        if grpc_settings.GRPC_ASYNC:
            return self._async_before_action()
        return self._before_action()

    def _after_action(self):
        ...

    async def _async_after_action(self):
        ...

    def after_action(self):
        """
        Runs anything that needs to occur after calling the method handler.
        """
        if grpc_settings.GRPC_ASYNC:
            return self._async_after_action()
        return self._after_action()

    def get_log_extra_context(self):
        """
        Using this method is deprecated.
        Refer to the logging documentation to see how to add extra context.
        """
        return grpc_settings.LOG_EXTRA_CONTEXT_FUNCTION(self)

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

        return cls._servicer_proxy(cls)
