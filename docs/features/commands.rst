.. _commands:

Commands
===========

DSG extends the set of default commands available in Django (see `Django admin and manage.py <https://docs.djangoproject.com/en/5.0/ref/django-admin/>`_ )

.. _commands-generate-proto:

Generate Proto
--------------

- ``manage.py generateproto`` (see :ref:`proto generation <proto-generation>` )

This command accepts the following arguments:

- ``--project``: Used to specify Django project. Use DJANGO_SETTINGS_MODULE by default
- ``--dry-run``: print proto data without writing them
- ``--no-generate-pb2``: Do not generate PB2 python files
- ``--check``: Return an error if the file generated is different from the file existent
- ``--custom-verbose``: Number from 1 to 4 indicating the verbose level of the generation
- ``--directory``: Directory where the proto files will be generated. Default will be in the apps directories

.. _commands-aio-run-server:

gRPC Run Async IO Server
----------------------------

- ``manage.py grpcrunaioserver``

This command is similar to django's ``manage.py runserver``, except it launches the *asynchronous* gRPC I/O server, hence the name. It is the recommended way to run gRPC services in production.
it accepts the following arguments:

- ``address`` : Optional address for which to open a port.
- ``--max-workers``: Number of maximum worker threads. Only needed for migration from sync to async server. Using it will have no effect if server fully async. See `gRPC doc migration_thread_pool argument <https://grpc.github.io/grpc/python/grpc_asyncio.html#grpc.aio.server>_`
- ``--dev`` Run the server in development mode. This tells Django to use the auto-reloader and run checks.


.. _commands-run-server:

gRPC Run Sync Server
----------------------

- ``manage.py grpcrunserver``

Same as ``grpcrunaioserver`` except this one is for *synchronous* mode. Mind that --max-workers will have no effect here.

.. warning::

    We do not recommend using this command in production. It is provided as a convenience so that you can test your gRPC services locally and will be removed in the future.
