Getting Started
===============

Quickstart Guide
----------------

Prerequisites
~~~~~~~~~~~~~

Installation
~~~~~~~~~~~~

Creating a New Project
~~~~~~~~~~~~~~~~~~~~~~

Adding a New App
~~~~~~~~~~~~~~~~

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

        def __str__(self):
            return self.full_name
    
    class Post(models.Model):
        pub_date = models.DateField()
        headline = models.CharField(max_length=200)
        content = models.TextField()
        user = models.ForeignKey(User, on_delete=models.CASCADE)
    
        def __str__(self):
            return self.headline 
    
    class Comment(models.Model):
        pub_date = models.DateField()
        content = models.TextField()
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        post = models.ForeignKey(Post, on_delete=models.CASCADE)
    
        def __str__(self):
            return self.pub_date 


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
        headline = serializers.CharField()
        content = serializers.CharField()
        user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            pk_field=serializers.UUIDField(format="hex_verbose"),
        )

        class Meta:
            model = Post
            fields = "__all__"

    class CommentProtoSerializer(proto_serializers.ModelProtoSerializer):

        class Meta:
            model = Comment
            fields = "__all__"


Defining gRPC services
~~~~~~~~~~~~~~~~~~~~~~~
Django Socio gRPC uses the name Service instead of View or Viewset.
With the exception of the name and the internal layer, a gRPC service works in the same way as a generic DRF View.

Django Socio gRPC Framework actually support both async and sync mode for gRPC.

You can refer to the part of the documentation describing the two types of method. In this example we are using an asynchronous service.

Following the same logic as DRF, Django Socio gRPC uses class-based services.

Here we implement pagination, permissions and filters by way of example.
You can write a mixin including these parameters and make an inheritance on the service class.
Please refer to the :ref:`Mixin section <Generic Mixins>` of this documentation to do this.

  .. code-block:: python

    #quickstart/services.py
    from django_filters.rest_framework import DjangoFilterBackend
    from rest_framework.pagination import PageNumberPagination
    from rest_framework.permissions import BasePermission
    from django_socio_grpc import generics

    from quickstart.models import User, Post, Comment
    from quickstart.serializer import UserProtoSerializer, PostProtoSerializer, CommentProtoSerializer


    class UserService(generics.AsyncModelService):
        pagination_class = PageNumberPagination
        permission_classes = (BasePermission,)
        filter_backends = [DjangoFilterBackend]

        queryset = User.objects.all()
        serializer_class = UserProtoSerializer
    
    class PostService(generics.AsyncModelService):
        queryset = Post.objects.all()
        serializer_class = PostProtoSerializer
    
    class CommentService(generics.AsyncModelService):
        queryset = Comment.objects.all()
        serializer_class = CommentProtoSerializer

**Note:**

You have the flexibility to revert to using the classic APIVIEW class or to reuse mixins or base classes to adapt to your needs. 

Example:

  .. code-block:: python

    from django.contrib.auth.models import User
    from quickstart.serializers import UserProtoSerializer
    from rest_framework import generics

    class UserListService(generics.ListCreateAPIView):
            queryset = User.objects.all()
            serializer_class = UserProtoSerializer



Register services
~~~~~~~~~~~~~~~~~~~~~~~

This Handler will be the entrypoint for the service registration. 
Set its path as the ``ROOT_HANDLERS_HOOK`` of the ``GRPC_FRAMEWORK`` settings:
  .. code-block:: python

    # tutorial/settings.py
    ...
    GRPC_FRAMEWORK = {
        "ROOT_HANDLERS_HOOK" : 'quickstart.handlers.grpc_handlers'


please refer to :ref:`Available Settings <Available Settings>` part of this documentation.

Note:

Create this file at the root of the project, here ``tutorial/`` 

  .. code-block:: python

    # tutorial/handlers.py
    from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
    from quickstart.services import UserService, PostService, CommentService,


    def grpc_handlers(server):
        app_registry = AppHandlerRegistry("quickstart", server)
        app_registry.register(UserService)
        app_registry.register(PostService)
        app_registry.register(CommentService)


Generate the app's Protobuf files and gRPC stubs
~~~~~~~~~~~~~~~~~~

This command will generate a folder called ``grpc`` at the root of your Django app. It contains the three files needed to generate the services: 

    * quickstart_pb2_grpc.py
    * quickstart_pb2.py
    * quickstart.proto


.. code-block:: python
    
    python manage.py generateproto


Assign newly generated classes
~~~~~~~~~~~~~~~~~~

In the ``grpc/quickstart.proto`` file, you can find the generation of the structure of responses and requests.
Their names are generated automatically.
The structure of the serializer response must be defined by assigning the format of the response class to the proto_class attribute and
the format for a list query to the proto_class_list attribute.

  .. code-block:: python

    #quickstart/serializers.py
    from django_socio_grpc import proto_serializers
    from rest_framework import serializers
    from quickstart.models import User, Post, Comment
    from quickstart.grpc.quickstart_pb2 import (
        UserResponse,
        UserListResponse,
        PostResponse,
        PostListResponse,
        CommentResponse,
        CommentListResponse
    )

    class UserProtoSerializer(proto_serializers.ModelProtoSerializer):
        full_name = serializers.CharField(allow_blank=True)
        class Meta:
            model = User
            proto_class = UserResponse
            proto_class_list = UserListResponse
            fields = "__all__"

    class PostProtoSerializer(proto_serializers.ModelProtoSerializer):
        pub_date = serializers.DateTimeField(read_only=True)
        headline = serializers.CharField()
        content = serializers.CharField()
        user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            pk_field=serializers.UUIDField(format="hex_verbose"),
        )

        class Meta:
            model = Post
            proto_class = PostResponse
            proto_class_list = PostListResponse
            fields = "__all__"

    class CommentProtoSerializer(proto_serializers.ModelProtoSerializer):
        class Meta:
            model = Comment
            proto_class = CommentResponse
            proto_class_list = CommentListResponse
            fields = "__all__"


Running the Server
~~~~~~~~~~~~~~~~~~

.. code-block:: python
    
    python manage.py grpcrunaioserver --dev

