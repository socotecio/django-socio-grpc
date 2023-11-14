"""
logging utils
"""
import logging
import logging.config
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django_socio_grpc.generics import GenericService


def default_get_log_extra_context(service: "GenericService"):
    """
    This method and the setting associated is deprecated
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
    This method and the setting associated is deprecated
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
            log_extra_context = default_get_log_extra_context(servicer_ctx.service)

            for key, value in log_extra_context.items():
                setattr(record, key, value)

        return record

    logging.setLogRecordFactory(record_factory)
