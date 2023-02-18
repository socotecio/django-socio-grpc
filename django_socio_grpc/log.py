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

from django_socio_grpc.settings import grpc_settings

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

    def add_custom_print_exception(self):
        global old_taceback_function
        old_taceback_function = traceback.print_exception

        # INFO - AM - Compatibility with python 3.5 -> 3.9, Before 3.10 exec is e_type. Be carreful when working with it. TODO whe dropping <3.10 support replace value and tb by exc
        def custom_print_exception(
            exc, value=None, tb=None, limit=None, file=None, chain=True
        ):
            self.log_unhandled_exception(exc, value=value, tb=tb)

        traceback.print_exception = custom_print_exception


grpcHandler = GRPCHandler()
grpcHandler.add_custom_print_exception()
