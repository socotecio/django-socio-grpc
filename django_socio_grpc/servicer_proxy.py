import logging
import os

import grpc
from django import db

from django_socio_grpc.exceptions import GRPCException
from django_socio_grpc.request_transformer.grpc_socio_proxy_context import (
    GRPCSocioProxyContext,
)

logger = logging.getLogger("django_socio_grpc")


def not_implemented(request, context):
    """Method not implemented"""
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details("Method not implemented!")
    raise NotImplementedError("Method not implemented!")


class ServicerProxy:
    def __init__(self, ServiceClass, **initkwargs):
        self.service_instance = ServiceClass(**initkwargs)
        self.grpc_async = os.environ.get("GRPC_ASYNC")

    def call_handler(self, action):
        if self.grpc_async:
            print("async_handler")

            async def async_handler(request, context):
                # db connection state managed similarly to the wsgi handler
                db.reset_queries()
                # INFO - AM - 22/04/2021 - next line break tests. Need to more understand the drowback about memory in production
                # db.close_old_connections()
                try:
                    self.service_instance.request = request
                    self.service_instance.context = GRPCSocioProxyContext(context, action)
                    self.service_instance.action = action
                    self.service_instance.before_action()

                    # INFO - AM - 05/05/2021 - getting the real function in the service and then calling it if necessary
                    instance_action = getattr(self.service_instance, action)
                    return await instance_action(
                        self.service_instance.request, self.service_instance.context
                    )
                except GRPCException as grpc_error:
                    logger.error(grpc_error)
                    context.abort(grpc_error.status_code, grpc_error.get_full_details())
                finally:
                    # INFO - AM - 22/04/2021 - next line break tests. Need to more understand the drowback about memory in production
                    # db.close_old_connections()
                    pass

            return async_handler
        else:

            def handler(request, context):
                # db connection state managed similarly to the wsgi handler
                db.reset_queries()
                # INFO - AM - 22/04/2021 - next line break tests. Need to more understand the drowback about memory in production
                # db.close_old_connections()
                try:
                    self.service_instance.request = request
                    self.service_instance.context = GRPCSocioProxyContext(context, action)
                    self.service_instance.action = action
                    self.service_instance.before_action()

                    # INFO - AM - 05/05/2021 - getting the real function in the service and then calling it if necessary
                    instance_action = getattr(self.service_instance, action)
                    return instance_action(
                        self.service_instance.request, self.service_instance.context
                    )
                except GRPCException as grpc_error:
                    logger.error(grpc_error)
                    context.abort(grpc_error.status_code, grpc_error.get_full_details())
                finally:
                    # INFO - AM - 22/04/2021 - next line break tests. Need to more understand the drowback about memory in production
                    # db.close_old_connections()
                    pass

            return handler

    def __getattr__(self, action):
        print(action)
        if not hasattr(self.service_instance, action):
            return not_implemented

        return self.call_handler(action)