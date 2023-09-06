.. _proto-generation:

Proto generation
================
To be able to generate proto files you need to register your service first. 
To do so please refer to `Service registration <https://socotecio.github.io/django-socio-grpc/server_and_service_register/#service-registration>`_ 

Description
-----------
Proto files contain the classes, descriptors and controller logic (``pb2.py`` files) and proto message syntax (``.proto`` file) necessary to run a grpc server.
In django-socio-grpc, proto files are generated from a ``ProtoSerializer`` class, 
this serializer class should be declared as either the request or response of a ``grpc_action``, or as a ``serializer_class`` attribute inside a registered service.
Fields contained in proto messages are mapped from the serializer fields.
In order to generate these files and its contents, there is a django command to run whenever you add or modify your serializers (or whenever you register a new service that uses an existing serializer)

Usage
-----
.. code-block:: bash

    python manage.py generateproto

Example
-------
Example serializer:

.. code-block:: python

    # quickstart/models.py
    from django.db import models 


    class User(models.Model):
        full_name = models.CharField(max_length=70)

        def __str__(self):
            return self.full_name

    # quickstart/serializers.py
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
    
    # Service
    from django_socio_grpc import generics
    from ..models import User
    from ..serializers import UserProtoSerializer


    class UserService(generics.AsyncModelService):
        queryset = User.objects.all()
        serializer_class = UserProtoSerializer

At the root of your project, run:

.. code-block:: bash

    python manage.py generateproto

If command executed successfully, you will see inside your user app, a grpc folder with two .py files, (``user_pb2.py`` and ``user_pb2_grpc.py``)
and a ``user.proto`` file. ``user.proto`` file should contain these lines:

.. code-block:: proto

    syntax = "proto3";

    package doc_example.generate_proto_doc;

    import "google/protobuf/empty.proto";

    service UserController {
        rpc List(UserListRequest) returns (UserListResponse) {}
        rpc Create(UserRequest) returns (UserResponse) {}
        rpc Retrieve(UserRetrieveRequest) returns (UserResponse) {}
        rpc Update(UserRequest) returns (UserResponse) {}
        rpc Destroy(UserDestroyRequest) returns (google.protobuf.Empty) {}
    }

    message UserResponse {
        string id = 1;
        string full_name = 2;
    }

    message UserListRequest {
    }

    message UserListResponse {
        repeated UserResponse results = 1;
    }

    message UserRequest {
        string id = 1;
        string full_name = 2;
    }

    message UserRetrieveRequest {
        string id = 1;
    }

    message UserDestroyRequest {
        string id = 1;
    }

Note: these files are meant for read only purposes, you can use the .proto file as a reference to verify wether
or not your serializer fields were correctly mapped but you should not try to modify them manually.