import django.db.models.options as options
from django.apps import AppConfig
from django.db import close_old_connections, reset_queries

from django_socio_grpc import signals

# Used to add options in class meta for customizing the proto file génération
options.DEFAULT_NAMES = options.DEFAULT_NAMES + ("grpc_messages", "grpc_methods")


class DjangoSocioGrpcConfig(AppConfig):
    name = "django_socio_grpc"
    verbose_name = "Django Socio gRPC"

    def ready(self):
        signals.grpc_action_started.connect(reset_queries)
        signals.grpc_action_started.connect(close_old_connections)
        signals.grpc_action_finished.connect(close_old_connections)
