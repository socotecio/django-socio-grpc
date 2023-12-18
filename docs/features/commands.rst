.. _commands:

Commands
===========

Django-socio-grpc lets you add custom commands on top of existing commands available by default in Django (see `Django admin and manage.py <https://docs.djangoproject.com/en/5.0/ref/django-admin/>`_ )
There are only three django-socio-grpc specific commands:

- ``manage.py generateproto`` (see :ref:`proto generation <proto-generation>` )
  
This command accepts the following arguments:

- ``--project``: Used to specify Django project. Use DJANGO_SETTINGS_MODULE by default
- ``--dry-run``: print proto data without writing them
- ``--no-generate-pb2``: Do not generate PB2 python files
- ``--check``: Return an error if the file generated is different from the file existent
- ``--custom-verbose``: Number from 1 to 4 indicating the verbose level of the generation
- ``--directory``: Directory where the proto files will be generated. Default will be in the apps directories

and

- ``manage.py grpcrunaioserver``

This command is similar to django's ``manage.py runserver``, except it launches a grpcaioserver in async mode.
it accepts the following arguments:

- ``address`` : Optional address for which to open a port.
- ``--max-workers``: Number of maximum worker threads. Only needed for migration from sync to async server. Using it will have no effect if server fully async. See `gRPC doc migration_thread_pool argument <https://grpc.github.io/grpc/python/grpc_asyncio.html#grpc.aio.server>_`
- ``--dev`` Run the server in development mode. This tells Django to use the auto-reloader and run checks.


finally:

- ``manage.py grpcrunserver``

Same as ``grpcrunaioserver`` except this one is for sync mode

.. warning::
We do not recommend using this command in production. It is provided as a convenience so that you can test your gRPC services locally and will be removed in the future.