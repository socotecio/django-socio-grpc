.. _commands:

Commands
===========

Django-socio-grpc lets you add custom commands on top of existing commands available by default in Django (see `Django admin and manage.py <https://docs.djangoproject.com/en/4.2/ref/django-admin/>`_ )
There are only two django-socio-grpc specific commands:

- ``manage.py generateproto`` (see :ref:`proto generation <proto-generation>` )

and

- ``manage.py grpcrunaioserver``

This command is similar to django's ``manage.py runserver``, except it launches a grpcaioserver.
it accepts the following arguments:

- ``address`` : Optional address for which to open a port.
- ``--max-workers``: Number of maximum worker threads.
- ``--dev`` Run the server in development mode. This tells Django to use the auto-reloader and run checks.