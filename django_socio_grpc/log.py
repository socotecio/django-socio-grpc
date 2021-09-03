"""
logging utils
"""
import asyncio
import logging
import logging.config
import sys
import threading
import traceback
from datetime import datetime

from django_socio_grpc.settings import grpc_settings


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
        if grpc_settings.LOGGING_ACTION:
            await grpc_settings.LOGGING_ACTION(record, is_intercept_except)

    def call_user_handler_sync(self, record, is_intercept_except):
        if grpc_settings.LOGGING_ACTION:
            grpc_settings.LOGGING_ACTION(record, is_intercept_except)

    def log_unhandled_exception(self, e_type, e_value, e_traceback):
        traceback.print_exception(e_type, e_value, e_traceback)
        formatted_exception = traceback.format_exception(e_type, e_value, e_traceback)

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

        # INFO - FB - 21/07/2021 - transform string like: in <function_name>\n    <text line that raise error>\n' to <function_name>
        func_name = text_function_and_line_error.split("\n")[0].replace("in", "").strip()

        return (pathname, lineno, func_name)


grpcHandler = GRPCHandler()
sys.excepthook = grpcHandler.log_unhandled_exception
