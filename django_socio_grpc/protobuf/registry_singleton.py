import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Dict

if TYPE_CHECKING:
    from django_socio_grpc.protobuf.app_handler_registry import AppHandlerRegistry

logger = logging.getLogger("django_socio_grpc")


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class RegistrySingleton(metaclass=SingletonMeta):
    """
    Registry Singleton is a singleton container for all the AppHandlerRegistry instances.
    """

    registered_apps: Dict[str, "AppHandlerRegistry"] = field(default_factory=dict)

    _instances: ClassVar = {}

    @classmethod
    def clean_all(cls):
        cls._instances.clear()
