.. _logging:

Logging
=======

Django-Socio-GRPC has a built-in way to handle the logging of your services.

Usage
-----

Django-Socio-GRPC uses the `standard Django logging system <https://docs.djangoproject.com/en/4.2/topics/logging/#topic-logging-parts-loggers>`_. You can configure it in your settings.py file.

=======
Loggers
=======


django_socio_grpc.request
##############

Log messages related to the handling of gRPC requests.

- If your service raises a `GRPCException`, it will result in a **WARNING** message.
  You can define your own `GRPCException` and set the `log_level` as you wish to change this.
- If your service raises another Exception, it will result in an **ERROR** message.
- Logging of **OK** responses is only activated when in `DEBUG` mode or if `LOG_OK_RESPONSE` settings is set to True

Messages to this logger have the following extra context:

- status_code: The **grpc.StatusCode** returned.
- request: The `GRPCRequestContainer` object that generated the logging message.

Example
-------

With the following service :

.. code-block:: python

    class SomethingService(Service):

        @grpc_action(request=[], response=[])
            async def RaiseUncaughtException(self, request, context):
            raise ValueError("test log")

        @grpc_action(request=[], response=[])
            async def RaiseGrpcException(self, request, context):
            raise NotFound("test log")

With the following logging settings :

.. code-block:: python

    LOGGING = {
        ...,
        "formatters": {
            ...,
            "classic": {
                "format": "{levelname} {message}",
            },
        },
        "handlers": {
            ...,
            "request": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
        },
        "loggers": {
            ...,
            "django_socio_grpc.request": {"handlers": ["request"], "level": "WARNING", "propagate": False},
        },
    }

You will get the following logs :

.. code-block::

    WARNING NotFound : SomethingService/RaiseGRPCException
    ERROR ValueError : SomethingService/RaiseUncaughtException
