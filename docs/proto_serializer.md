## Proto Serializer


Proto Serializer works exctly the same as [DRF serializer](https://www.django-rest-framework.org/api-guide/serializers/). You juste have to inherit from a different class (see mapping under) and add two meta attr `proto_class` and `proto_class_list`.

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
        proto_class_list = quickstart_pb2.QuestionListResponse
        fields = ["id", "question_text", "pub_date"]
```

### proto_class and proto_class_list

`proto_class` and `proto_class_list` will be used to convert incoming grpc message or python data into grpc messages.

`proto_class_list` is used when the param `many=True` is passed to the serializer. It allow us to have 2 differents proto messages with the same models for list and retrieve methods in a ModelService

If the message received in request is different than the one used in response then you will have to create 2 serializers.

### serializer.data vs serializer.message

Django Socio gRPC support retro compatibility so `serializer.data` is still accessible and still in dictionnary format. However, it's recommended to use `serializer.message` that is in the gRPC message format and should always return `serializer.message` as response data.


### Tips for converting UUID Field

If you use UUID you can came accross problem as this type is not automatically converted in string format when used as Foreign Key.
To fix this please use [pk_field](https://www.django-rest-framework.org/api-guide/relations/#primarykeyrelatedfield):

```python
related_object = serializers.PrimaryKeyRelatedField(
    queryset=Something.objects.all(),
    pk_field=UUIDField(format="hex_verbose"),
)
```