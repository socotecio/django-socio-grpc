import abc
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union

from django_socio_grpc.grpc_actions.utils import get_serializer_class
from django_socio_grpc.utils.registry_singleton import get_lookup_field_from_serializer

if TYPE_CHECKING:
    from django_socio_grpc.generics import GenericService

    from .actions import GRPCAction


_T = TypeVar("_T")

ServiceCallable = Callable[["GenericService"], _T]


class Placeholder(metaclass=abc.ABCMeta):
    """
    Placeholder is an abstract class used to define a placeholder for a grpc_action parameter
    """

    @abc.abstractmethod
    def __call__(self, service, action: "GRPCAction", field: str):
        pass


class AttrPlaceholder(Placeholder):
    """Simple placeholder class to dynamically get an attribute of the service"""

    def __init__(self, attr_name: str):
        self.attr_name = attr_name

    def __call__(self, service, action: "GRPCAction", field: str):
        attr = getattr(service, self.attr_name)
        setattr(action, field, attr)


class FnPlaceholder(Placeholder):
    """Simple placeholder class to retrieve anything from a function"""

    def __init__(self, fn: ServiceCallable):
        self.fn = fn

    def __call__(self, service, action: "GRPCAction", field: str):
        attr = self.fn(service)
        setattr(action, field, attr)


class StrTemplatePlaceholder(Placeholder):
    def __init__(self, string: str, *params: Union[str, ServiceCallable[str]]) -> None:
        """String template with either service attributes names or functions as parameter

        :param string: Template string to format
        :type string: str
        :param params: Parameters to format the string with
        :type params: *[str, (service) -> str]

        """
        self.string = string
        self.params = params

    def get_param_value(self, service, param: Union[str, ServiceCallable[str]]):
        if isinstance(param, str):
            return getattr(service, param)
        elif callable(param):
            return param(service)
        else:
            raise ValueError(f"Unsupported param type {param}")

    def __call__(self, service, action: "GRPCAction", field: str):

        formatted_string = self.string.format(
            *[self.get_param_value(service, param) for param in self.params]
        )

        setattr(action, field, formatted_string)


def _get_lookup_fields(service):
    serializer = get_serializer_class(service)
    lookup_field = get_lookup_field_from_serializer(serializer(), service)
    return [{"name": lookup_field[0], "type": lookup_field[1]}]


def _get_serializer_class(service):
    return service.get_serializer_class()


LookupField = FnPlaceholder(_get_lookup_fields)
"""Placeholder object to get matching service lookup field message"""

SelfSerializer = FnPlaceholder(_get_serializer_class)
"""Placeholder object to get matching service serializer"""
