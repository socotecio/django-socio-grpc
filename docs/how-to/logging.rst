Logging
=======

Description
-----------

Django-Socio-GRPC has a built-in way to handle the logging of the errors of your services.
    
Usage
-----

Django-Socio-GRPC uses a system of logging based on the one used by Django.

Here's a short reminder on the system it uses.

It uses 4 main objects for it.
    - Loggers
    - Handlers
    - Filters
    - Formatters

=======
Loggers
=======

A logger is the entry point into the logging system. Each logger is a named bucket to which messages can be written for processing.

A logger is configured to have a log level. This log level describes the severity of the messages that the logger will handle. Python defines the following log levels:

    - DEBUG: Low level system information for debugging purposes
    - INFO: General system information
    - WARNING: Information describing a minor problem that has occurred.
    - ERROR: Information describing a major problem that has occurred.
    - CRITICAL: Information describing a critical problem that has occurred.

========
Handlers
========

The handler is the engine that determines what happens to each message in a logger. It describes a particular logging behavior, such as writing a message to the screen, to a file, or to a network socket.

Like loggers, handlers also have a log level. If the log level of a log record doesn’t meet or exceed the level of the handler, the handler will ignore the message.

=======
Filters
=======

A filter is used to provide additional control over which log records are passed from logger to handler.

==========
Formatters
==========

Ultimately, a log record needs to be rendered as text. Formatters describe the exact format of that text. A formatter usually consists of a Python formatting string containing LogRecord attributes; however, you can also write custom formatters to implement specific formatting behavior.


Here's an example of a Logging setup that uses all four of these objects.

.. code-block:: python
    LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "special": {
            "()": "project.logging.SpecialFilter",
            "foo": "bar",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["special"],
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": True,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "myproject.custom": {
            "handlers": ["console", "mail_admins"],
            "level": "INFO",
            "filters": ["special"],
        },
    },
}

=====================
Logging GRPC Services
=====================

You'll want to be able to log information about your grpc services.
Django-Socio-GRPC is built-in with existing loggers to get information from GRPC services

If you want to add information to your logs from grpc. You will need to reproduce something similar to these two functions.

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

            record.grpc_service_name = ""
            record.grpc_action = ""
            record.grpc_user_pk = ""

            if hasattr(servicer_ctx, "service"):
                log_extra_context = default_get_log_extra_context(servicer_ctx.service)

                for key, value in log_extra_context.items():
                    setattr(record, key, value)

            return record

        logging.setLogRecordFactory(record_factory)

In this example it will enable you to define formatters like this for example.

.. code-block:: python
    "formatters": {
        "django_socio_grpc_formatter": {
            "format": "{levelname} {grpc_service_name} {grpc_action} {grpc_user_pk} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    }


=====================
Logging GRPC Requests
=====================

Django-Socio-GRPC by default log requests only when something goes wrong just like Django does.
    - If your service raises a GRPCException, it will result by default to a Warning.
      You can define your own GRPCException and set the log_level as you wish to change this.
    - If your service raises another Exception, it will result in an Error.
    - Lastly, if you want to log requests even if they are ok, you can launch django in DEBUG mode
      or you can enable LOG_OK_RESPONSE in your settings.

Example
-------

Let's set up a simple logging process and see the results

Here's an example of logging setup.

.. code-block:: python
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
        "formatters": {
            "classic": {
                "format": "[django]-[%(levelname)s]-[%(asctime)s]-[%(name)s:%(lineno)s] %(message)s"
            },
            "fmt": {
                "format": 'level=%(levelname)s name=%(name)s line=%(pathname)s:%(lineno)s message="%(message)s" socio_service_name="%(socio_service_name)s" socio_action="%(socio_action)s" time=%(asctime)s levelno=%(levelno)s socio_usermanagement_uuid="%(socio_usermanagement_uuid)s" socio_user_roles="%(socio_user_roles)s" socio_client_id="%(socio_client_id)s" funcName=%(funcName)s',
            },
        },
        "handlers": {
            "null": {"level": "DEBUG", "class": "logging.NullHandler"},
            "console": {
                "level": logging.DEBUG if DEBUG else logging.INFO,
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "fmt",
            },
        },
        "loggers": {
            "django.db.backends": {"handlers": ["console"], "propagate": False},
            "django.utils.autoreload": {"handlers": ["console"]},
            "django.security.DisallowedHost": {"handlers": ["null"], "propagate": False},
            "django": {"handlers": ["console"], "propagate": True},
            "": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        },
    }

With services like this :

.. code-block:: python

    class SomethingService(generics.AsyncModelService):
        queryset = Something.objects.all()
        serializer_class = SomethingProtoSerializer

    @grpc_action(request=[], response=[])
    async def LogError(self, request, context):
        logger.error("test log from testgrpc in test-infra-back: LogError")
        return empty_pb2.Empty()

    @grpc_action(request=[], response=[])
        async def RaiseException(self, request, context):
        raise ValueError("test log from testgrpc in test-infra-back: RaiseException")

    @grpc_action(request=[], response=[])
        async def RaiseGrpcException(self, request, context):
        raise NotFound("test log from testgrpc in test-infra-back: RaiseGRPCException")

It will result in logs like this :

.. code-block::
    level=WARNING name=django_socio_grpc.request line=/opt/code/django_socio_grpc/services/servicer_proxy.py:283 message="NotFound : test log from testgrpc in test-infra-back: RaiseGRPCException"
    socio_service_name="Something" socio_action="RaiseGrpcException" time=2023-11-17T10:32:58.099154 levelno=40 socio_usermanagement_uuid="098410fd-56ed-4efa-bfa8-394439827c6f" socio_user_roles="" socio_client_id="" funcName=async_process_exception
    level=ERROR name=django_socio_grpc line=/opt/code/django_socio_grpc/services/servicer_proxy.py:291 message="ValueError : test log from testgrpc in test-infra-back: RaiseException"
    socio_service_name="Something" socio_action="RaiseException" time=2023-11-17T10:37:57.276262 levelno=40 socio_usermanagement_uuid="098410fd-56ed-4efa-bfa8-394439827c6f" socio_user_roles="" socio_client_id="" funcName=async_process_exception