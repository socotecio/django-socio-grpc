.. _health_check:

Health Check
============

DSG has support for health checking through the standard service API `health/v1 <https://github.com/grpc/grpc-proto/blob/master/grpc/health/v1/health.proto>`_.

Usage
-----

The service is automatically added to the server if you enable it in the gRPC settings :

.. code-block:: python
    
    GRPC_FRAMEWORK = {
        "ENABLE_HEALTH_CHECK": True,
    }

The default value is False, if you don't need it, no action is needed.