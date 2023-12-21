Logging
=======

Description
-----------

Here's how you can add extra context to your logging in DSG

Usage
-----

=====================
Logging GRPC Services
=====================

You'll want to be able to log information about your grpc services.
DSG is built-in with :ref:`existing loggers<logging>` to get information from GRPC services

If you want to add information to your logs from grpc. You will need to define something like these two functions and call set_log_record_factory in your settings before any log using your formatter is called.

.. code-block:: python

    def default_get_log_extra_context(service: "GenericService"):
        """
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
        It will allow to inject the default extra context of each service in the log record if needed.
        If this method is call before any log you can use grpc_service_name, grpc_action, grpc_user_pk in your log formatter
        """
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            from django_socio_grpc.services.servicer_proxy import get_servicer_context

            servicer_ctx = get_servicer_context()

            record = old_factory(*args, **kwargs)

            """
            Setting default so formatter doesn't crash if data is missing
            """
            record.grpc_service_name = ""
            record.grpc_action = ""
            record.grpc_user_pk = ""

            if hasattr(servicer_ctx, "service"):
                log_extra_context = default_get_log_extra_context(servicer_ctx.service)

                for key, value in log_extra_context.items():
                    setattr(record, key, value)

            return record

        logging.setLogRecordFactory(record_factory)

In this example it will enable you to define formatters like these:

.. code-block:: python

    "formatters": {
        "django_socio_grpc_formatter": {
            "format": "[django]-[%(levelname)s]-[%(asctime)s]-[%(name)s:%(lineno)s] [{grpc_service_name} {grpc_action} {grpc_user_pk}] %(message)s",
        },
        "simple": {
            "format": "[django]-[%(levelname)s]-[%(asctime)s]-[%(name)s:%(lineno)s] %(message)s",
        },
    }
