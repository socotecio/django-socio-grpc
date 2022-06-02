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

import asyncio
import logging
from asyncio.coroutines import _is_coroutine
from typing import Any, Dict, Optional

from django_socio_grpc.services import Service
from django_socio_grpc.utils.registry_singleton import RegistrySingleton

from .placeholders import Placeholder

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

        self.response_message_name: Optional[None] = None
        self.request_message_name: Optional[None] = None

        if asyncio.iscoroutinefunction(function):
            self._is_coroutine = _is_coroutine

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

            # INFO - LG - 31/05/2022 Iterate over the GRPCAction attributes
            # and resolve all the placeholder instances
            service = owner()
            service.action = name
            for action_param_field, action_param_value in self.get_action_params().items():
                if isinstance(action_param_value, Placeholder):
                    action_param_value(service, self, action_param_field)

            message_names = service_registry.register_custom_action(
                service_class=owner, function_name=name, **self.get_action_params()
            )

            self.response_message_name = message_names[0]
            self.request_message_name = message_names[1]

        except Exception as e:
            logger.exception(f"Error while registering grpc_action {owner} - {name}: {e}")
        setattr(owner, name, self)


class GRPCActionMixinMeta(type):
    def before_registration(cls, service_class=None):
        """
        Call all the service parents `_before_registration` methods
        """
        for base in cls.action_parents[::-1]:
            if "_before_registration" in base.__dict__:
                base._before_registration(service_class or cls)

    def get_parents_action_registry(cls, service):
        """
        return all the grpc action registries (static and dynamic) of all the parent mixin
        """
        registry = {}
        # INFO - AM - 25/05/2022 - action_parents is all the parents
        # instance that inherit from GRPCActionMixin and the instance itself
        # to merge all the mixin action registry in one in the mro order
        for parent in cls.action_parents[::-1]:
            # INFO - AM - 25/05/2022 - if the parent inherit from GRPCActionMixin it
            # will have _dynamic_grpc_action_registry (method) and
            # _decorated_grpc_action_registry(dict) that have dictionnary data with
            # data like grpc_action parameter allowing to register them
            registry.update(parent.get_class_action_registry(service))

        return registry

    def get_class_action_registry(cls, service):
        """
        return all the grpc action registries (static and dynamic) of the class
        """
        registry = {}
        if "_decorated_grpc_action_registry" in cls.__dict__:
            registry.update(cls._decorated_grpc_action_registry)
        if "_dynamic_grpc_action_registry" in cls.__dict__:
            registry.update(cls._dynamic_grpc_action_registry(service))
        return registry

    @property
    def action_parents(cls):
        return [base for base in cls.mro() if issubclass(base, GRPCActionMixin)]

    # INFO - AM - 25/05/2022 - register_actions iterate over the grpc_action_registry
    # that use the private property _dynamic_grpc_action_registry and _decorated_grpc_action_registry
    # that are populated automatically to register the mixins actions
    def register_actions(cls):
        cls.before_registration()
        for action, kwargs in cls.get_parents_action_registry(cls()).items():
            register_action(cls, action, **kwargs)


def register_action(cls, action_name: str, name: Optional[str] = None, **kwargs):
    """
    Register action take function_name of mixin and register them if they are decorated (so already a GRPCAction)
    or transform them into a GRPCAction before registring them
    """

    # INFO - AM - 25/05/2022 - get function in service. This can be a function or
    # a GRPCAction if used with decorator
    action = getattr(cls, action_name)

    if not isinstance(action, GRPCAction):
        action = GRPCAction(action, **kwargs)

    action.register(cls, name or action.function.__name__)


class GRPCActionMixin(metaclass=GRPCActionMixinMeta):

    _decorated_grpc_action_registry: Dict[str, Dict[str, Any]]
    """Static gRPC action registry"""

    _abstract = True

    def __new__(cls, *args, **kwargs):
        if cls._abstract:
            raise TypeError(f"{cls.__name__} is abstract and cannot be instantiated")
        return super().__new__(cls, *args, **kwargs)

    def __init_subclass__(cls, abstract=False) -> None:
        """
        INFO - AM - 25/05/2022 - __init_subclass__ allow to register the mixins actions with the child name to generate the corect proto
        Example: ListIdMixin have a Listids method and we want it inside the BasicService. We need to pass BasicService as owner to register_custom_action
        """
        super().__init_subclass__()

        if "_abstract" not in cls.__dict__:
            # Child need to be Service to not be abstract
            cls._abstract = abstract or not issubclass(cls, Service)

        if cls._abstract:
            return

        cls.register_actions()

    def _before_registration(service_class):
        """
        This should be overriden in your service or mixin if you want a specific behavior for a mixin
        Method called before gRPC actions registration
        """
        pass

    def _dynamic_grpc_action_registry(service) -> Dict[str, Dict[str, Any]]:
        """Dynamic gRPC action registry"""
        return {}
