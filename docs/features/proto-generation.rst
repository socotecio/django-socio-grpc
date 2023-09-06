.. _proto-generation:

Proto generation
================
To be able to generate proto files you need to register your service first. 
To do so please refer to :ref:`getting started <getting_started>` at section service registration

Description
-----------
Proto files contain the classes, descriptors and controller logic (``pb2.py`` files) and proto message syntax (``.proto`` file) necessary to run a grpc server.
In django-socio-grpc, proto files are generated from a ``grpc_action`` request / response contents (see :ref:`grpc action <grpc_action>`).


You can also generate proto files from a service that has a ``serializer_class`` attribute (mapped to a ``ProtoSerializer`` class) and inherits from a mixin that automatically generates grpc_actions


In order to generate these files and its contents, there is a django command to run whenever you add a ``grpc_action`` or modify your request / response

Usage
-----
.. code-block:: bash

    python manage.py generateproto

Example
-------

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
    from django_socio_grpc.decorators import grpc_action
    from ..models import User
    from ..serializers import UserProtoSerializer

    # inherits from AsyncModelService, therefore will register all default CRUD actions.
    class UserService(generics.AsyncModelService):
        queryset = User.objects.all()
        serializer_class = UserProtoSerializer

        @grpc_action
        async def SomeCustomMethod(
            request=[{"name": "foo", "type": "string"}],
            response=[{"name": "bar", "type": "string"}]
        ):  
            # logic here
            pass

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
        rpc SomeCustomMethod(SomeCustomMethodRequest) returns (SomeCustomMethodResponse) {}
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

    message SomeCustomMethodRequest {
        string foo = 1;
    }

    message SomeCustomMethodResponse {
        string bar = 1;
    }


Note: these files are meant for read only purposes, you can use the .proto file as a reference to verify wether
or not your serializer fields were correctly mapped but you should not try to modify them manually.