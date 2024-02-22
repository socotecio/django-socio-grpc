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
from django_socio_grpc.protobuf.generation_plugin import (
    BaseGenerationPlugin,
    RequestAsListGenerationPlugin,
    ResponseAsListGenerationPlugin,
)
from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.protobuf.proto_classes import (
    EmptyMessage,
    FieldCardinality,
    FieldDict,
    ProtoField,
    ProtoMessage,
    ProtoRpc,
    ProtoService,
    RequestProtoMessage,
    ResponseProtoMessage,
)
from django_socio_grpc.request_transformer.grpc_internal_proxy import GRPCInternalProxyContext
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.constants import (
    DEFAULT_LIST_FIELD_NAME,
    LIST_ATTR_MESSAGE_NAME,
    REQUEST_SUFFIX,
    RESPONSE_SUFFIX,
)
from django_socio_grpc.utils.debug import ProtoGeneratorPrintHelper
from django_socio_grpc.utils.tools import rreplace
from django_socio_grpc.utils.utils import _is_generator, isgeneratorfunction

from .placeholders import Placeholder

logger = logging.getLogger("django_scoio_grpc.generation")

if TYPE_CHECKING:
    from django_socio_grpc.services import Service


RequestResponseType = Union[str, Type[BaseSerializer], Placeholder, List[FieldDict]]


@dataclass
class GRPCAction:
    function: Callable[["Service", Any, GRPCInternalProxyContext], Any]
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
    message_name_constructor_class: Type[MessageNameConstructor] = MessageNameConstructor
    use_generation_plugins: List[Type[BaseGenerationPlugin]] = field(default_factory=list)

    proto_rpc: Optional[ProtoRpc] = field(init=False, default=None)

    def __post_init__(self):
        if isinstance(self.function, SyncToAsync):
            base_function = self.function

            async def func(*args, **kwargs):
                return await base_function(*args, **kwargs)

            self.function = functools.update_wrapper(func, self.function.func)

        if asyncio.iscoroutinefunction(self.function):
            self._is_coroutine = _is_coroutine

        if isgeneratorfunction(self.function):
            self._is_generator = _is_generator

        # DEPRECATED - AM - 22/02/2024
        self._maintain_compat()

    def _maintain_compat(self):
        """
        Transform old arguments to the correct plugins
        """
        warning_message = "You are using %s argument in grpc_action. This argument is deprecated and has been remplaced by a specific GenerationPlugin. Please update following the documentation: TODO"
        if self.use_request_list is not None:
            logger.warning(warning_message.format("use_request_list"))

            if self.request_message_list_attr:
                logger.warning(warning_message.format("request_message_list_attr"))
            self.use_generation_plugins.insert(
                0,
                RequestAsListGenerationPlugin(
                    list_field_name=self.request_message_list_attr or "results"
                ),
            )

        if self.use_response_list is not None:
            logger.warning(warning_message.format("use_response_list"))
            if self.response_message_list_attr:
                logger.warning(warning_message.format("response_message_list_attr"))
            self.use_generation_plugins.insert(
                0,
                ResponseAsListGenerationPlugin(
                    list_field_name=self.response_message_list_attr or "results"
                ),
            )

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
            "message_name_constructor_class": self.message_name_constructor_class,
            "use_generation_plugins": self.use_generation_plugins,
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

    def make_proto_rpc(self, action_name: str, service: Type["Service"]) -> ProtoRpc:
        assert not isinstance(self.request, Placeholder)
        assert not isinstance(self.response, Placeholder)

        req_class = res_class = ProtoMessage
        if grpc_settings.SEPARATE_READ_WRITE_MODEL:
            req_class = RequestProtoMessage
            res_class = ResponseProtoMessage

        # additional_action_fields = service._additional_action_fields()

        name_constructor = self.message_name_constructor_class(
            action_name=action_name, service=service
        )

        request_name = name_constructor.construct_request_name(
            message=self.request, message_name=self.request_name
        )
        request = req_class.create(message=self.request, name=request_name)

        response_name = name_constructor.construct_response_name(
            message=self.response, message_name=self.response_name
        )
        response = res_class.create(message=self.response, name=response_name)

        for generation_plugin in self.use_generation_plugins:
            request, response = generation_plugin.run_validation_and_transform(
                service=service, request_message=request, response_message=response
            )

        if not request.fields:
            request = EmptyMessage

        if not response.fields:
            response = EmptyMessage

        # TODO if not field, (maybe only one field that is Struct) replace by auto import

        # request = self.create_proto_message(
        #     self.request,
        #     self.request_name,
        #     req_class,
        #     action_name,
        #     service,
        #     self.use_request_list,
        #     self.request_message_list_attr,
        #     additional_action_fields,
        # )
        # response = self.create_proto_message(
        #     self.response,
        #     self.response_name,
        #     res_class,
        #     action_name,
        #     service,
        #     self.use_response_list,
        #     self.response_message_list_attr,
        # )

        return ProtoRpc(
            name=action_name,
            request=request,
            response=response,
            request_stream=self.request_stream,
            response_stream=self.response_stream,
        )

    def register(self, owner: Type["Service"], action_name: str):
        # INFO - AM - 29/12/2023 - (PROTO_DEBUG, step: 10, method: register) allow to print the service and action being registered before displaying the proto
        ProtoGeneratorPrintHelper.reset()
        ProtoGeneratorPrintHelper.set_service_and_action(
            service_name=owner.__name__, action_name=action_name
        )
        ProtoGeneratorPrintHelper.print("register ", owner.__name__, action_name)
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

    def _dynamic_grpc_action_registry(service) -> Dict[str, Dict[str, Any]]:
        """Dynamic gRPC action registry"""
        return {}
