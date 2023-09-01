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

    #quickstart/models
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
For more extensive use, you can use all the DRF serializer methods: see the doc here 
.. _SO: https://www.django-rest-framework.org/api-guide/serializers/
 
  .. code-block:: python

    #quickstart/serializers
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
            PostListResponse
        )
        except ImportError:
            UserResponse = None
            UserListResponse = None
            PostResponse = None
            PostListResponse = None


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

Following the same logic as DRF, Django Socio gRPC uses class-based services.

Our example is based on the following models, serializers and services.
Please refer to the other chapters for more complex examples.







You have the flexibility to revert to using the classic APIVIEW class or to reuse mixins or base classes to adapt to your needs. 

Example:

  .. code-block:: python

    from django.contrib.auth.models import User
    from myapp.serializers import UserProtoSerializer
    from django_socio_grpc import generics

    class UserListService(generics.ListCreateAPIView):
            queryset = User.objects.all()
            serializer_class = UserProtoSerializer






Running the Server
~~~~~~~~~~~~~~~~~~



