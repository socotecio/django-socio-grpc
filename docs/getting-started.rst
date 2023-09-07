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




Defining models
~~~~~~~~~~~~~~~~~~~~~~~
Models are created in the same way as in Django (`Django documentation <https://docs.djangoproject.com/fr/4.2/topics/db/models/>`_) .
Each model is assigned to a table in the database.
It inherits from a Python class django.db.models.Model.
Each attribute represents a field in the table.
The API for accessing the database is the same as Django's (`Query creation <https://docs.djangoproject.com/fr/4.2/topics/db/queries/>`_).

  .. code-block:: python

    #quickstart/models.py
    from django.db import models
    class User(models.Model):
    full_name = models.CharField(max_length=70)

    class Post(models.Model):
        pub_date = models.DateField()
        headline = models.CharField(max_length=200)
        content = models.TextField()
        user = models.ForeignKey(User, on_delete=models.CASCADE)


Defining serializers
~~~~~~~~~~~~~~~~~~~~~~~
In this example, our serializers inherit from ModelProtoSerializer, which is simply an inheritance of DRF's ModelSerializer.
For more extensive use, you can use all the DRF serializer methods: `Django REST framework serializers <https://www.django-rest-framework.org/api-guide/serializers/>`_.

  .. code-block:: python

    #quickstart/serializers.py
    from django_socio_grpc import proto_serializers
    from rest_framework import serializers
    from quickstart.models import User, Post, Comment

    class UserProtoSerializer(proto_serializers.ModelProtoSerializer):
        # This line is written here as an example,
        # but can be removed as the serializer integrates all the fields in the model
        full_name = serializers.CharField(allow_blank=True)
        class Meta:
            model = User
            fields = "__all__"

    class PostProtoSerializer(proto_serializers.ModelProtoSerializer):
        pub_date = serializers.DateTimeField(read_only=True)
        user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            pk_field=serializers.UUIDField(format="hex_verbose"),
        )

        class Meta:
            model = Post
            fields = "__all__"


Defining gRPC services
~~~~~~~~~~~~~~~~~~~~~~~
.. _define-grpc-service:

Whereas DRF uses APIView, Django Socio gRPC uses Service.
With the exception of the gRPC internal layer, a Service
is made to work in the same way as a generic DRF APIView.

Django Socio gRPC Framework also supports both sync and async.
In this quickstart, we will make an asynchronous service.

Following the same logic as DRF, Django Socio gRPC uses class-based services.

DSG mixins make it easy to declare one or several of the CRUD actions.
Please refer to the :ref:`Mixin section <Generic Mixins>` for more information.

In the the following example we will create 2 services.

- `UserService`, will be a read-only service (`AsyncReadOnlyModelService`), meaning that
  it will have 2 gRPC actions: `List` and `Retrieve`.
- `PostService`, will be a read-write service (`AsyncModelService`), meaning that
  it will have 6: `List`, `Retrieve`, `Create`, `Update`, `PartialUpdate`, `Destroy`.

  .. code-block:: python

    #quickstart/services.py
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework.pagination import PageNumberPagination
    from django_socio_grpc import generics

    from quickstart.models import User, Post, Comment
    from quickstart.serializer import UserProtoSerializer, PostProtoSerializer, CommentProtoSerializer

    class UserService(generics.AsyncReadOnlyModelService):
        queryset = User.objects.all()
        serializer_class = UserProtoSerializer

    class PostService(generics.AsyncModelService):
        queryset = Post.objects.all()
        serializer_class = PostProtoSerializer


**Note:**

DSG Generic services and mixins are based on DRF Generic views and mixins.

In DSG :

  .. code-block:: python

    from django.contrib.auth.models import User
    from quickstart.serializers import UserProtoSerializer
    from django_socio_grpc import generics

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



Register services
~~~~~~~~~~~~~~~~~~~~~~~

You need to register your services in a handler function.
This handler will be the entrypoint for your whole app.
In this quickstart, we will register our services in the ``quickstart/handlers.py`` file.

  .. code-block:: python

    # quickstart/handlers.py
    from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
    from quickstart.services import UserService, PostService, CommentService,


    def grpc_handlers(server):
        app_registry = AppHandlerRegistry("quickstart", server)
        app_registry.register(UserService)
        app_registry.register(PostService)
        app_registry.register(CommentService)

Set its path as the ``ROOT_HANDLERS_HOOK`` of the ``GRPC_FRAMEWORK`` :ref:`settings <Available Settings>`:

  .. code-block:: python

    # quickstart/settings.py
    ...
    GRPC_FRAMEWORK = {
        "ROOT_HANDLERS_HOOK" : 'quickstart.handlers.grpc_handlers',
        ...
    }


Generate the app's Protobuf files and gRPC stubs
~~~~~~~~~~~~~~~~~~

Run this command :

.. code-block:: python

    python manage.py generateproto

This will generate a folder called ``grpc`` at the root of your Django app.
It contains the three files describing your new gRPC service:

- `quickstart_pb2_grpc.py`
- `quickstart_pb2.py`
- `quickstart.proto`



Assign newly generated classes
~~~~~~~~~~~~~~~~~~

In the ``quickstart/grpc/quickstart.proto`` file,
you can find the generation of the structure of responses and requests.
For each serializer, you will find the basic Response message name and the ListResponse message name.
Serializers need to be assigned to these gRPC messages, which are defined in the ``pb2`` file.
You need to import the messages in the ``serializers.py`` file and assign them to the serializers.


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

You can now run the server with the following command:

.. code-block:: python

    python manage.py grpcrunaioserver --dev

The server is now running on port `50051` by default.
