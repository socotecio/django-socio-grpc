"""
>>> MyMixin(GRPCActionMixin, abstract=True):
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
import logging
from typing import Any, Dict, Optional

from django_socio_grpc.utils.registry_singleton import (
    RegistrySingleton,
    get_message_name_from_field_or_serializer_instance,
)

logger = logging.getLogger("django_socio_grpc")


class GRPCAction:
    """
    This class wrap a grpc method in a service to be able to register it in RegistrySingleton
    """

    def __init__(
        self,
        function,
        request=None,
        response=None,
        request_name=None,
        response_name=None,
        request_stream=False,
        response_stream=False,
        use_request_list=False,
        use_response_list=False,
        *args,
        **kwargs,
    ):
        self.request = request
        self.response = response
        self.request_name = request_name
        self.response_name = response_name
        self.request_stream = request_stream
        self.response_stream = response_stream
        self.use_request_list = use_request_list
        self.use_response_list = use_response_list
        self.function = function

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
            return
        self.register(owner, name)

    def __get__(self, obj, type=None):
        return self.__class__(self.function.__get__(obj, type), **self.get_action_params())

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

    def register(self, owner, name):
        try:
            service_registry = RegistrySingleton()

            # INFO - LG - 31/05/2022 - Replace SelfSerializer placeholder with the real serializer
            service_instance = owner()
            service_instance.action = name
            serializer_class = service_instance.get_serializer_class()
            if self.request is SelfSerializer:
                self.request = serializer_class
            if self.response is SelfSerializer:
                self.response = serializer_class

            # Replace AttrPlaceholders with matching attribute
            for k, v in self.get_action_params().items():
                if isinstance(v, AttrPlaceholder):
                    setattr(self, k, v(service_instance))

            service_registry.register_custom_action(
                service_class=owner, function_name=name, **self.get_action_params()
            )
        except Exception as e:
            logger.exception(f"Error while registering grpc_action {owner} - {name}: {e}")
        setattr(owner, name, self.function)


class GRPCActionMixinMeta(abc.ABCMeta):
    def before_registration(cls, service_class=None):
        """
        Call all the service_class parents `_before_registration` methods
        """
        if not service_class:
            service_class = cls
        for base in cls._action_parents[::-1]:
            if "_before_registration" in base.__dict__:
                base._before_registration(service_class)

    def get_grpc_action_registry(cls, service_class=None):
        """
        return all the grpc action registries (static and dynamic) of all the parent mixin
        """
        if not service_class:
            service_class = cls
        registry = {}
        # INFO - AM - 25/05/2022 - _action_parents is all the parents instance that inherit from GRPCActionMixin and the instance itself to merge all the mixin action registry in one in the mro order
        for parent in cls._action_parents[::-1]:
            # INFO - AM - 25/05/2022 - if the parent inherit from GRPCActionMixin it will have _dynamic_grpc_action_registry (method) and _decorated_grpc_action_registry(dict) that have dictionnary data with data like grpc_action parameter allowing to register them
            if "_decorated_grpc_action_registry" in parent.__dict__:
                registry.update(parent._decorated_grpc_action_registry)
            if "_dynamic_grpc_action_registry" in parent.__dict__:
                registry.update(parent._dynamic_grpc_action_registry(service_class()))

        return registry

    @property
    def _action_parents(cls):
        return [base for base in cls.mro() if issubclass(base, GRPCActionMixin)]

    # INFO - AM - 25/05/2022 - register_actions iterate over the grpc_action_registry that use the private property _dynamic_grpc_action_registry and _decorated_grpc_action_registry that are populated automatically to register the mixins actions
    def register_actions(cls):
        cls.before_registration()
        for action, kwargs in cls.get_grpc_action_registry().items():
            register_action(cls, action, **kwargs)


def register_action(cls, action_name: str, name: Optional[str] = None, **kwargs):
    """
    Register action take function_name of mixin and register them if they are decorated (so already a GRPCAction)
    or transform them into a GRPCAction before registring them
    """

    # INFO - AM - 25/05/2022 - get function in service. This can be a function or a GRPCAction if used with decorator
    action = getattr(cls, action_name)

    # Action is already a GRPC Action
    if not isinstance(action, GRPCAction):
        action = GRPCAction(action, **kwargs)

    action.register(cls, name or action.function.__name__)


class GRPCActionMixin(metaclass=GRPCActionMixinMeta):

    _decorated_grpc_action_registry: Dict[str, Dict[str, Any]]
    """Static gRPC action registry"""

    _abstract = True

    def __init_subclass__(cls, abstract=False) -> None:
        """
        INFO - AM - 25/05/2022 - __init_subclass__ allow to register the mixins actions with the child name to generate the corect proto
        Example: ListIdMixin have a Listids method and we want it inside the BasicService. We need to pass BasicService as owner to register_custom_action
        """
        super().__init_subclass__()

        if "_abstract" not in cls.__dict__:
            cls._abstract = abstract

        if cls._abstract:
            return

        # INFO - AM - 25/05/2022 - register actions will get _decorated_grpc_action_registry of all Mixin that the service inherit to register t
        cls.register_actions()

    def _before_registration(service):
        """
        This should be overriden in your service or mixin if you want a specific behavior for a mixin
        Method called before gRPC actions registration
        """
        pass

    def _dynamic_grpc_action_registry(service) -> Dict[str, Dict[str, Any]]:
        """Dynamic gRPC action registry"""
        return {}


SelfSerializer = object()
"""Use this placeholder object when you need the matching service serializer"""


class AttrPlaceholder:
    """Use this placeholder class to dynamically get an attribute of the service"""

    def __init__(self, attr_name: str):
        self.attr_name = attr_name

    def __call__(self, service):
        return getattr(service, self.attr_name)


def get_serializer_and_base_name(service, action: Optional[str] = None):
    service = service.__class__()
    if action:
        service.action = action
    serializer = service.get_serializer_class()
    message_name = get_message_name_from_field_or_serializer_instance(
        serializer(), append_type=False
    )

    return serializer, message_name
