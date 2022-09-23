## Proto Serializer


Proto Serializer works exactly the same as [DRF serializer](https://www.django-rest-framework.org/api-guide/serializers/). You juste have to inherit from a different class (see mapping under) and add two meta attr `proto_class` and `proto_class_list`.

### Mapping betwen Django REST Framework and Django Socio gRPC

| DRF Class | DSG class |
| --------- | --------- |
| rest_framework.serializers.BaseSerializer | django_socio_grpc.proto_serializers.BaseProtoSerializer |
| rest_framework.serializers.Serializer | django_socio_grpc.proto_serializers.ProtoSerializer |
| rest_framework.serializers.ListSerializer | django_socio_grpc.proto_serializers.ListProtoSerializer |
| rest_framework.serializers.ModelSerializer | django_socio_grpc.proto_serializers.ModelProtoSerializer |

### Example with ModelProtoSerializer

Example will only focus on ModelProtoSerializer.

First we will use again our Question model used in the quickstart:

```python
class Question(models.Model):
  question_text = models.CharField(max_length=200)
  pub_date = models.DateTimeField('date published')
```

Then we generate the proto file for this model. See [Generate Proto](https://socotecio.github.io/django-socio-grpc/#quickstart)

You can now define your serializer like this:
```python
# quickstart/serializers.py
from django_socio_grpc import proto_serializers
import quickstart.grpc.quickstart_pb2 as quickstart_pb2
from .models import Question


class QuestionProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = Question
        proto_class = quickstart_pb2.Question
        proto_comment = ProtoComment(["Multiline", "comment", "for", "message"])
        proto_class_list = quickstart_pb2.QuestionListResponse
        fields = ["id", "question_text", "pub_date"]
```

### proto_class and proto_class_list

`proto_class` and `proto_class_list` will be used to convert incoming grpc message or python data into grpc messages.

`proto_class_list` is used when the param `many=True` is passed to the serializer. It allow us to have 2 differents proto messages with the same models for list and retrieve methods in a ModelService

If the message received in request is different than the one used in response then you will have to create 2 serializers.

### serializer.data vs serializer.message

Django Socio gRPC support retro compatibility so `serializer.data` is still accessible and still in dictionnary format. However, it's recommended to use `serializer.message` that is in the gRPC message format and should always return `serializer.message` as response data.

### Extra kwargs options

Extra kwargs options are used like this: `serializer_instance = SerializerClass(**extra_kwras_options)`

- `stream <Boolean>`: return the message as a list of proto_class instead of an instance of proto_class_list to be used in stream. See [Stream exemple](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/mixins.py#L107)

- `message_list_attr <String>`: change the attribute name for the list of instance returned by a proto_class_list (default is results).

- `proto_comment <ProtoComment or string>`: add to model (message) comment in output PROTO file. `ProtoComment` class is declared in `django_socio_grpc.utils.tools` a helps to have multi-line comments.

### Tips for converting UUID Field

If you use UUID you can came accross problem as this type is not automatically converted in string format when used as Foreign Key.
To fix this please use [pk_field](https://www.django-rest-framework.org/api-guide/relations/#primarykeyrelatedfield):

```python
related_object = serializers.PrimaryKeyRelatedField(
    queryset=Something.objects.all(),
    pk_field=UUIDField(format="hex_verbose"),
)
```

### Tips for converting empty string to None

As gRPC always send the default value for type if not send some behavior of DRF like handling differently None value and empty string are not working.
You can design your own system by adding arguments to adapt the behavior but if you have field where empty string mean None as for Datetime for example you can use code like this:

```python
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
```
