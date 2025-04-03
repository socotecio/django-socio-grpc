.. _getting_started:

Getting Started
===============

Quickstart Guide
----------------

We are going to create a simple blog application with a gRPC service.
The blog application will have the following models: ``User`` and ``Post``.

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

  django-admin startproject dsg_tutorial

Add now the following lines to the ``INSTALLED_APPS`` section of your ``dsg_tutorial/settings.py`` file:

.. code-block:: python

  INSTALLED_APPS = [
    ...
    'django_socio_grpc',
  ]

See `Django tutorial <https://docs.djangoproject.com/en/5.0/intro/tutorial01/>`_ for more information

Adding a New App
~~~~~~~~~~~~~~~~

Then create a new app. First, cd into the project directory:

.. code-block:: bash

  cd dsg_tutorial

Create the new app:

.. code-block:: bash

  python manage.py startapp quickstart

This will create a new directory called ``quickstart`` inside your project directory including python files.

Add the new app to the ``INSTALLED_APPS`` section of your ``dsg_tutorial/settings.py`` file:

.. code-block:: python

  INSTALLED_APPS = [
    ...
    'quickstart',
  ]

Finally migrate the database:

.. code-block:: bash

  python manage.py migrate

See `Django tutorial <https://docs.djangoproject.com/en/5.0/intro/tutorial01/>`_ for more information

.. _getting-started-defining-models:

Defining models
~~~~~~~~~~~~~~~~~~~~~~~
Create your models as described in the `Django documentation <https://docs.djangoproject.com/en/5.0/topics/db/models/>`_ .
Each model is assigned to a table in the database.
It inherits from ``django.db.models.Model`` Django class.
Each attribute represents a field in the table.
For directly working with the database, use the usual Django API (see `Query creation <https://docs.djangoproject.com/en/5.0/topics/db/queries/>`_).

.. code-block:: python

    #quickstart/models.py
    from django.db import models

    class User(models.Model):
        full_name = models.CharField(max_length=70)

    class Post(models.Model):
        # If you are using Django >= 5.0, consider using `db_default` instead of `auto_now_add`: https://docs.djangoproject.com/en/5.1/ref/models/fields/#django.db.models.Field.db_default
        pub_date = models.DateField(auto_now_add=True)
        headline = models.CharField(max_length=200)
        content = models.TextField()
        user = models.ForeignKey(User, on_delete=models.CASCADE)


Defining serializers
~~~~~~~~~~~~~~~~~~~~~~~

Serializers convert the data from the Django database into protobuf format, that can be sent over the network via gRPC, and also back from protobuf into the Django database.

In this simple example, our serializers inherit from ModelProtoSerializer, which is simply an inheritance of DRF's ModelSerializer.
For more extensive use, you can use all the DRF serializer methods: `Django REST framework serializers <https://www.django-rest-framework.org/api-guide/serializers/>`_.

See :ref:`ProtoSerialzer doc page <proto-serializers>` for more information.

  .. code-block:: python

    #quickstart/serializers.py
    from django_socio_grpc import proto_serializers
    from rest_framework import serializers
    from quickstart.models import User, Post

    class UserProtoSerializer(proto_serializers.ModelProtoSerializer):
        # This line is written here as an example,
        # but can be removed as the serializer integrates all the fields in the model
        full_name = serializers.CharField(allow_blank=True)
        class Meta:
            model = User
            fields = "__all__"

    class PostProtoSerializer(proto_serializers.ModelProtoSerializer):
        pub_date = serializers.DateTimeField(read_only=True)

        class Meta:
            model = Post
            fields = "__all__"


.. _define-grpc-service:

Defining gRPC services
~~~~~~~~~~~~~~~~~~~~~~~

Services define the gRPC actions that can be performed, e.g., on your models. :ref:`Its what is used to
generate the protobuf files and gRPC stubs<quickstart-generate-proto>`. So all the gRPC actions that you want in
your proto file should be declared or inhetited in your service.

The gRPC service is the equivalent of the `DRF APIView <https://www.django-rest-framework.org/api-guide/generic-views/>`_ and behaves in a similar way
(it only contains an additional internal layer). See additional note after example for comparaison.

In the the following example we will create 2 services.

- ``UserService``, will be a read-only service (:func:`AsyncReadOnlyModelService<django_socio_grpc.generics.AsyncReadOnlyModelService>`), meaning that
  it will have 2 gRPC actions: `List` and `Retrieve`.
- ``PostService``, will be a read-write service (:func:`AsyncModelService<django_socio_grpc.generics.AsyncModelService>`), meaning that
  it will have 6 gRPC actions: `List`, `Retrieve`, `Create`, `Update`, `PartialUpdate`, `Destroy`.

See :ref:`Mixin section <Generic Mixins>` and :ref:`Proto generation <proto-generation>` documentation to help you understand how actions are declared.

.. code-block:: python

    #quickstart/services.py
    from django_socio_grpc import generics

    from quickstart.models import User, Post
    from quickstart.serializers import UserProtoSerializer, PostProtoSerializer

    # This service will have only the List and Retrieve actions
    class UserService(generics.AsyncReadOnlyModelService):
        queryset = User.objects.all()
        serializer_class = UserProtoSerializer

    # This service will have all the CRUD actions
    class PostService(generics.AsyncModelService):
        queryset = Post.objects.all()
        serializer_class = PostProtoSerializer

.. warning::

  DSG supports both sync and async, but we recommend using async services, since
  sync services will be deprecated in the future versions of DSG.

.. note::

  DSG Generic services and mixins are based on DRF Generic views and mixins,
  so you can create your services in a similar way as you would do with DRF in a class-based services, e.g.:


  In DSG :

  .. code-block:: python

      from django.contrib.auth.models import User
      from quickstart.serializers import UserProtoSerializer
      from django_socio_grpc import generics

      # This is and example of a custom service
      class MyListService(generics.ListCreateService):
          queryset = User.objects.all()
          serializer_class = UserProtoSerializer

  In DRF :

  .. code-block:: python

      from django.contrib.auth.models import User
      from quickstart.serializers import UserProtoSerializer
      from rest_framework import generics

      class MyListService(generics.ListCreateAPIView):
          queryset = User.objects.all()
          serializer_class = UserProtoSerializer



.. _quickstart-register-services:

Register services
~~~~~~~~~~~~~~~~~~~~~~~

You need to register your services in a handler function.
This handler will be the entrypoint for your whole app.
In this quickstart, we will register our services in the ``quickstart/handlers.py`` file.

.. code-block:: python

    # quickstart/handlers.py
    from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
    from quickstart.services import UserService, PostService

    def grpc_handlers(server):
        app_registry = AppHandlerRegistry("quickstart", server)
        app_registry.register(UserService)
        app_registry.register(PostService)

Set its path as the ``ROOT_HANDLERS_HOOK`` of the ``GRPC_FRAMEWORK`` :ref:`settings <Available Settings>` section of your ``dsg_tutorial/settings.py`` file:

.. code-block:: python

    # dsg_tutorial/settings.py
    ...
    GRPC_FRAMEWORK = {
        "ROOT_HANDLERS_HOOK" : 'quickstart.handlers.grpc_handlers',
        ...
    }

.. note::

  To better understand the register process and have recommandation about the ``handlers.py`` file for more complex project please read the :ref:`Service Registry documentation<services-registry>`

.. _quickstart-generate-proto:

Generate the app's Protobuf files and gRPC stubs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To generate (and update) the .proto files and gRPC stubs from the services defined in service.py,
you need to run the following command:

.. code-block:: python

    python manage.py generateproto


See `Proto generation <proto-generation>`_ for more information.


This will generate a folder called ``grpc`` at the root of your Django app.

It contains the three files describing your new gRPC service:

- `quickstart_pb2_grpc.py`
- `quickstart_pb2.py`
- `quickstart.proto`

**DSG generate all the file needed by gRPC. Meaning that you don't need to deal with protofile manually.**

Assign newly generated classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the newly generated ``quickstart/grpc/quickstart.proto`` file,
you can find  the structure of Service, responses message and requests message.

For each serializer of your app attached to a service, you will find the associated protobuf **message**. If the serializer is used as a list you will also find the associated **list message**.

To let the DSG magic opere you need to manually (for now) reassign this generated message to the Serializer. This message exit in python class in the generated ``pb2`` file.

You only need to import the messages in the ``serializers.py``
file and assign them to the serializers, like in the following example:


.. code-block:: python

    #quickstart/serializers.py
    ...
    from quickstart.grpc.quickstart_pb2 import (
        UserResponse,
        UserListResponse,
        PostResponse,
        PostListResponse,
    )

    class UserProtoSerializer(proto_serializers.ModelProtoSerializer):
        ...
        class Meta:
            ...
            proto_class = UserResponse
            proto_class_list = UserListResponse

    class PostProtoSerializer(proto_serializers.ModelProtoSerializer):
        ...
        class Meta:
            ...
            proto_class = PostResponse
            proto_class_list = PostListResponse

Running the Server
~~~~~~~~~~~~~~~~~~

You can now run the gRPC server with the following command:

.. code-block:: python

    python manage.py makemigrations
    python manage.py migrate
    python manage.py grpcrunaioserver --dev

The server is now running on port `50051` by default. See :ref:`How To Web <how-to-web>` to see how to call this server with web client or :ref:`Python example <examples>` for python client example.

To read more about the grpcrunaioserver please :ref:`read the commands documentation <commands-aio-run-server>`

To continue reading consider read:

- :ref:`Unit testing the quickstart app <testing>`
- :ref:`Generic Mixins <Generic Mixins>`
- :ref:`gRPC Action <grpc_action>`
- :ref:`Proto Serializers <proto-serializers>`
- :ref:`Proto generation <proto-generation>`
