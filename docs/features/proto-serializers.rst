.. _proto-serializers:

Proto Serializers
=================

Proto Serializer works exactly the same as `DRF serializer <https://www.django-rest-framework.org/api-guide/serializers/>`_. You just have to inherit from a different class (see mapping below) and add two meta attributes `proto_class` and `proto_class_list`.

Mapping between Django REST Framework and Django Socio gRPC
----------------------------------------------------------

.. list-table:: DRF to DSG Class Mapping
   :widths: 50 50
   :header-rows: 1

   * - DRF Class
     - DSG class
   * - ``rest_framework.serializers.BaseSerializer``
     - ``django_socio_grpc.proto_serializers.BaseProtoSerializer``
   * - ``rest_framework.serializers.Serializer``
     - ``django_socio_grpc.proto_serializers.ProtoSerializer``
   * - ``rest_framework.serializers.ListSerializer``
     - ``django_socio_grpc.proto_serializers.ListProtoSerializer``
   * - ``rest_framework.serializers.ModelSerializer``
     - ``django_socio_grpc.proto_serializers.ModelProtoSerializer``

Example with ModelProtoSerializer
---------------------------------

Example will only focus on ModelProtoSerializer.

First, we will use our `Post` model used in the :ref:`Getting started<getting_started>`

.. code-block:: python

    class Post(models.Model):
        pub_date = models.DateField()
        headline = models.CharField(max_length=200)
        content = models.TextField()
        user = models.ForeignKey(User, on_delete=models.CASCADE)

Then we generate the proto file for this model. See :ref:`Proto Gneration <proto-generation>`_ for more information. Be sure you completed all the step before the :ref:`Generate proto quickstart step <quickstart-generate-proto>`

You can now define your serializer like this:

.. code-block:: python

    #quickstart/serializers.py
    from django_socio_grpc import proto_serializers
    from rest_framework import serializers
    from quickstart.models import Post

    from quickstart.grpc.quickstart_pb2 import (
        PostResponse,
        PostListResponse,
    )

    class PostProtoSerializer(proto_serializers.ModelProtoSerializer):
        pub_date = serializers.DateTimeField(read_only=True)
        user = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all(),
            pk_field=serializers.UUIDField(format="hex_verbose"),
        )

        class Meta:
            model = Post
            proto_class = PostResponse
            proto_class_list = PostListResponse
            fields = "__all__"
            

proto_class and proto_class_list
--------------------------------

`proto_class` and `proto_class_list` will be used to convert incoming gRPC messages or Python data into gRPC messages.

`proto_class_list` is used when the parameter `many=True` is passed to the serializer. It allows us to have two different proto messages with the same models for list and retrieve methods in a ModelService.

If the message received in the request is different than the one used in the response, then you will have to create two serializers.

serializer.data vs serializer.message
-------------------------------------

Django Socio gRPC supports retro compatibility, so `serializer.data` is still accessible and still in dictionary format. However, it's recommended to use `serializer.message` that is in the gRPC message format and should always return `serializer.message` as response data.

Note that async method serializer.adata vs serializer.amessage exist. See :ref:`Sync vs Async page <TODO>`

Extra kwargs options
--------------------

Extra kwargs options are used like this: ``serializer_instance = SerializerClass(**extra_kwras_options)``

- ``stream <Boolean>``: return the message as a list of proto_class instead of an instance of proto_class_list to be used in stream. See `Stream example <https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/mixins.py#L136>`_

- ``message_list_attr <String>``: change the attribute name for the list of instances returned by a proto_class_list (default is results). See :ref:`Customizing the Name of the Field in the ListResponse <customizing-the-name-of-the-field-in-the-listresponse>`

- ``proto_comment <ProtoComment or string>``: add to the model (message) comment in the output PROTO file. `ProtoComment` class is declared in `django_socio_grpc.protobuf` and helps to have multi-line comments.  See :ref:`Add comments to fields <adding-comments-to-fields>`


Use Cases
---------

=============================================
Converting PrimaryKeyRelatedField UUID Field
=============================================

If you use UUID, you can come across a problem as this type is not automatically converted into string format when used as a Foreign Key.
To fix this, please use `pk_field <https://www.django-rest-framework.org/api-guide/relations/#primarykeyrelatedfield>`_:

.. code-block:: python

    related_object = serializers.PrimaryKeyRelatedField(
        queryset=Something.objects.all(),
        pk_field=UUIDField(format="hex_verbose"),
    )

=========================================
Converting empty string to None
=========================================

As gRPC always sends the default value for the type if not sent, some behaviors of DRF, like handling differently None value and empty string, are not working.
You can design your own system by adding arguments to adapt the behavior, but if you have a field where an empty string means None, as for Datetime, for example, you can use code like this:

.. code-block:: python

    from django_socio_grpc import proto_serializers
    from rest_framework.fields import DateTimeField
    from django.core.exceptions import ObjectDoesNotExist

    class NullableDatetimeField(DateTimeField):
        def to_internal_value(self, value):
            if not value:
                return None
            return super().to_internal_value()

    class ExampleProtoSerializer(proto_serializers.ModelProtoSerializer):
        example_datetime = NullableDatetimeField(validators=[])

        class Meta:
            model = Example
            proto_class = example_pb2.Example
            proto_class_list = example_pb2.ExampleListResponse
            fields = "__all__"


==============================
Read-Only and Write-Only Props
==============================

If the setting `SEPARATE_READ_WRITE_MODEL` is `True`, Django Socio gRPC will automatically use `read_only` and `write_only` field kwargs to generate fields only in the request or response message. This is also true for Django fields with specific values (e.g., `editable=False`).

Example:

.. code-block:: python

    class BasicServiceSerializer(proto_serializers.ProtoSerializer):

        user_name = serializers.CharField(read_only=True)
        email = serializers.CharField()
        password = serializers.CharField(write_only=True)

        class Meta:
            fields = ["user_name", "email", "password"]

Generated Message:

.. code-block:: proto

    message BasicServiceRequest {
        string user_name = 1;
        string password = 2;
    }

    message BasicServiceResponse {
        string user_name = 1;
        string email = 2;
    }

=================
Nested Serializer
=================

Django Socio gRPC supports nested serializers without any extra work. Just try it.

.. code-block:: python

    class RelatedFieldModelSerializer(proto_serializers.ModelProtoSerializer):
        foreign_obj = ForeignModelSerializer(read_only=True)
        many_many_obj = ManyManyModelSerializer(read_only=True, many=True)

        class Meta:
            model = RelatedFieldModel
            fields = ["uuid", "foreign_obj", "many_many_obj"]

Generated Proto:

.. code-block:: proto

    message RelatedFieldModelResponse {
        string uuid = 1;
        ForeignModelResponse foreign_obj = 2;
        repeated ManyManyModelResponse many_many_obj = 3;
    }

====================================
Special Case of BaseProtoSerializer
====================================

As `BaseProtoSerializer` doesn't have fields but only `to_representation` and `to_internal_value`, we can't automatically introspect code to find the correct proto type.

To address this issue, you have to manually declare the name and protobuf type of the `BaseProtoSerializer` in a `to_proto_message` method.

This `to_proto_message` needs to return a list of dictionaries in the same format as :ref:`grpc action <grpc_action>` request or response as a list input.

.. code-block:: python

    class BaseProtoExampleSerializer(proto_serializers.BaseProtoSerializer):
        def to_representation(self, el):
            return {
                "uuid": str(el.uuid),
                "number_of_elements": el.number_of_elements,
                "is_archived": el.is_archived,
            }

        def to_proto_message(self):
            return [
                {"name": "uuid", "type": "string"},
                {"name": "number_of_elements", "type": "int32"},
                {"name": "is_archived", "type": "bool"},
            ]

Generated Proto:

.. code-block:: proto

    message BaseProtoExampleResponse {
        string uuid = 1;
        int32 number_of_elements = 2;
        bool is_archived = 3;
    }


=====================================
Special Case of SerializerMethodField
=====================================

DRF ``SerializerMethodField`` class is a field type that returns the result of a method. So there is no possibility to automatically find the type of this field. To circumvent this problem, Django Socio gRPC introduces function introspection where we are looking for return annotation in the method to find the prototype.

.. code-block:: python

    from typing import List, Dict

    class ExampleSerializer(proto_serializers.ProtoSerializer):

        default_method_field = serializers.SerializerMethodField()
        custom_method_field = serializers.SerializerMethodField(method_name="custom_method")

        def get_default_method_field(self, obj) -> int:
            return 3

        def custom_method(self, obj) -> List[Dict]:
            return [{"test": "test"}]

        class Meta:
            fields = ["default_method_field", "custom_method_field"]

Generated Proto:

.. code-block:: proto

    message ExampleResponse {
        int32 default_method_field = 2;
        repeated google.protobuf.Struct custom_method_field = 3;
    }


.. _customizing-the-name-of-the-field-in-the-listresponse:
=====================================================
Customizing the Name of the Field in the ListResponse
=====================================================

By default, the name of the field used for the list response is `results`. You can override it in the meta of your serializer:

.. code-block:: python

    class ExampleSerializer(proto_serializers.ProtoSerializer):

        uuid = serializers.CharField()
        name = serializers.CharField()

        class Meta:
            message_list_attr = "list_custom_field_name"
            fields = ["uuid", "name"]

Generated Proto:

.. code-block:: proto

    message ExampleResponse {
        string uuid = 1;
        string name = 2;
    }

    message ExampleListResponse {
        repeated ExampleResponse list_custom_field_name = 1;
        int32 count = 2;
    }

.. _adding-comments-to-fields:
========================
Adding Comments to Fields
========================

You could specify comments for fields in your model (proto message) via `help_text` attribute and `django_socio_grpc.utils.tools.ProtoComment` class:

.. code-block:: python

    class ExampleSerializer(proto_serializers.ProtoSerializer):

        name = serializers.CharField(help_text=ProtoComment(["Comment for the name field"]))
        value = serializers.CharField(help_text=ProtoComment(["Multiline comment", "for the value field"]))

        class Meta:
            fields = ["name", "value"]

Generated Proto:

.. code-block:: proto

    message ExampleResponse {
        // Comment for the name field
        string name = 1;
        // Multiline comment
        // for the value field
        string value = 2;
    }