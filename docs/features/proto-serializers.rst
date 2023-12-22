.. _proto-serializers:

Proto Serializers
=================

Proto Serializers are used to convert Django database data into protobuf messages that can be sent via gRPC and vice versa.

There are four types of proto serializers available:

- :ref:`BaseProtoSerializer <proto-serializers-base-proto-serializer>` : Base class for all proto serializers
- :ref:`ProtoSerializer <proto-serializers-proto-serializer>` : Same as ``BaseProtoSerializer`` but inherit from `DRF Serializer class <https://www.django-rest-framework.org/api-guide/serializers/#serializers>`_
- :ref:`ListProtoSerializer <proto-serializers-list-proto-serializer>` : Base class for all proto serializers that use DRF fields and have kwargs ``many=True``
- :ref:`ModelProtoSerializer <proto-serializers-model-proto-serializer>` : Class that allow to generate serializer field from ``Model`` fields


They work exactly in the same way as `DRF serializer <https://www.django-rest-framework.org/api-guide/serializers/>`_. You just have to inherit from a the corresponding DSG class (see mapping below) and add two meta attributes ``proto_class`` and ``proto_class_list`` (s. examples).

Mapping between DRF and DSG
---------------------------

.. list-table:: DRF to DSG Class Mapping
   :widths: 50 50
   :header-rows: 1

   * - DRF Class
     - DSG class
   * - ``rest_framework.serializers.BaseSerializer``
     - :func:`django_socio_grpc.proto_serializers.BaseProtoSerializer`
   * - ``rest_framework.serializers.Serializer``
     - :func:`django_socio_grpc.proto_serializers.ProtoSerializer`
   * - ``rest_framework.serializers.ListSerializer``
     - :func:`django_socio_grpc.proto_serializers.ListProtoSerializer`
   * - ``rest_framework.serializers.ModelSerializer``
     - :func:`django_socio_grpc.proto_serializers.ModelProtoSerializer`

.. _proto-serializers-base-proto-serializer:

BaseProtoSerializer
-------------------

BaseProtoSerializer is the base class for all proto serializers. It doesn't have any fields and is used to convert data into a gRPC message.

It needs to define the method *to_proto_message* to be able to correctly generate proto file. See :ref:`Proto generation <proto-generation>` for generation and :ref:`Request/Response format of grpc_action<grpc-action-request-response>` for expected return format.


.. code-block:: python

    from django_socio_grpc import proto_serializers

    class BaseProtoSerializer(proto_serializers.BaseProtoSerializer):
        def to_representation(self, el):
            return {
                "uuid": str(el.uuid),
                "number_of_elements": el.number_of_elements,
                "is_archived": el.is_archived,
            }

        def to_internal_value(self, data):
            return {
                "uuid": UUID(data["uuid"]),
                "number_of_elements": data["number_of_elements"],
                "is_archived": data["is_archived"],
            }

        def to_proto_message(self):
            return [
                {"name": "uuid", "type": "string"},
                {"name": "number_of_elements", "type": "int32"},
                {"name": "is_archived", "type": "bool"},
            ]

.. _proto-serializers-proto-serializer:

ProtoSerializer
---------------

``ProtoSerializer`` is the same as ``BaseProtoSerializer`` except it inherit from ``rest_framework.Serializer`` instead of ``rest_framework.BaseSerializer``.

You can find more information on the `DRF documentation <https://www.django-rest-framework.org/api-guide/serializers/#baseserializer>`_

It also need to define the method to_proto_message to be able to correctly generate proto file. See :ref:`Proto generation <proto-generation>` for generation and :ref:`Request/Response format of grpc_action<grpc-action-request-response>` for expected return format.

.. _proto-serializers-list-proto-serializer:

ListProtoSerializer
-------------------

The ListProtoSerializer class provides the behavior for serializing and validating multiple objects at once. 
You won't typically need to use ListProtoSerializer directly, 
but should instead simply pass ``many=True`` when instantiating a serializer.

When a serializer is instantiated and ``many=True`` is passed, a ``ListSerializer`` instance will be created. 
The serializer class then becomes a child of the parent ListSerializer

The following argument can also be passed to a ListSerializer field or a serializer that is passed ``many=True``:

``allow_empty``: This is ``True`` by default, but can be set to False if you want to disallow empty lists as valid input.

``max_length``: This is ``None`` by default, but can be set to a positive integer if you want to validate that the list contains no more than this number of elements.

``min_length``: This is ``None`` by default, but can be set to a positive integer if you want to validate that the list contains no fewer than this number of elements.

.. _proto-serializers-model-proto-serializer:

ModelProtoSerializer
--------------------

Often you'll want serializer classes that map closely to **Django model** definitions.

The ``ModelProtoSerialize`` class provides a shortcut that lets you automatically create a Serializer class with fields that correspond to the Model fields.

The ``ModelProtoSerialize`` class is the same as a regular Serializer class, except that:

 - It will automatically generate a set of fields for you, based on the model.
 - It will automatically generate validators for the serializer, such as unique_together validators.
 - It includes simple default implementations of .create() and .update().


Example of a ModelProtoSerializer
-----------------------------------

This Example will only focus on ``ModelProtoSerializer``.

First, we will use our ``Post`` model used in the :ref:`Getting started<getting-started-defining-models>`.

.. code-block:: python

    class Post(models.Model):
        pub_date = models.DateField()
        headline = models.CharField(max_length=200)
        content = models.TextField()
        user = models.ForeignKey(User, on_delete=models.CASCADE)

Then we generate the proto file for this model. See :ref:`Proto Generation<proto-generation>` for more information. Be sure you completed all the step before the :ref:`Generate proto quickstart step <quickstart-generate-proto>`

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

``proto_class`` and ``proto_class_list`` will be used to convert incoming gRPC messages or Python data into gRPC messages.

``proto_class_list`` is used when the parameter ``many=True`` is passed to the serializer. 
It allows us to have two different proto messages with the same models for list and retrieve methods in a ModelService.

**If the message received in the request is different than the one used in the response, then you will have to create two serializers.**

serializer.data vs serializer.message
-------------------------------------

DSG supports retro compatibility, so ``serializer.data`` is still accessible and still in dictionary format. 
However, it's recommended to use ``serializer.message`` that is in the gRPC message format and should always return ``serializer.message`` as response data.

Note that async method ``serializer.adata`` and ``serializer.amessage`` exist. See :ref:`Sync vs Async page <sync-vs-async>`

.. _proto-serializer-extra-kwargs-options:

Extra kwargs options
--------------------

Extra kwargs options are used like this: ``serializer_instance = SerializerClass(**extra_kwras_options)``

- ``stream <Boolean>``: Return the message as a list of proto_class instead of an instance of proto_class_list to be used in stream. See `Stream example <https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/mixins.py#L136>`_

- ``message_list_attr <String>``: Change the attribute name for the list of instances returned by a proto_class_list (default is results). See :ref:`Customizing the Name of the Field in the ListResponse <customizing-the-name-of-the-field-in-the-listresponse>`

- ``proto_comment <ProtoComment or string>``: Add to the model (message) comment in the output PROTO file. ``ProtoComment`` class is declared in ``django_socio_grpc.protobuf`` and helps to have multi-line comments. See :ref:`Add comments to fields <adding-comments-to-fields>`


Use Cases
---------

=============================================
Converting PrimaryKeyRelatedField UUID Field
=============================================

If you use UUIDs as **primary key** you can come across a problem as this type is not automatically converted into string format when used as a Foreign Key.
To fix this, please use `pk_field arg of PrimaryKeyRelatedField <https://www.django-rest-framework.org/api-guide/relations/#primarykeyrelatedfield>`_  :


Example:

.. code-block:: python
    :emphasize-lines: 9

    # serializers.py
    from django_socio_grpc import proto_serializers
    from rest_framework.serializers import UUIDField, PrimaryKeyRelatedField

    # related_object is a UUIDField of a related object
    class ExampleProtoSerializer(proto_serializers.ModelProtoSerializer):
        related_object = PrimaryKeyRelatedField(
            queryset=Something.objects.all(),
            pk_field=UUIDField(format="hex_verbose"),
        )
        class Meta:
            model = MyModel
            proto_class = my_model_pb2.ExampleResponse

            proto_class_list = my_model_pb2.ExampleListResponse

            fields = "__all__"

.. _proto-serializers-nullable-fields:

===========================
Nullable fieds (`optional`)
===========================

In gRPC, all fields have a default value. For example, if you have a field of type `int32` and you don't set a value, the default value will be `0`.
To know if this field was set (so its value is actually `0`) or not, the field needs to be declared as `optional`
(see `proto3 <https://protobuf.dev/programming-guides/proto3/#field-labels>`_ documentation).

.. warning::

    There is no way to differentiate between a field that was not set and a field that was set to `None`.
    Therefore ``{}`` and ``{"field": None}`` will be converted to the same gRPC message.
    By default, we decided to interpret no presence of a field as ``None`` to have an intuitive way to use nullable fields which
    are extensively used in Django (``null=True``) and DRF (``allow_null=True``) options.
    This behavior has an unintended consequence with default values in ``ModelProtoSerializer``, because
    the value will be `None` instead of being absent.
    There is an `open issue <https://github.com/socotecio/django-socio-grpc/issues/171>`_ on the subject, with a workaround.

There are multiple ways to have proto fields with ``optional``:

- In ``ProtoSerializer``, you can use ``allow_null=True`` in the field kwargs.
- In ``SerializerMethodField``, you can use the return annotation ``Optional[...]`` or ``... | None`` for Python 3.10+.
- In ``ModelProtoSerializer``, model fields with ``null=True`` will be converted to ``optional`` fields.
- In ``GRPCAction`` you can set ``cardinality`` to ``optional`` in the `request` or `response` :func:`FieldDict <django_socio_grpc.protobuf.typing.FieldDict>`.

==============================
Read-Only and Write-Only Props
==============================


If the setting `SEPARATE_READ_WRITE_MODEL` is `True`, DSG will automatically use `read_only` and `write_only` field kwargs to generate fields only in the request or response message. This is also true for Django fields with specific values (e.g., ``editable=False``).

.. warning::
    This setting is deprecated. See :ref:`setting documentation<grpc-settings-separate-read-write-model>` 


Example:

.. code-block:: python

    from django_socio_grpc import proto_serializers

    class BasicLoginServiceSerializer(proto_serializers.ProtoSerializer):

        user_name = serializers.CharField(read_only=True)
        email = serializers.CharField()
        password = serializers.CharField(write_only=True)

        class Meta:
            fields = ["user_name", "email", "password"]

Will result in the following proto after generation:

.. code-block:: proto

    message BasicLoginServiceRequest {
        string user_name = 1;
        string password = 2;
    }

    message BasicLoginServiceResponse {
        string user_name = 1;
        string email = 2;
    }

=================
Nested Serializer
=================

DSG supports **nested serializers** without any extra work. Just try it.

You can see full example of it in `our app <https://github.com/socotecio/django-socio-grpc/tree/master/django_socio_grpc/tests/fakeapp>`_ used for unit testing DSG. Extract from it:

.. code-block:: python

    from django_socio_grpc import proto_serializers

    class ExampleRelatedFieldModelSerializer(proto_serializers.ModelProtoSerializer):
        
        # foreign_obj id the name of the foreign key in RelatedFieldModel and ForeignModelSerializer it's serializer. These are only example taken from unit test of DSG.
        foreign_obj = ForeignModelSerializer(read_only=True)
        # many_many_obj id the name of the many to many key in RelatedFieldModel and ManyManyModelSerializer it's serializer. These are only example taken from unit test of DSG.
        many_many_obj = ManyManyModelSerializer(read_only=True, many=True)

        class Meta:
            # RelatedFieldModel is the model that have foreign_obj and many_many_obj attributes
            model = RelatedFieldModel
            fields = ["uuid", "foreign_obj", "many_many_obj"]

Will result in the following proto after generation:

.. code-block:: proto

    message ExampleRelatedFieldModelResponse {
        string uuid = 1;
        ForeignModelResponse foreign_obj = 2;
        repeated ManyManyModelResponse many_many_obj = 3;
    }

====================================
Special Case of BaseProtoSerializer
====================================

As ``BaseProtoSerializer`` doesn't have fields but only ``to_representation`` and ``to_internal_value``, **we can't automatically introspect code to find the correct proto type**.

To address this issue, you have to **manually declare** the name and protobuf type of the ``BaseProtoSerializer`` in a ``to_proto_message`` method.

This ``to_proto_message`` needs to return a list of dictionaries in the same format as :ref:`grpc action <grpc_action>` request or response as a list input.

.. code-block:: python

    from django_socio_grpc import proto_serializers

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

DRF ``SerializerMethodField`` class is a field type that returns the result of a method. So there is no possibility to automatically find the type of this field. 
To circumvent this problem, DSG introduces function introspection where we are looking for return annotation in the method to find the prototype.

.. code-block:: python

    from typing import List, Dict
    from django_socio_grpc import proto_serializers
    from rest_framework import serializers

    class ExampleSerializer(proto_serializers.ProtoSerializer):

       :TODO: module "serializers" does not exist, please add the correct import

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

By default, the name of the field used for the list response is ``results``. You can override it in the meta of your serializer:

.. code-block:: python

    from django_socio_grpc import proto_serializers
    from rest_framework import serializers

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

=========================
Adding Comments to Fields
=========================

You could specify comments for fields in your model (proto message) via ``help_text`` attribute and :func:`django_socio_grpc.protobuf.ProtoComment` class:

.. code-block:: python

    from django_socio_grpc import proto_serializers
    from rest_framework import serializers
    from django_socio_grpc.protobuf import ProtoComment

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

===============================
Choosing cardinality of a field
===============================

Protobuf has different cardinality key words to specify behavior of a field such as ``optional`` or ``repeated``.

It's what's coming before the type of a field in a proto message:

.. code-block:: proto

    message MyMessage {
        // optional     \ is field cardinality
        // string       \ is field type
        // my_variable  \ is field name
        // 1 is field   \ position
        optional string my_variable = 1;
    }

See :func:`FieldCardinality<django_socio_grpc.protobuf.typing.FieldCardinality>` for exhaustive list of cardinality DSG support.

It is actually **not possible to specifically choose cardinality for a serializer field** for now. 
``optional`` cardinality is set following what is described :ref:`here<proto-serializers-nullable-fields>`.
``repeated`` cardinality is set when using ``ListField``, ``ListSerializer`` or ``Serializer`` with ``many=true`` argument.

We started discussions about adding more cardinality options and let field set them. You are welcome for contribution in this `issue <https://github.com/socotecio/django-socio-grpc/issues/219>`_.
