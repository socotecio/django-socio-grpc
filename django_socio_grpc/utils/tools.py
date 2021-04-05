"""
Generation class for grpc_tools.protoc
"""
import os
import sys
from importlib import import_module

from grpc_tools import protoc

from django.conf import settings


class Generation:
    """Generation class for grpc_tools.protoc"""

    def __init__(self, app):
        self.app = app

    def run(self):
        app_root = import_module(self.app).__path__[0]
        self.build_package_protos(app_root, True)

    def build_package_protos(self, app_root, strict_mode=False):
        base_dir = settings.BASE_DIR
        relative_path = os.path.relpath(app_root, base_dir)
        prefix = relative_path.replace('{}'.format(self.app), '')
        proto_file = '{}/{}.proto'.format(self.app, self.app)

        command = ['grpc_tools.protoc',
                   '-I./{}'.format(prefix),
                   '--python_out=./{}'.format(prefix),
                   '--grpc_python_out=./{}'.format(prefix),
                   ] + [proto_file]
        if protoc.main(command) != 0:
            if strict_mode:
                raise Exception('error: {} failed'.format(command))
            else:
                sys.stderr.write('warning: {} failed'.format(command))
