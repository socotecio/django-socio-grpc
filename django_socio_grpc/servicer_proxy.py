import asyncio
import logging
import os

from asgiref.sync import async_to_sync, sync_to_async
from django import db

from django_socio_grpc.exceptions import GRPCException, Unimplemented
from django_socio_grpc.request_transformer.grpc_socio_proxy_context import (
    GRPCSocioProxyContext,
)

logger = logging.getLogger("django_socio_grpc")


class ServicerProxy:
    def __init__(self, ServiceClass, **initkwargs):
        self.service_class = ServiceClass
        self.initkwargs = initkwargs
        # TODO - AM - 06/05 - convert to boolean ?
        self.grpc_async = os.environ.get("GRPC_ASYNC", False)

    def call_handler(self, action):
        service_instance = self.create_service()
        if self.grpc_async:

            async def async_handler(request, context):
                # db connection state managed similarly to the wsgi handler
                db.reset_queries()
                # INFO - AM - 30/06/2021 - Need this in production environnement to avoid SSL end of files errors when too much connection on database
                await sync_to_async(close_old_connections)()
                try:
                    service_instance.request = request
                    service_instance.context = GRPCSocioProxyContext(context, action)
                    service_instance.action = action
                    await sync_to_async(service_instance.before_action)()

                    # INFO - AM - 05/05/2021 - getting the real function in the service and then calling it if necessary
                    instance_action = getattr(service_instance, action)
                    return await instance_action(
                        service_instance.request, service_instance.context
                    )
                except GRPCException as grpc_error:
                    logger.error(grpc_error)
                    await context.abort(grpc_error.status_code, grpc_error.get_full_details())
                finally:
                    # INFO - AM - 30/06/2021 - Need this in production environnement to avoid SSL end of files errors when too much connection on database
                    await sync_to_async(close_old_connections)()
                    pass

            return async_handler
        else:

            def handler(request, context):
                # db connection state managed similarly to the wsgi handler
                db.reset_queries()
                # INFO - AM - 30/06/2021 - Need this in production environnement to avoid SSL end of files errors when too much connection on database
                close_old_connections()
                try:
                    service_instance.request = request
                    service_instance.context = GRPCSocioProxyContext(context, action)
                    service_instance.action = action
                    service_instance.before_action()

                    # INFO - AM - 05/05/2021 - getting the real function in the service and then calling it if necessary
                    instance_action = getattr(service_instance, action)
                    if asyncio.iscoroutinefunction(instance_action):
                        instance_action = async_to_sync(instance_action)
                    return instance_action(service_instance.request, service_instance.context)
                except GRPCException as grpc_error:
                    logger.error(grpc_error)
                    context.abort(grpc_error.status_code, grpc_error.get_full_details())
                finally:
                    # INFO - AM - 30/06/2021 - Need this in production environnement to avoid SSL end of files errors when too much connection on database
                    close_old_connections()
                    pass

            return handler

    def create_service(self):
        return self.service_class(**self.initkwargs)

    def __getattr__(self, action):
        if not hasattr(self.service_class, action):
            raise Unimplemented()

        return self.call_handler(action)


def close_old_connections():
    for conn in db.connections.all():
        if conn.get_autocommit():
            conn.close_if_unusable_or_obsolete()
