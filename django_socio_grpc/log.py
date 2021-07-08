"""
logging utils
"""
import logging
import logging.config

from django.utils.module_loading import import_string

from django_socio_grpc.settings import grpc_settings

DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "django_socio_grpc_format": {
            "format": "{asctime}:{levelno}:{name}:{pathname}:{funcName}:{lineno:d}:{levelname}:{message}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        },
    },
    "handlers": {
        "django_socio_grpc_handler": {
            "level": "DEBUG",
            "class": "django_socio_grpc.log.GRPCHandler",
            "formatter": "django_socio_grpc_format",
        },
    },
    "loggers": {
        "django_socio_grpc": {"handlers": ["django_socio_grpc_handler"], "propagate": False},
    },
}


def configure_logging(logging_config, logging_settings):
    if logging_config:
        logging_config_func = import_string(logging_config)

        logging.config.dictConfig(DEFAULT_LOGGING)

        if logging_settings:
            logging_config_func(logging_settings)


class GRPCHandler(logging.Handler):
    def emit(self, record):
        self.format(record)
        grpc_settings.LOGGING_ACTION(record)
