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

    # It is a preferable option to import the pb2 response in this way because,
    # for the moment, django-socio-grpc does not dynamically detect the correct response
    # from the pb2 files to associate with the serializer.
    # If a response does not exist, it will raise an exception, and block the generation of proto files.
    # Catching the exception helps to solve this problem,
    # and allows django-socio-grpc to generate proto files normally.
    try:
        from quickstart.grpc.quickstart_pb2 import (
            UserResponse,
            UserListResponse,
            PostResponse,
            PostListResponse,
            CommentResponse,
            CommentListResponse
        )
        except ImportError:
            UserResponse = None
            UserListResponse = None
            PostResponse = None
            PostListResponse = None
            CommentResponse = None
            CommentListResponse = None


    class UserProtoSerializer(proto_serializers.ModelProtoSerializer):
        # This line is written here as an example,
        # but can be removed as the serializer integrates all the fields in the model
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

        pub_date = serializers.DateTimeField(read_only=True)
        content =  serializers.CharField()
        user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            pk_field=serializers.UUIDField(format="hex_verbose"),
        )
        post = serializers.PrimaryKeyRelatedField(
            queryset=Post.objects.all(),
            pk_field=serializers.UUIDField(format="hex_verbose"),
        )

        class Meta:
            model = Comment
            proto_class = CommentResponse
            proto_class_list = CommentListResponse
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


    class UserService(generics.AsyncBaseService):

        pagination_class = PageNumberPagination
        permission_classes = (BasePermission,)
        filter_backends = [DjangoFilterBackend]

        queryset = User.objects.all()
        serializer_class = UserProtoSerializer
    
    class PostService(generics.AsyncBaseService):
        queryset = Post.objects.all()
        serializer_class = PostProtoSerializer
    
    class CommentService(generics.AsyncBaseService):
        queryset = Comment.objects.all()
        serializer_class = CommentProtoSerializer

**Note:**

You have the flexibility to revert to using the classic APIVIEW class or to reuse mixins or base classes to adapt to your needs. 

Example:

  .. code-block:: python

    from django.contrib.auth.models import User
    from myapp.serializers import UserProtoSerializer
    from django_socio_grpc import generics

    class UserListService(generics.ListCreateAPIView):
            queryset = User.objects.all()
            serializer_class = UserProtoSerializer



Register services
~~~~~~~~~~~~~~~~~~~~~~~

This Handler will be the entrypoint for the service registration. 
Set its path as the ``ROOT_HANDLERS_HOOK`` of the ``GRPC_FRAMEWORK`` settings, 
please refer to :ref:`Available Settings <Available Settings>` part of this documentation.

  .. code-block:: python

    # quickstart/handlers.py
    from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
    from quickstart.services import UserService, PostService, CommentService,


    def grpc_handlers(server):
        app_registry = AppHandlerRegistry("quickstart", server)
        app_registry.register(UserService)
        app_registry.register(PostService)
        app_registry.register(CommentService)


Generate the protofile and the client associated to the model
~~~~~~~~~~~~~~~~~~

This command will generate a folder called ``grpc`` at the root of your Django app. It contains the three files needed to generate the services: 

    * quickstart_pb2_grpc.py
    * quickstart_pb2.py
    * quickstart.proto


.. code-block:: python
    
    python manage.py generateproto



Running the Server
~~~~~~~~~~~~~~~~~~

.. code-block:: python
    
    python manage.py grpcrunaioserver --dev

