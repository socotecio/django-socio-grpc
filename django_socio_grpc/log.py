"""
logging utils
"""
import asyncio
import json
import logging
import logging.config
import sys
import threading
import traceback
from datetime import datetime
from typing import TYPE_CHECKING

from django_socio_grpc.settings import grpc_settings

if TYPE_CHECKING:
    from django_socio_grpc.generics import GenericService

old_taceback_function = None


class GRPCHandler(logging.Handler):
    def emit(self, record, is_intercept_except=False):
        self.format(record)
        if record.name == "django_socio_grpc" and getattr(record, "emit_to_server", True):
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.call_user_handler(record, is_intercept_except))
            except Exception:
                # Info - AM - 17/08/2021 - This is not working for log in grpcrunaioserver. be careful
                t = threading.Thread(
                    target=self.call_user_handler_sync,
                    args=[record, is_intercept_except],
                    daemon=True,
                )
                t.start()

    async def call_user_handler(self, record, is_intercept_except):
        try:
            if grpc_settings.LOGGING_ACTION:
                await grpc_settings.LOGGING_ACTION(record, is_intercept_except)
        except Exception:
            pass

    def call_user_handler_sync(self, record, is_intercept_except):
        try:
            if grpc_settings.LOGGING_ACTION:
                grpc_settings.LOGGING_ACTION(record, is_intercept_except)
        except Exception:
            pass

    def log_unhandled_exception(self, exc, value=None, tb=None):

        # INFO - AM - 18/02/2023 - value=value, tb=tb still retro compatible but we prepare the next breaking change. TODO when dropping 2.9 support remove this condition
        if sys.version_info[0] >= 3 and sys.version_info[1] >= 10:
            if old_taceback_function is not None:
                old_taceback_function(exc)
            formatted_exception = traceback.format_exception(exc)
        else:
            etype = None
            if value is None or tb is None:
                etype, value, tb = sys.exc_info()
            if old_taceback_function is not None:
                old_taceback_function(etype=etype, value=value, tb=tb)
            formatted_exception = traceback.format_exception(etype=etype, value=value, tb=tb)

        msg = "".join(formatted_exception)
        pathname, lineno, funcName = self.extract_exc_info_from_traceback(formatted_exception)
        # INFO - AG - 11/05/2022 - Send locals variables if exist in location where the exception occurs else send None
        try:
            tb = traceback.TracebackException.from_exception(exc, capture_locals=True)
        except Exception:
            tb = None
        # INFO - AG - 11/05/2022 - format dict of locals variables
        locals = (
            json.dumps(tb.stack[-1].locals, sort_keys=False, indent=4)
            if tb and len(tb.stack) > 1
            else None
        )
        record = logging.makeLogRecord(
            {
                "asctime": self.generate_asctime(),
                "name": "django_socio_grpc",
                "levelname": "ERROR",
                "pathname": pathname,
                "lineno": lineno,
                "msg": msg,
                "locals": locals,
                "funcName": funcName,
            }
        )
        self.emit(record, True)

    def generate_asctime(self):
        now = datetime.now()
        str_now = now.strftime("%Y-%m-%d %H:%M:%S")
        return str_now

    def extract_exc_info_from_traceback(self, formatted_exception):
        if not len(formatted_exception):
            return ("no path", "0", "no formatted exception")
        # INFO - AM - 01/02/2023 - RuntimeError can produce this
        if len(formatted_exception) < 2:
            return ("no path", "0", formatted_exception[0])
        # INFO - FB - 21/07/2021 - formatted_exception is an array where each item is a line of the traceback from the exeption and the last item is the text of the exception
        # INFO - FB - 21/07/2021 - Getting the -2 element mean getting the line where the exception is raised
        traceback_last_line = formatted_exception[-2]

        # INFO - AM - 01/02/2023 - Sometime when exception is raising in exception we need to take 2 line before it line
        if (
            traceback_last_line
            == "\nDuring handling of the above exception, another exception occurred:\n\n"
        ):
            traceback_last_line = formatted_exception[-4]

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

        # INFO - FB - 21/07/2021 - transform string like: in <function_name>\n    <text line that raise error>\n' to <function_name>
        func_name = text_function_and_line_error.split("\n")[0].replace("in", "").strip()

        return (pathname, lineno, func_name)


def default_get_log_extra_context(service: "GenericService"):
    """
    This method is the default used for the grpc_settings: LOG_EXTRA_CONTEXT_FUNCTION.
    It allow logs to have extra data about the current context of the log. Used especially for tracing system.
    """
    extra_context = {
        "grpc_service_name": service.get_service_name(),
        "grpc_action": service.action,
    }
    if hasattr(service.context, "user") and hasattr(service.context.user, "pk"):
        extra_context["grpc_user_pk"] = service.context.user.pk
    return extra_context


def set_log_record_factory():
    """
    This method is not used by default. You juste have to execute it in your app code. Preferentially at some entrypoint.
    It will allow to inject the default extra context of each service in the log record if needed.
    If this method is call before any log you can use grpc_service_name, grpc_action, grpc_user_pk in your log formatter
    """
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        from django_socio_grpc.services.servicer_proxy import get_servicer_context

        servicer_ctx = get_servicer_context()

        record = old_factory(*args, **kwargs)

        record.grpc_service_name = ""
        record.grpc_action = ""
        record.grpc_user_pk = ""

        if hasattr(servicer_ctx, "service"):
            log_extra_context = servicer_ctx.service.get_log_extra_context()

            for key, value in log_extra_context.items():
                setattr(record, key, value)

        return record

    logging.setLogRecordFactory(record_factory)
