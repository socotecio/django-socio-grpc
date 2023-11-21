.. _logging:

Logging
=======

Description
-----------

Django-Socio-GRPC has a built-in way to handle the logging of the errors of your services.
    
Usage
-----

Django-Socio-GRPC uses a system of logging based on the one used by Django. `Documentation <https://docs.djangoproject.com/en/4.2/topics/logging/#topic-logging-parts-loggers>`_.


=====================
Logging GRPC Requests
=====================

Django-Socio-GRPC by default log requests only when something goes wrong just like Django does.
    - If your service raises a GRPCException, it will result by default to a Warning.
      You can define your own GRPCException and set the log_level as you wish to change this.
    - If your service raises another Exception, it will result in an Error.
    - Logging incoming request is only activated when in DEBUG mode or if LOG_OK_RESPONSE settings is set to True

These messages have the additionnal context : 

    - status_code: The Grpc_Response code associated with the request.
    - request: The request object.

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