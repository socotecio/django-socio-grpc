.. _getting_started:
Getting Started
===============

Quickstart Guide
----------------

We are going to create a simple blog application with a gRPC service.
The blog application will have the following models: ``User``, ``Post`` and ``Comment``.

Prerequisites
~~~~~~~~~~~~~

You will need to install the following packages:

- Python (>= 3.8)


Installation
~~~~~~~~~~~~

Install the package via pip:

.. code-block:: bash

  pip install django-socio-grpc


Creating a New Project
~~~~~~~~~~~~~~~~~~~~~~

Now you can create the project by running the following command :

.. code-block:: bash

  django-admin startproject tutorial

Add now the following lines to the ``INSTALLED_APPS`` section of your ``tutorial/settings.py`` file:

.. code-block:: python

  INSTALLED_APPS = [
    ...
    'django_socio_grpc',
  ]


Adding a New App
~~~~~~~~~~~~~~~~

Then create a new app. First, cd into the project directory:

.. code-block:: bash

  cd tutorial

Create the new app:

.. code-block:: bash

  python manage.py startapp quickstart

This will create a new directory called ``quickstart`` inside your project directory including python files.

Add the new app to the ``INSTALLED_APPS`` section of your ``tutorial/settings.py`` file:

.. code-block:: python

  INSTALLED_APPS = [
    ...
    'quickstart',
  ]

Finally migrate the database:

.. code-block:: bash

  python manage.py migrate


.. _define-grpc-service:

Defining a gRPC Service
~~~~~~~~~~~~~~~~~~~~~~~


Running the Server
~~~~~~~~~~~~~~~~~~
