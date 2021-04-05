"""
logging utils
"""
import logging
import logging.config

from django.conf import settings
from django.core.management.color import color_style
from django.utils.module_loading import import_string

logger = logging.getLogger('grpc.server')

DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'grpc.server': {
            '()': 'grpc_framework.utils.log.ServerFormatter',
            'format': '[{server_time}] {message} {resp_code} {resp_time}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'grpc.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'grpc.server',
        },
    },
    'loggers': {
        'grpc': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'grpc.server': {
            'handlers': ['grpc.server'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}


def configure_logging(logging_config, logging_settings):
    if logging_config:
        logging_config_func = import_string(logging_config)

        logging.config.dictConfig(DEFAULT_LOGGING)

        if logging_settings:
            logging_config_func(logging_settings)


class RequireDebugFalse(logging.Filter):
    def filter(self, record):
        return not settings.DEBUG


class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        return settings.DEBUG


class ServerFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.style = color_style()
        super().__init__(*args, **kwargs)

    def format(self, record):
        msg = record.msg
        code = getattr(record, 'resp_code', None)
        if code:
            if code == 'success':
                msg = self.style.HTTP_SUCCESS(msg)
            else:
                msg = self.style.HTTP_SERVER_ERROR(msg)

        if self.uses_server_time() and not hasattr(record, 'server_time'):
            record.server_time = self.formatTime(record, self.datefmt)

        record.msg = msg
        return super().format(record)

    def uses_server_time(self):
        return self._fmt.find('{server_time}') >= 0


def log_response(message, response, logger=logger, level=None, exc_info=None):
    if level is None:
        if response['code'] == 'success':
            level = 'info'
        else:
            level = 'error'

    getattr(logger, level)(
        message,
        extra={
            'resp_time': response['resp_time'],
            'resp_code': response['code'],
        },
        exc_info=exc_info
    )
