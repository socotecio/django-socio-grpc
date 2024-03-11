"""
This module contains all the exceptions that can be raised by DSG.

It builds on top of DRF APIException and adds gRPC status codes to the exceptions.
https://www.django-rest-framework.org/api-guide/exceptions/#apiexception
"""

import json
from typing import Literal, Tuple

import grpc
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from grpc import StatusCode
from rest_framework import status
from rest_framework.exceptions import APIException


class ProtobufGenerationException(Exception):
    """
    An exception class for handling errors related to protobuf generation within DSG. It can be raised with specific information about the app name, model name, and a detail message.
    """

    default_detail = "Unknown"

    def __init__(self, app_name=None, model_name=None, detail=None):
        self.app_name = app_name
        self.model_name = model_name
        self.detail = detail if detail is not None else self.default_detail

    def __str__(self):
        return f"Error on protobuf generation on model {self.model_name} on app {self.app_name}: {self.detail}"


LOGGING_LEVEL = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class GRPCException(APIException):
    """
    Base class for DSG exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    You can also set `.logging_level` property to log the exception with the
    """

    status_code: StatusCode = StatusCode.INTERNAL
    logging_level: LOGGING_LEVEL = "WARNING"


class Unauthenticated(GRPCException):
    """
    Subclass of GRPCException representing the UNAUTHENTICATED gRPC status code. It indicates that authentication credentials were not provided.
    """

    status_code = StatusCode.UNAUTHENTICATED
    default_detail = _("Authentication credentials were not provided.")
    default_code = "not_authenticated"


class PermissionDenied(GRPCException):
    """
    Subclass of GRPCException representing the PERMISSION_DENIED gRPC status code. It indicates that the user does not have permission to perform a certain action.
    """

    status_code = StatusCode.PERMISSION_DENIED
    default_detail = _("You do not have permission to perform this action.")
    default_code = "permission_denied"


class NotFound(GRPCException):
    """
    Subclass of GRPCException representing the NOT_FOUND gRPC status code. It indicates that the requested resource was not found.
    """

    status_code = StatusCode.NOT_FOUND
    default_detail = _("Not found.")
    default_code = "not_found"


class AlreadyExist(GRPCException):
    """
    Subclass of GRPCException representing the ALREADY_EXISTS gRPC status code. It indicates that the requested resource already exists.
    """

    status_code = StatusCode.ALREADY_EXISTS
    default_detail = _("Already exists.")
    default_code = "already_exist"


class InvalidArgument(GRPCException):
    """
    Subclass of GRPCException representing the INVALID_ARGUMENT gRPC status code. It indicates that an invalid argument was provided.
    """

    status_code = StatusCode.INVALID_ARGUMENT
    default_detail = _("Invalid argument.")
    default_code = "invalid_argument"


class Unimplemented(GRPCException):
    """
    Subclass of GRPCException representing the UNIMPLEMENTED gRPC status code. It indicates that the requested operation is not yet implemented.
    """

    status_code = StatusCode.UNIMPLEMENTED
    default_detail = _("Unimplemented.")
    default_code = "unimplemented"


def get_exception_status_code_and_details(exc: Exception) -> Tuple[grpc.StatusCode, str]:
    """
    Get the gRPC status code and details from the exception.
    `rest_framework.exceptions.APIException` HTTP status codes are mapped to gRPC status codes.
    Other exceptions are mapped to `grpc.StatusCode.UNKNOWN`. Their details are the exception class name.
    In debug mode, the details are the exception message.
    """

    if isinstance(exc, APIException):
        status_code = exc.status_code
        if not isinstance(status_code, grpc.StatusCode):
            status_code = HTTP_CODE_TO_GRPC_CODE.get(status_code, grpc.StatusCode.UNKNOWN)
        return status_code, json.dumps(exc.get_full_details())
    else:
        details = type(exc).__name__
        if settings.DEBUG:
            details = str(exc)
        return grpc.StatusCode.UNKNOWN, details


HTTP_CODE_TO_GRPC_CODE = {
    status.HTTP_400_BAD_REQUEST: StatusCode.INVALID_ARGUMENT,
    status.HTTP_401_UNAUTHORIZED: StatusCode.UNAUTHENTICATED,
    status.HTTP_403_FORBIDDEN: StatusCode.PERMISSION_DENIED,
    status.HTTP_404_NOT_FOUND: StatusCode.NOT_FOUND,
    status.HTTP_405_METHOD_NOT_ALLOWED: StatusCode.UNIMPLEMENTED,
    status.HTTP_406_NOT_ACCEPTABLE: StatusCode.INVALID_ARGUMENT,
    status.HTTP_408_REQUEST_TIMEOUT: StatusCode.DEADLINE_EXCEEDED,
    status.HTTP_409_CONFLICT: StatusCode.ABORTED,
    status.HTTP_410_GONE: StatusCode.NOT_FOUND,
    status.HTTP_411_LENGTH_REQUIRED: StatusCode.INVALID_ARGUMENT,
    status.HTTP_412_PRECONDITION_FAILED: StatusCode.FAILED_PRECONDITION,
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: StatusCode.INVALID_ARGUMENT,
    status.HTTP_414_REQUEST_URI_TOO_LONG: StatusCode.INVALID_ARGUMENT,
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: StatusCode.INVALID_ARGUMENT,
    status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE: StatusCode.OUT_OF_RANGE,
    status.HTTP_417_EXPECTATION_FAILED: StatusCode.INVALID_ARGUMENT,
    status.HTTP_422_UNPROCESSABLE_ENTITY: StatusCode.INVALID_ARGUMENT,
    status.HTTP_423_LOCKED: StatusCode.FAILED_PRECONDITION,
    status.HTTP_424_FAILED_DEPENDENCY: StatusCode.FAILED_PRECONDITION,
    status.HTTP_428_PRECONDITION_REQUIRED: StatusCode.FAILED_PRECONDITION,
    status.HTTP_429_TOO_MANY_REQUESTS: StatusCode.RESOURCE_EXHAUSTED,
    status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE: StatusCode.INVALID_ARGUMENT,
    status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS: StatusCode.PERMISSION_DENIED,
    status.HTTP_500_INTERNAL_SERVER_ERROR: StatusCode.INTERNAL,
    status.HTTP_501_NOT_IMPLEMENTED: StatusCode.UNIMPLEMENTED,
    status.HTTP_502_BAD_GATEWAY: StatusCode.INTERNAL,
    status.HTTP_503_SERVICE_UNAVAILABLE: StatusCode.UNAVAILABLE,
    status.HTTP_504_GATEWAY_TIMEOUT: StatusCode.DEADLINE_EXCEEDED,
    status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED: StatusCode.UNIMPLEMENTED,
    status.HTTP_507_INSUFFICIENT_STORAGE: StatusCode.RESOURCE_EXHAUSTED,
    status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED: StatusCode.UNAUTHENTICATED,
}
"""
Map HTTP status codes to gRPC status codes. Allows the handling of DRF exceptions.
DSG must return gRPC status codes to the client.

https://grpc.github.io/grpc/core/md_doc_statuscodes.html
https://www.rfc-editor.org/rfc/rfc9110.html
"""
