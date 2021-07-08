"""
logging utils
"""
import logging

from django_socio_grpc.settings import grpc_settings

DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "socio_grpc_format": {
            "format": "{asctime}:{levelno}:{name}:{pathname}:{funcName}:{lineno:d}:{levelname}:{message}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        },
    },
    "handlers": {
        "socio_grpc_handler": {
            "level": "DEBUG",
            "class": "django_socio_grpc.log.GRPCHandler",
            "formatter": "socio_grpc_format",
        },
    },
    "loggers": {
        "socio_grpc_logger": {"handlers": ["socio_grpc_handler"], "propagate": False},
    },
}

class GRPCHandler(logging.Handler):
    def emit(self, record):
        self.format(record)
        grpc_settings.LOGGING_ACTION(record)
