"""
logging utils
"""
import logging
import logging.config
import sys
from datetime import datetime
from traceback import format_exception

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
            "level": "INFO",
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
    def emit(self, record, is_intercept_except=False):
        self.format(record)
        if grpc_settings.LOGGING_ACTION:
            grpc_settings.LOGGING_ACTION(record, is_intercept_except)

    def log_unhandled_exception(self, e_type, e_value, e_traceback):
        formatted_exception = format_exception(e_type, e_value, e_traceback)

        msg = "".join(formatted_exception)
        pathname, lineno, funcName = self.extract_exc_info_from_traceback(formatted_exception)

        record = logging.makeLogRecord(
            {
                "asctime": self.generate_asctime(),
                "name": "django_socio_grpc",
                "levelname": "ERROR",
                "pathname": pathname,
                "lineno": lineno,
                "msg": msg,
                "funcName": funcName,
            }
        )
        self.emit(record, True)

    def generate_asctime(self):
        now = datetime.now()
        str_now = now.strftime("%Y-%m-%d %H:%M:%S")
        return str_now

    def extract_exc_info_from_traceback(self, formatted_exception):
        # INFO - FB - 21/07/2021 - formatted_exception is an array where each item is a line of the traceback from the exeption and the last item is the text of the exception
        # INFO - FB - 21/07/2021 - Getting the -2 element mean getting the line where the exception is raised
        traceback_last_line = formatted_exception[-2]

        # INFO - FB - 21/07/2021 - traceback_last_line look lie: '  File "<pathtofile>", line <linenumber>, in <function_name>\n    <text line that raise error>\n'
        (
            text_path_file,
            text_line_number,
            text_function_and_line_error,
        ) = traceback_last_line.split(",", 2)

        # INFO - FB - 21/07/2021 - transform string like:  File "<pathtofile>" to <pathtofile>
        pathname = text_path_file.strip().split('"')[1]

        # INFO - FB - 21/07/2021 - transform string like: line <linenumber> to <linenumber>
        lineno = text_line_number.replace("line", "").strip()

        # INFO - FB - 21/07/2021 - transform string like: 'in <function_name>\n    <text line that raise error>\n' to <function_name>
        func_name = text_function_and_line_error.split("\n")[0].replace("in", "").strip()

        return (pathname, lineno, func_name)


grpcHandler = GRPCHandler()
sys.excepthook = grpcHandler.log_unhandled_exception
