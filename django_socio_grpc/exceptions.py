"""
Handled exceptions raised by socio grpc framework.

this file is almost identical to https://github.com/encode/django-rest-framework/blob/master/rest_framework/exceptions.py
But with the grpc code: https://grpc.github.io/grpc/python/grpc.html#grpc-status-code
This file will grown to support all the gRPC exception when needed
"""
import json
from logging import Logger, getLogger
from typing import Literal

from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from grpc import StatusCode
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

exception_logger = getLogger("django_socio_grpc.exceptions")


def _get_error_details(data, default_code=None):
    """
    Descend into a nested data structure, forcing any
    lazy translation strings or strings into `ErrorDetail`.
    """
    if isinstance(data, (list, tuple)):
        ret = [_get_error_details(item, default_code) for item in data]
        if isinstance(data, ReturnList):
            return ReturnList(ret, serializer=data.serializer)
        return ret
    elif isinstance(data, dict):
        ret = {key: _get_error_details(value, default_code) for key, value in data.items()}
        if isinstance(data, ReturnDict):
            return ReturnDict(ret, serializer=data.serializer)
        return ret

    text = force_str(data)
    code = getattr(data, "code", default_code)
    return ErrorDetail(text, code)


def _get_codes(detail):
    if isinstance(detail, list):
        return [_get_codes(item) for item in detail]
    elif isinstance(detail, dict):
        return {key: _get_codes(value) for key, value in detail.items()}
    return detail.code


def _get_full_details(detail):
    if isinstance(detail, list):
        full_details = [_get_full_details(item) for item in detail]
    elif isinstance(detail, dict):
        full_details = {key: _get_full_details(value) for key, value in detail.items()}
    elif isinstance(detail, str):
        full_details = detail
    else:
        full_details = {"message": detail, "code": detail.code}
    return json.dumps(full_details)


class ErrorDetail(str):
    """
    A string-like object that can additionally have a code.
    """

    code = None

    def __new__(cls, string, code=None):
        self = super().__new__(cls, string)
        self.code = code
        return self

    def __eq__(self, other):
        r = super().__eq__(other)
        if r is NotImplemented:
            return NotImplemented
        try:
            return r and self.code == other.code
        except AttributeError:
            return r

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "ErrorDetail(string={!r}, code={!r})".format(
            str(self),
            self.code,
        )

    def __hash__(self):
        return hash(str(self))


class ProtobufGenerationException(Exception):
    """
    Class for Socio gRPC framework protobuff generation exceptions.
    """

    default_detail = "Unknow"

    def __init__(self, app_name=None, model_name=None, detail=None):
        self.app_name = app_name
        self.model_name = model_name
        self.detail = detail if detail is not None else self.default_detail

    def __str__(self):
        return f"Error on protobuf generation on model {self.model_name} on app {self.app_name}: {self.detail}"


LOGGING_LEVEL = Literal["INFO", "WARNING", "ERROR", "CRITICAL"]


class GRPCException(Exception):
    """
    Base class for Socio gRPC framework runtime exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """

    status_code: StatusCode = StatusCode.INTERNAL
    default_detail: str = _("A server error occurred.")
    default_code: str = "error"
    logging_level: LOGGING_LEVEL = "WARNING"

    def __init__(self, code=None, detail=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        self.detail = _get_error_details(detail, code)

    def __str__(self):
        return str(self.detail)

    def get_codes(self):
        """
        Return only the code part of the error details.

        Eg. {"name": ["required"]}
        """
        return _get_codes(self.detail)

    def get_full_details(self):
        """
        Return both the message & code parts of the error details.

        Eg. {"name": [{"message": "This field is required.", "code": "required"}]}
        """
        return _get_full_details(self.detail)

    def log_exception(self, logger: Logger, message: str, extra={}):
        try:
            log_level = getattr(logger, self.logging_level.lower())
        except AttributeError:
            exception_logger.warning(
                f"Unsupported logging level {self.logging_level}. Defaulting to Warning"
            )
            log_level = logger.warning
        log_level(message, exc_info=self, extra=extra)


class Unauthenticated(GRPCException):
    status_code = StatusCode.UNAUTHENTICATED
    default_detail = _("Authentication credentials were not provided.")
    default_code = "not_authenticated"


class PermissionDenied(GRPCException):
    status_code = StatusCode.PERMISSION_DENIED
    default_detail = _("You do not have permission to perform this action.")
    default_code = "permission_denied"


class NotFound(GRPCException):
    status_code = StatusCode.NOT_FOUND
    default_detail = _("Not found.")
    default_code = "not_found"


class AlreadyExist(GRPCException):
    status_code = StatusCode.ALREADY_EXISTS
    default_detail = _("Already exists.")
    default_code = "already_exist"


class InvalidArgument(GRPCException):
    status_code = StatusCode.INVALID_ARGUMENT
    default_detail = _("Invalid argument.")
    default_code = "invalid_argument"


class Unimplemented(GRPCException):
    status_code = StatusCode.UNIMPLEMENTED
    default_detail = _("Unimplemented.")
    default_code = "unimplemented"
