Enumerations
============

Description
-----------

DSG can handle the generation of enumerations in your `.proto` files in two ways:

- Using an Annotated Serializer or Model field, with choices
- Using FieldDict in the `grpc_action` decorator

Unless you are using enums in a FieldDict directly, you should be using `TextChoices` or `IntegerChoices` as defined in the Django documentation `here <https://docs.djangoproject.com/en/5.1/ref/models/fields/#enumeration-types>`_.

Using a FieldDict
-----------------

In a FieldDict, you can specify an Enum for the type. This will generate the corresponding enum in the `.proto` file.

.. code-block:: python

    @grpc_action(
        request=[{"name": "enum_example", "type": MyEnum}],
        response=[{"name": "value", "type": "string"}],
    )

Using an Annotated Serializer or Model field
--------------------------------------------

If you want to use choices in a Serializer or Model, you can use `TextChoices` or `IntegerChoices` and use `Annotated` to specify the choices you use as metadata.

DSG is not able to directly access the choices in the field as they are normalized as a tuple missing the keys; that's why we use `Annotated`.

.. warning::

    If you don't use `Annotated`, no enum will be generated in the `.proto` file; instead, your field will simply be a string or int32 type.

Example in a model:

.. code-block:: python

    from typing import Annotated

    class MyModel(models.Model):
        class MyEnum(models.TextChoices):
            FIRST = "FIRST", "First"
            SECOND = "SECOND", "Second"

        my_field: Annotated[models.CharField, MyEnum] = models.CharField(choices=MyEnum)

Example in a Serializer:

.. code-block:: python
    
    from typing import Annotated

    class MySerializer(proto_serializers.ProtoSerializer):
        class MyEnum(models.TextChoices):
            FIRST = "FIRST", "First"
            SECOND = "SECOND", "Second"

        my_field: Annotated[serializers.ChoiceField, MyEnum] = serializers.ChoiceField(choices=MyEnum)

Note that if you use a `ModelProtoSerializer`, and your model has `Annotated` on fields containing choices, you don't have to annotate them again in the serializer.

Using Generated Enums
---------------------

When generated, the enums are accessible from your `pb2` files.

.. code-block:: python

    myapp_pb2.MyEnum.Enum.FIRST
    myapp_pb2.MyEnum.Enum.SECOND

.. note::

    The reason the syntax is `NameOfYourEnum.Enum` is that the enum is actually encapsulated in a message. In protobuf, enums work similarly to C++, meaning that enum members are siblings of their type, preventing the creation of two enums with the same member names.
