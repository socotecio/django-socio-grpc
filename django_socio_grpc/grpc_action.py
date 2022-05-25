import logging

from django_socio_grpc.utils.registry_singleton import RegistrySingleton

import abc
from typing import Any, Dict, Optional

from django_socio_grpc.decorators import grpc_action

logger = logging.getLogger("django_socio_grpc")


class GRPCAction:
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
        if issubclass(owner, GRPCActionMixin):
            if "_decorated_grpc_action_registry" not in owner.__dict__:
                owner._decorated_grpc_action_registry = {}
            owner._decorated_grpc_action_registry.update({name: self.get_action_params()})
        self.register(owner, name)

    def __get__(self, obj, type=None):
        return self.__class__(self.function.__get__(obj, type))

    def __call__(self, *args, **kwargs):
        self.function(*args, **kwargs)

    def get_action_params(self):
        return {
            "request": self.request,
            "request_name": self.request_name,
            "response": self.response,
            "response_name": self.response_name,
            "request_stream": self.request_stream,
            "response_stream": self.response_stream,
            "use_request_list": self.use_request_list,
            "use_response_list": self.use_response_list,
        }

    def register(self, owner, name):
        try:
            service_registry = RegistrySingleton()
            service_registry.register_custom_action(
                service_class=owner,
                function_name=name,
                request=self.request,
                response=self.response,
                request_name=self.request_name,
                response_name=self.response_name,
                request_stream=self.request_stream,
                response_stream=self.response_stream,
                use_request_list=self.use_request_list,
                use_response_list=self.use_response_list,
            )
        except Exception as e:
            logger.exception(f"Error while registering grpc_action {owner} - {name}: {e}")
        setattr(owner, name, self.function)

class GRPCActionMixinMeta(abc.ABCMeta):
    def before_registration(cls, service_class=None):
        if not service_class:
            service_class = cls
        for base in cls._action_parents[::-1]:
            if "_before_registration" in base.__dict__:
                base._before_registration(service_class)

    def grpc_action_registry(cls, service_class=None):
        if not service_class:
            service_class = cls
        registry = {}
        for parent in cls._action_parents[::-1]:
            if "_grpc_action_registry" in parent.__dict__:
                registry.update(parent._grpc_action_registry(service_class))

        return registry

    @property
    def _action_parents(cls):
        return [base for base in cls.mro() if issubclass(base, GRPCActionMixin)]

    def register_actions(cls):
        cls.before_registration()
        for action, kwargs in cls.grpc_action_registry().items():
            register_action(cls, action, **kwargs)


def register_action(cls, action_name: str, name: Optional[str] = None, **kwargs):

    action = getattr(cls, action_name)

    # Action is already a GRPC Action
    if isinstance(action, GRPCAction):
        return
    GRPCAction(action, **kwargs).register(cls, name or action.__name__)


class GRPCActionMixin(metaclass=GRPCActionMixinMeta):

    _decorated_grpc_action_registry: Dict[str, Dict[str, Any]]

    def __init_subclass__(cls, abstract=False) -> None:
        super().__init_subclass__()

        if abstract:
            return

        cls.register_actions()

    def _before_registration(service):
        pass

    def _grpc_action_registry(service) -> Dict[str, Dict[str, Any]]:
        return {}
