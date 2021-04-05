"""
Server for grpc_framework.
"""
from concurrent import futures
import contextlib

import grpc

from django.conf import settings

from grpc_framework.settings import grpc_settings
from grpc_framework.service import Service
from grpc_framework.signals import grpc_server_init, grpc_server_started, grpc_server_shutdown
from grpc_framework.utils.log import configure_logging
from grpc_framework.exceptions import ServerException


class GrpcServer:
    """GrpcServer"""

    def __init__(self, max_workers=5, ssl=False):
        self.max_workers = max_workers
        self.ssl = ssl
        self.interceptors = self.add_interceptors()
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.max_workers),
                                  interceptors=self.interceptors)
        grpc_server_init.send(None, server=self.server)
        configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)

    def add_interceptors(self):
        interceptors = []
        for interceptor in grpc_settings.INTERCEPTORS:
            interceptors.append(interceptor[0](**interceptor[1]))
        return interceptors

    @contextlib.contextmanager
    def start(self, address, port, *args, **kwargs):
        self.add_services()
        if self.ssl is True:
            server_certificate_key = kwargs.pop('certificate_key', None)
            server_certificate = kwargs.pop('certificate', None)
            root_certificate = kwargs.pop('root_certificate', None)
            if not server_certificate_key or not server_certificate:
                raise ServerException

            require_client_auth = True if root_certificate else False
            server_credentials = grpc.ssl_server_credentials(((server_certificate_key, server_certificate),),
                                                             root_certificate, require_client_auth)
            self.server.add_secure_port(f'{address}:{port}', server_credentials)

        else:
            self.server.add_insecure_port(f'{address}:{port}')

        grpc_server_started.send(None, server=self.server)
        self.server.start()

        try:
            yield self.server
        finally:
            grpc_server_shutdown.send(None, server=self.server)

    def add_services(self):
        grpc_apps = grpc_settings.grpc_apps
        for grpc_app in grpc_apps:
            service = Service(grpc_app)
            handler = service.find_handler()
            handler(service.service_class(), self.server)
