.. _logging:

Logging
=======

Description
-----------

Django-Socio-GRPC has a built-in way to handle the logging of the errors of your services.
    
Usage
-----

Django-Socio-GRPC uses a system of logging based on the one used by Django. `Documentation <https://docs.djangoproject.com/fr/4.2/topics/logging/#topic-logging-parts-loggers>`_.

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
Logging GRPC Requests
=====================

Django-Socio-GRPC by default log requests only when something goes wrong just like Django does.
    - If your service raises a GRPCException, it will result by default to a Warning.
      You can define your own GRPCException and set the log_level as you wish to change this.
    - If your service raises another Exception, it will result in an Error.
    - Logging incoming request is only activated when in DEBUG mode or if LOG_OK_RESPONSE settings is set to True

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
        },
        "handlers": {
            "null": {"level": "DEBUG", "class": "logging.NullHandler"},
            "console": {
                "level": logging.DEBUG if DEBUG else logging.INFO,
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "classic",
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
    [django]-[WARNING]-[2023-11-17T10:32:58.099154]-[django_socio_grpc.request:283] NotFound : test log from testgrpc in test-infra-back: RaiseGRPCException
    [django]-[ERROR]-[2023-11-17T10:37:57.276262]-[django_socio_grpc.request:291] ValueError : test log from testgrpc in test-infra-back: RaiseException