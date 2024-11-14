Enumerations
============

Description
-----------

DSG can handle the generation of enumerations in your `.proto` files in three ways:

- Using a Serializer or Model field with TextChoices (limited features)
- Using an Annotated Serializer or Model field (all features)
- Using FieldDict in the `grpc_action` decorator (all features)

Unless you are using enums in a FieldDict directly, you should be using `TextChoices` or `IntegerChoices` as defined in the Django documentation `here <https://docs.djangoproject.com/en/5.1/ref/models/fields/#enumeration-types>`_.

Using a Serializer or Model field with TextChoices
--------------------------------------------------

This method is limited to the use of `TextChoices` in Django models or serializers and only include a subset of the features, but it is the simplest way to generate an enum.

For this to work your TextChoices need to be defined with key-like members in the first value of the tuple (letters all in uppercase, numbers allowed after the first letter, and underscore character).

This works :

.. code-block:: python

    class MyModel(models.Model):
        class MyEnum(models.TextChoices):
            VALUE_1 = "VALUE_1", "Value 1"
            #          ^^^^^^^  This will be the first key of the enum
            VALUE_2 = "VALUE_2", "Value 2"

        my_field = models.CharField(choices=MyEnum.choices)

Here is the generated enum in .proto file:

.. code-block:: protobuf

    message Request {
        MyEnum.Enum my_field = 1;
    }

    message MyEnum {
        enum Enum {
            ENUM_UNSPECIFIED = 0;
            VALUE_1 = 1;
            VALUE_2 = 2;
        }
    }

This doesn't work and will be generated as a string field:

.. code-block:: python

    class MyModel(models.Model):
        class MyEnum(models.TextChoices):
            VALUE_1 = "Value1", "Value 1"
            VALUE_2 = "VALUE 2", "Value 2"

        my_field = models.CharField(choices=MyEnum.choices)

Here is the generated .proto file:

.. code-block:: protobuf

    message Request {
        string my_field = 1;
    }

Using an Annotated Serializer or Model field
--------------------------------------------

If you want to use choices in a Serializer or Model, you can use `TextChoices` or `IntegerChoices` and use `Annotated` to specify the choices you use as metadata.

DSG is not able to directly access the Enum in the field as it is normalized as a tuple missing the keys; that's why we use `Annotated`.

By using this method the keys of the Enum will be used to build the Enum in the `.proto` file.

Example in a model:

.. code-block:: python

    from typing import Annotated

    class MyModel(models.Model):
        class MyEnum(models.TextChoices):
            VALUE_1 = "VALUE_1", "Value 1"
            #^^^^^^  This will be the first key of the enum
            VALUE_2 = "VALUE_2", "Value 2"

        my_field: Annotated[models.CharField, MyEnum] = models.CharField(choices=MyEnum)

Example in a Serializer:

.. code-block:: python

    from typing import Annotated

    class MySerializer(proto_serializers.ProtoSerializer):
        class MyEnum(models.TextChoices):
            VALUE_1 = "VALUE_1", "Value 1"
            VALUE_2 = "VALUE_2", "Value 2"

        my_field: Annotated[serializers.ChoiceField, MyEnum] = serializers.ChoiceField(choices=MyEnum)

Here is the generated enum in `.proto` file:

.. code-block:: protobuf

    message Request {
        MyEnum.Enum my_field = 1;
    }

    message MyEnum {
        enum Enum {
            ENUM_UNSPECIFIED = 0;
            VALUE_1 = 1;
            VALUE_2 = 2;
        }
    }

Note that if you use a `ModelProtoSerializer`, and your model has `Annotated` on fields containing choices, you don't have to annotate them again in the serializer.

Using a FieldDict
-----------------

In a FieldDict, you can specify an Enum for the type. This will generate the corresponding enum in the `.proto` file.

.. code-block:: python

    @grpc_action(
        request=[{"name": "enum_example", "type": MyEnum}],
        response=[{"name": "value", "type": "string"}],
    )

Here is the generated enum in `.proto` file:

.. code-block:: protobuf

    message Request {
        MyEnum.Enum enum_example = 1;
    }

    message MyEnum {
        enum Enum {
            ENUM_UNSPECIFIED = 0;
            VALUE_1 = 1;
            VALUE_2 = 2;
        }
    }

Adding Comments
---------------

.. warning::

    This feature is only available when using `Annotated` in a Serializer or Model field, or when using a FieldDict in the `grpc_action` decorator.


You can add comments at the enumeration level by adding a Docstring to it, or at the members level by adding Annotated to them.

.. code-block:: python

    from typing import Annotated

    class MyModel(models.Model):
        class MyEnum(models.TextChoices):
            """My enum comment"""

            VALUE_1 : Annotated[tuple, ["Comment", "on two lines"]] = "VALUE_1", "Value 1"
            VALUE_2 : Annotated[tuple, "Comment on one line"] = "VALUE_2", "Value 2"

        my_field: Annotated[models.CharField, MyEnum] = models.CharField(choices=MyEnum)

Here is the generated enum in `.proto` file:

.. code-block:: protobuf

    // My enum comment
    message MyEnum {
        enum Enum {
            ENUM_UNSPECIFIED = 0;
            // Comment
            // on two lines
            VALUE_1 = 1;
            // Comment on one line
            VALUE_2 = 2;
        }
    }

Modify how Enums are generated using generation plugins
-------------------------------------------------------

.. note::

    In protobuf, enums work similarly to C++, meaning that enum members are siblings of their type, preventing the creation of two enums with the same member names. **Most of the time you want to encapsulate your enums in a message.**

There are currently four ways the Enums can be written to the .proto file:

- GlobalScopeEnumGenerationPlugin : In the global scope
- GlobalScopeWrappedEnumGenerationPlugin : In the global scope, wrapped in a message (default)
- InMessageEnumGenerationPlugin : In the message scope
- InMessageWrappedEnumGenerationPlugin : In the message scope, wrapped in a message

Theses options can be set by using the appropriate generation plugin.

Using Generated Enums
---------------------

When generated, the enums are accessible from your `pb2` files.

The location where they are generated is based the generation plugin you are using.

For exemple if you are using the GlobalScopeWrappedEnumGenerationPlugin :

.. code-block:: python

    myapp_pb2.MyEnum.Enum.VALUE_1
    myapp_pb2.MyEnum.Enum.VALUE_2

Using the GlobalScopeEnumGenerationPlugin :

.. code-block:: python

    myapp_pb2.MyEnum.VALUE_1
    myapp_pb2.MyEnum.VALUE_2

Using the InMessageEnumGenerationPlugin :

.. code-block:: python

    myapp_pb2.MyMessage.MyEnum.VALUE_1
    myapp_pb2.MyMessage.MyEnum.VALUE_2

Using the InMessageWrappedEnumGenerationPlugin :

.. code-block:: python

    myapp_pb2.MyMessage.MyEnum.Enum.VALUE_1
    myapp_pb2.MyMessage.MyEnum.Enum.VALUE_2
