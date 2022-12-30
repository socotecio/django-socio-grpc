"""
>>> MyMixin(GRPCActionMixin, ):
...     @grpc_action(request=[], response=[])
...     def MyDecoratedAction(self, request, context):
...         pass
...
...     def MyAction(self, request, context):
...         pass
...
...     def _dynamic_grpc_action_registry(service):
...         return {
...             "MyAction": {request=[], request_name=service.req_name, response=[]}
...         }
...
...     def _before_registration(service):
...         service.req_name = service.__name__

>>> MyService(MyMixin):
...     @grpc_action(request=[], response=[])
...     def MyServiceAction(self, request, context):
...         pass
...
...     @grpc_action(request=[], response=[])
...     def MySecondServiceAction(self, request, context):
...         pass
...
...     def _before_registration(service):
...         service.req_name = "MyReqName"

GRPCAction registration lifecycle on class definition :

---> MyService parents and MyService `_before_registration` methods are called.
with MyService as the argument.
---> MyService parents and MyService `_dynamic_grpc_action_registry` methods are called
with MyService as the argument and their returned dict is merged with decorated actions data
from MyService abstract parents. This dict is then registered.
"""

import abc
import asyncio
import functools
import logging
from asyncio.coroutines import _is_coroutine
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union

from asgiref.sync import SyncToAsync
from rest_framework.serializers import BaseSerializer

from django_socio_grpc.protobuf.exceptions import ProtoRegistrationError
from django_socio_grpc.protobuf.proto_classes import (
    FieldCardinality,
    FieldDict,
    ProtoField,
    ProtoMessage,
    ProtoRpc,
    ProtoService,
    RequestProtoMessage,
    ResponseProtoMessage,
)
from django_socio_grpc.request_transformer.grpc_socio_proxy_context import (
    GRPCSocioProxyContext,
)
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.tools import rreplace
from django_socio_grpc.utils.utils import _is_generator, isgeneratorfunction

from .placeholders import Placeholder

if TYPE_CHECKING:
    from django_socio_grpc.services import Service


logger = logging.getLogger("django_socio_grpc")


RequestResponseType = Union[str, Type[BaseSerializer], Placeholder, List[FieldDict]]


@dataclass
class GRPCAction:
    function: Callable[["Service", Any, GRPCSocioProxyContext], Any]
    request: Optional[RequestResponseType] = None
    response: Optional[RequestResponseType] = None
    request_name: Optional[str] = None
    response_name: Optional[str] = None
    request_stream: bool = False
    response_stream: bool = False
    use_request_list: bool = False
    use_response_list: bool = False
    request_message_list_attr: Optional[str] = None
    response_message_list_attr: Optional[str] = None

    proto_rpc: Optional[ProtoRpc] = field(init=False, default=None)

    def __post_init__(self):

        if isinstance(self.function, SyncToAsync):

            async def func(self, *args, **kwargs):
                return await self.function(self, *args, **kwargs)

            self.function = functools.update_wrapper(func, self.function.func)

        if asyncio.iscoroutinefunction(self.function):
            self._is_coroutine = _is_coroutine

        if isgeneratorfunction(self.function):
            self._is_generator = _is_generator

    def __set_name__(self, owner, name):
        """
        set name function is called automatically by python and allow us
        to retrieve the owner(Service) instance that we need for proto registration
        """
        # INFO - LG - 25/05/2022 - For GRPCActionMixins, we store the action info in the owner's
        # _decorated_grpc_action_registry attribute to register later on services
        if issubclass(owner, GRPCActionMixin):
            if "_decorated_grpc_action_registry" not in owner.__dict__:
                owner._decorated_grpc_action_registry = {}
            owner._decorated_grpc_action_registry.update({name: self.get_action_params()})

    def __get__(self, obj, type=None):
        return self.clone(function=self.function.__get__(obj, type))

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def get_action_params(self):
        return {
            "request": self.request,
            "request_name": self.request_name,
            "request_stream": self.request_stream,
            "use_request_list": self.use_request_list,
            "response": self.response,
            "response_name": self.response_name,
            "response_stream": self.response_stream,
            "use_response_list": self.use_response_list,
        }

    @property
    def request_message_name(self) -> Optional[str]:
        try:
            return self.proto_rpc.request_name
        except AttributeError:
            return None

    @property
    def response_message_name(self) -> Optional[str]:
        try:
            return self.proto_rpc.response_name
        except AttributeError:
            return None

    def create_proto_message(
        self,
        message: Optional[Union[str, Type[BaseSerializer], List[FieldDict]]],
        message_name: Optional[str],
        message_class: Type[ProtoMessage],
        action_name: str,
        service: Type["Service"],
        as_list: bool,
        list_field_name: Optional[str],
    ):

        assert not isinstance(message, Placeholder)
        try:

            prefix = service.get_service_name()
            proto_message = message_class.create(
                message,
                base_name=message_name or action_name,
                appendable_name=not message_name,
                prefix=prefix,
            )
            if as_list:
                try:
                    list_field_name = proto_message.serializer.Meta.message_list_attr
                except AttributeError:
                    list_field_name = list_field_name or "results"

                fields = [
                    ProtoField(
                        name=list_field_name,
                        field_type=proto_message,
                        cardinality=FieldCardinality.REPEATED,
                    )
                ]
                if getattr(service, "pagination_class", None):
                    fields.append(
                        ProtoField(
                            name="count",
                            field_type="int32",
                        )
                    ),

                base_list_name = action_name
                prefixable = True
                if isinstance(proto_message, str):
                    proto_message_name = proto_message
                elif not proto_message.imported_from:
                    proto_message_name = proto_message.base_name
                    prefixable = proto_message.prefixable
                else:
                    proto_message_name = action_name

                base_list_name = rreplace(proto_message_name, message_class.suffix, "", 1)

                list_message = message_class(
                    base_name=f"{base_list_name}List",
                    fields=fields,
                    prefix=prefix,
                    prefixable=prefixable,
                )

                if not proto_message.serializer:
                    list_message.comments = proto_message.comments
                    proto_message.comments = None

                return list_message

            return proto_message

        except TypeError:
            raise ProtoRegistrationError(
                f"GRPCAction {action_name} has an invalid message type: {type(message)}"
            )

    def make_proto_rpc(self, action_name: str, service: Type["Service"]) -> ProtoRpc:

        req_class = res_class = ProtoMessage
        if grpc_settings.SEPARATE_READ_WRITE_MODEL:
            req_class = RequestProtoMessage
            res_class = ResponseProtoMessage

        request = self.create_proto_message(
            self.request,
            self.request_name,
            req_class,
            action_name,
            service,
            self.use_request_list,
            self.request_message_list_attr,
        )
        response = self.create_proto_message(
            self.response,
            self.response_name,
            res_class,
            action_name,
            service,
            self.use_response_list,
            self.response_message_list_attr,
        )

        return ProtoRpc(
            name=action_name,
            request=request,
            response=response,
            request_stream=self.request_stream,
            response_stream=self.response_stream,
        )

    def register(self, owner: Type["Service"], action_name: str):
        try:
            self.resolve_placeholders(owner, action_name)

            self.proto_rpc = self.make_proto_rpc(action_name, owner)
        except ProtoRegistrationError as e:
            e.action = action_name
            e.service = owner.get_service_name()
            raise e
        except Exception as e:
            raise ProtoRegistrationError(
                e, action=action_name, service=owner.get_service_name()
            )

        owner.proto_service.add_rpc(self.proto_rpc)

        setattr(owner, action_name, self)

    def resolve_placeholders(self, service_class: Type["Service"], action: str):
        """
        Iterate over the `GRPCAction` attributes and resolve all the placeholder instances

        Classic placeholder usage :
        >>> @grpc_action(request=MyRequestPlaceholder, response=MyResponsePlaceholder)
        >>> def MyAction(self, request, context): ...

        `MyRequestPlaceholder` and `MyResponsePlaceholder` are placeholder instances
        which are resolved with the current service by this method, allowing us to
        set dynamic attributes to the `GRPCAction`.
        """

        service = service_class()
        service.action = action
        for action_param_field, action_param_value in self.get_action_params().items():
            if isinstance(action_param_value, Placeholder):
                action_param_value(service, self, action_param_field)

    def clone(self, **kwargs):
        """
        Clones the current `GRPCAction` instance overriding the given kwargs
        """
        kwargs = {**self.get_action_params(), **kwargs}
        fn = kwargs.pop("function", self.function)
        new_cls = self.__class__(fn, **kwargs)
        new_cls.proto_rpc = self.proto_rpc
        return new_cls


def register_action(cls, action_name: str, name: Optional[str] = None, **kwargs):
    """
    Register action function_name of mixin and register them if they are decorated (so already a GRPCAction)
    or transform them into a GRPCAction before registering them
    """

    # INFO - AM - 25/05/2022 - get function in service. This can be a function or
    # a GRPCAction if used with decorator
    action = getattr(cls, action_name)

    if not isinstance(action, GRPCAction):
        action = GRPCAction(action, **kwargs)

    action.register(cls, name or getattr(action.function, "__name__", action_name))


class GRPCActionMixin(abc.ABC):

    _decorated_grpc_action_registry: Dict[str, Dict[str, Any]]
    """Registry of grpc actions declared in the class"""

    proto_service: ProtoService

    @classmethod
    @abc.abstractmethod
    def get_controller_name(cls) -> str:
        ...

    @classmethod
    def before_registration(cls, service_class=None):
        """
        Call all the service parents `_before_registration` methods
        """
        cls.proto_service = ProtoService(cls.get_controller_name())
        for base in cls.get_action_parents()[::-1]:
            if "_before_registration" in base.__dict__:
                base._before_registration(service_class or cls)

    @classmethod
    def get_parents_action_registry(cls, service):
        """
        Returns all the grpc action registries (decorated and dynamic) of all the parent mixin
        """
        registry = {}

        for parent in cls.get_action_parents()[::-1]:
            # INFO - AM - 25/05/2022 - if the parent inherit from GRPCActionMixin it
            # will have _dynamic_grpc_action_registry (method) and
            # _decorated_grpc_action_registry(dict) that have dictionnary data with
            # data like grpc_action parameter allowing to register them
            registry.update(parent.get_class_action_registry(service))

        return registry

    @classmethod
    def get_class_action_registry(cls, service):
        """
        Returns all the grpc action registries (decorated and dynamic) of the class
        """
        registry = {}
        if "_decorated_grpc_action_registry" in cls.__dict__:
            registry.update(cls._decorated_grpc_action_registry)
        if "_dynamic_grpc_action_registry" in cls.__dict__:
            registry.update(cls._dynamic_grpc_action_registry(service))
        return registry

    @classmethod
    def get_action_parents(cls):
        """
        Returns all the GRPCActionMixin parents of the class in mro order
        """
        return [base for base in cls.mro() if issubclass(base, GRPCActionMixin)]

    @classmethod
    def register_actions(cls):
        """
        Call the `_before_registration` method of all the parents
        Then iterate over the action registry and register the grpc actions
        """
        cls.before_registration()
        for action, kwargs in cls.get_parents_action_registry(cls()).items():
            register_action(cls, action, **kwargs)

    def _before_registration(service_class):
        """
        This should be overriden in your service or mixin if you want a specific behavior for a mixin
        Method called before gRPC actions registration
        """
        pass

    def _dynamic_grpc_action_registry(service) -> Dict[str, Dict[str, Any]]:
        """Dynamic gRPC action registry"""
        return {}
