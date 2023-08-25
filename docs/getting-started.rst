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


Defining a gRPC Service
~~~~~~~~~~~~~~~~~~~~~~~
Django Socio gRPC uses the name Service instead of View or Viewset.
With the exception of the name and the internal layer, a gRPC service works in the same way as a generic DRF View.

Following the same logic as DRF, Django Socio gRPC uses class-based services.

Our example is based on the following models, serializers and services.
Please refer to the other chapters for more complex examples.

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

    #quickstarts/serializers
    from django_socio_grpc import proto_serializers

    class UserProtoSerializer(proto_serializers.ModelProtoSerializer):


    class PostProtoSerializer(proto_serializers.ModelProtoSerializer):

    class CommentProtoSerializer(proto_serializers.ModelProtoSerializer):





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



