# Django Socio gRPC Documentation

Learn how to use gRPC with Django like you usually code with Django Rest Framework.

## What is Django Socio gRPC

Django Socio gRPC is the implementation of how to do gRPC in a django web serveur in the Django Rest Framework way. This project is strongly inspired from [Django gRPC Framework](https://github.com/fengsp/django-grpc-framework) but add all the necessary features to be production ready such as pagination, filtering, async, authentification, ...
And some really cool helper as the protobuf generation from the model or the register helper.

## Quickstart

### Install dependencies

```bash
pip install django-socio-grpc
```

### Django setup

```bash
django-admin startproject tutorial
cd tutorial
django-admin startapp quickstart
python manage.py migrate
```

### Django settings

Add `django_socio_grpc` and you new `quickstart` app to INSTALLED_APPS, settings module is in tutorial/settings.py:

```python
INSTALLED_APPS = [
    ...
    'django_socio_grpc',
    'quickstart'
]
```

### Define a model

```python
# quickstart/models.py
from django.db import models


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
```

### Define a Serializer

```python
# quickstart/serializers.py
from django_socio_grpc import proto_serializers
from .models import Question


class QuestionProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = Question
        fields = ["id", "question_text", "pub_date"]

```

### Define a Service

```python
# quickstart/services.py
from django_socio_grpc import generics
from .models import Question
from .serializers import QuestionProtoSerializer


class QuestionService(generics.AsyncModelService):
    queryset = Question.objects.all()
    serializer_class = QuestionProtoSerializer

```

### Register the service

```python
# quickstart/handlers.py
from django_socio_grpc.utils.servicer_register import AppHandlerRegistry
from quickstart.services import QuestionService


def grpc_handlers(server):
    app_registry = AppHandlerRegistry("quickstart", server)
    app_registry.register(QuestionService)
```

This Handler will be the entrypoint for the service registration. Set its path as the `ROOT_HANDLERS_HOOK` 
of the `GRPC_FRAMEWORK` settings

```python
# tutorial/settings.py
...
GRPC_FRAMEWORK = {
    "ROOT_HANDLERS_HOOK" : 'quickstart.handlers.grpc_handlers'
}
```


### Generate the protofile and the client associated to the model

```bash
python manage.py generateproto
```

### Assign the newly generated class to the serializer

```python
# quickstart/serializers.py
from django_socio_grpc import proto_serializers
import quickstart.grpc.quickstart_pb2 as quickstart_pb2
from .models import Question


class QuestionProtoSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = Question
        proto_class = quickstart_pb2.QuestionResponse # Modification here
        proto_class_list = quickstart_pb2.QuestionListResponse # Modification here
        fields = ["id", "question_text", "pub_date"]
```

### Launch the server

```bash
python manage.py grpcrunaioserver --dev
```
