import abc
from typing import TYPE_CHECKING, Callable, TypeVar, Union

from django_socio_grpc.grpc_actions.utils import (
    get_lookup_field_from_serializer,
    get_serializer_class,
)

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
    def resolve(self, service: "GenericService"):
        """
        Resolve the placeholder
        :param service: the service instance
        :param action: the current action
        :return: the resolved value
        """
        raise NotImplementedError

    def __call__(self, service: "GenericService", action: "GRPCAction", field: str):
        setattr(action, field, self.resolve(service))


class AttrPlaceholder(Placeholder):
    """Simple placeholder class to dynamically get an attribute of the service"""

    def __init__(self, attr_name: str):
        self.attr_name = attr_name

    def resolve(self, service: "GenericService"):
        return getattr(service, self.attr_name)


class FnPlaceholder(Placeholder):
    """Simple placeholder class to retrieve anything from a function"""

    def __init__(self, fn: ServiceCallable):
        self.fn = fn

    def resolve(self, service: "GenericService"):
        return self.fn(service)


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

    def resolve(self, service: "GenericService"):
        return self.string.format(
            *[self.get_param_value(service, param) for param in self.params]
        )


def _get_lookup_fields(service):
    serializer = get_serializer_class(service)
    lname, ltype = get_lookup_field_from_serializer(serializer(), service)
    return [{"name": lname, "type": ltype}]


def _get_serializer_class(service):
    return service.get_serializer_class()


LookupField = FnPlaceholder(_get_lookup_fields)
"""Placeholder object to get matching service lookup field message"""

SelfSerializer = FnPlaceholder(_get_serializer_class)
"""Placeholder object to get matching service serializer"""
