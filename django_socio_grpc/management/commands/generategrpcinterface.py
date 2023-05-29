# -*- coding: utf-8 -*-
"""
The Django socio gRPC interface Generator is a  which can automatically generate
(scaffold) a Django grpc interface for you. By doing this it will introspect your
models and automatically generate an table with properties like:

 - `fields` for all local fields

"""

import re
import os
import logging

from django.apps import apps
from django.conf import settings
from django.core.management.base import LabelCommand, CommandError
from django.db import models


# Configurable constants
MAX_LINE_WIDTH = getattr(settings, 'MAX_LINE_WIDTH', 120)
INDENT_WIDTH = getattr(settings, 'INDENT_WIDTH', 4)


class Command(LabelCommand):
    help = '''Generate all required gRPC interface files, like serializers, services and `handlers.py` for the given app (models)'''
    # args = "[app_name]"
    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument('app_name', help='Name of the app to generate the gRPC interface for')
        #parser.add_argument('model_name', nargs='*')

    #@signalcommand
    def handle(self, *args, **options):
        self.app_name = options['app_name']

        logging.warning("!! only a scaffold is generated, please check/add content to the generated files !!!")

        try:
            app = apps.get_app_config(self.app_name)
        except LookupError:
            self.stderr.write('This command requires an existing app name as argument')
            self.stderr.write('Available apps:')
            app_labels = [app.label for app in apps.get_app_configs()]
            for label in sorted(app_labels):
                self.stderr.write('    %s' % label)
            return

        model_res = []
        # for arg in options['model_name']:
        #     model_res.append(re.compile(arg, re.IGNORECASE))

        GRPCInterfaceApp(app, model_res, **options)

        #self.stdout.write()


class GRPCInterfaceApp():
    def __init__(self, app_config, model_res, **options):
        self.app_config = app_config
        self.model_res = model_res
        self.options = options
        self.app_name = options['app_name']

        self.serializers_str = ""
        self.services_str = ""
        self.handler_str = ""
        self.model_names = [model.__name__ for model in self.app_config.get_models()]

        self.generate_serializers()
        self.generate_services()
        self.generate_handlers()


    def generate_serializer_imports(self):
        self.serializers_str += f"""## generated with django-socio-grpc generateprpcinterface {self.app_name}  (LARA-version)

import logging

from django_socio_grpc import proto_serializers
#import {self.app_name}.grpc.{self.app_name}_pb2 as {self.app_name}_pb2

from {self.app_name}.models import {', '.join(self.model_names)}\n\n"""

    def generate_serializers(self):
        self.generate_serializer_imports()

        # generate serializer classes

        for model in self.app_config.get_models():
            fields = [field.name for field in model._meta.fields if "_id" not in field.name]
            #     fields_param_str = ", ".join([f"{field}=None" for field in fields])
            #     fields_str = ",".join([f"\n{4 * INDENT_WIDTH * ' '}'{field}'" for field in fields])
            fields_str = ", ".join([f"{field}'" for field in fields])

            self.serializers_str += f"""class {model.__name__.capitalize()}ProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = {model.__name__}
        # proto_class = {self.app_name}_pb2.{model.__name__.capitalize()}Response \n
        # proto_class_list = {self.app_name}_pb2.{model.__name__.capitalize()}ListResponse \n

        fields = '__all__' # [{fields_str}] \n\n"""

        # check, if serializer.py exists
        # then ask, if we should append to file

        if os.path.isfile("serializers.py"):
            append = input("serializers.py already exists, append to file? (y/n) ")
            if append.lower() == "y":
                with open("serializers.py", "a") as f:
                    f.write(self.serializers_str)
        else:
            # write sef.serializers_str to file
            with open("serializers.py", "w") as f:
                f.write(self.serializers_str)

    def generate_services_imports(self):
        self.services_str += f"""## generated with django-socio-grpc generateprpcinterface {self.app_name}  (LARA-version)

from django_socio_grpc import generics
from .serializers import {', '.join([model.capitalize() + "ProtoSerializer" for model in self.model_names])}\n\n
from {self.app_name}.models import {', '.join(self.model_names)}\n\n"""


    def generate_services(self):
        self.generate_services_imports()

        # generate service classes
        for model in self.model_names:
            self.services_str += f"""class {model.capitalize()}Service(generics.ModelService):
    queryset = {model}.objects.all()
    serializer_class = {model.capitalize()}ProtoSerializer\n\n"""
        
        # check, if services.py exists
        # then ask, if we should append to file

        if os.path.isfile("services.py"):
            append = input("services.py already exists, append to file? (y/n) ")
            if append.lower() == "y":
                with open("services.py", "a") as f:
                    f.write(self.services_str)
        else:
            # write self.services_str to file
            with open("services.py", "w") as f:
                f.write(self.services_str)


    def generate_handler_imports(self):
        self.handler_str += f"""# generated with django-socio-grpc generateprpcinterface {self.app_name}  (LARA-version)

#import logging
from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
from {self.app_name}.grpc.services import {', '.join([model.capitalize() + "Service" for model in self.model_names])}\n\n"""

    def generate_handlers(self):
        self.generate_handler_imports()

        # generate handler functions
        self.handler_str += f"""def grpc_handlers(server):
    app_registry = AppHandlerRegistry("{self.app_name}", server)\n"""

        for model in self.model_names:
            self.handler_str += f"""
    app_registry.register({model.capitalize()}Service)\n"""
            
        # check, if handlers.py exists
        # then ask, if we should append to file

        if os.path.isfile("handlers.py"):
            append = input("handlers.py already exists, append to file? (y/n) ")
            if append.lower() == "y":
                with open("handlers.py", "a") as f:
                    f.write(self.handler_str)
        else:
            # write self.handler_str to file
            with open("handlers.py", "w") as f:
                f.write(self.handler_str)



