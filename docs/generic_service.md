# Generic Service

Django Socio gRPC use services instead of View of Viewset. Except for the name and the internal layer a Service work like a [DRF Generic views](https://www.django-rest-framework.org/api-guide/generic-views/#api-reference).

The generic services are class based service that allow you to reuse part of common logic between api. Same logic that DRF Generics views.

If the generic services don't suit the needs of your API, you can drop down to using the regular APIView class, or reuse the mixins and base classes used by the generic services to compose your own set of reusable generic services.

## Examples

```python
from django.contrib.auth.models import User
from myapp.serializers import UserProtoSerializer
from django_socio_grpc import generics

class UserListService(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProtoSerializer
```
