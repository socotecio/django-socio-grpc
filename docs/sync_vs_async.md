## Sync vs Async

Django Socio gRPC Framework actually support both async and sync mode for gRPC.

gRPC AsyncIO API is the new version of gRPC Python whose architecture is tailored to AsyncIO. So its the recommended usage. The change are minor in the API but major in the underlying stack. It will allow you to handle way more requests in some case. Specifically if you use streaming where using it in sync mode can block your whole server.

The Django Socio gRPC framework work the same in sync or async mode. But be carreful of some minor chnage in the import or in the Django ORM call.

### The different imports

| Async Class | Sync class |
| --------- | --------- |
| django_socio_grpc.mixins.AsyncCreateModelMixin | django_socio_grpc.mixins.CreateModelMixin |
| django_socio_grpc.mixins.AsyncListModelMixin | django_socio_grpc.mixins.ListModelMixin |
| django_socio_grpc.mixins.AsyncStreamModelMixin | django_socio_grpc.mixins.StreamModelMixin |
| django_socio_grpc.mixins.AsyncRetrieveModelMixin | django_socio_grpc.mixins.RetrieveModelMixin |
| django_socio_grpc.mixins.AsyncUpdateModelMixin | django_socio_grpc.mixins.UpdateModelMixin |
| django_socio_grpc.mixins.AsyncPartialUpdateModelMixin | django_socio_grpc.mixins.PartialUpdateModelMixin |
| django_socio_grpc.mixins.AsyncDestroyModelMixin | django_socio_grpc.mixins.DestroyModelMixin |
| --------------------- | --------------------- |
| django_socio_grpc.generics.AsyncCreateService | django_socio_grpc.generics.CreateService |
| django_socio_grpc.generics.AsyncListService | django_socio_grpc.generics.ListService |
| django_socio_grpc.generics.AsyncStreamService | django_socio_grpc.generics.StreamService |
| django_socio_grpc.generics.AsyncRetrieveService | django_socio_grpc.generics.RetrieveService |
| django_socio_grpc.generics.AsyncDestroyService | django_socio_grpc.generics.DestroyService |
| django_socio_grpc.generics.AsyncUpdateService | django_socio_grpc.generics.UpdateService |
| django_socio_grpc.generics.AsyncReadOnlyModelService | django_socio_grpc.generics.ReadOnlyModelService |
| django_socio_grpc.generics.AsyncModelService | django_socio_grpc.generics.class ModelService(
 |

### The usage of the django ORM

The django ORM (in its verson <=4.0) is currenctly not supporing async request. This way you can't use orm methodes inside an async context.
Fortunatly it exist wrapper from asgiref that allow you to wrap method sync method to use them in an async context.

See [example inside the mixins](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/mixins.py#L284) to understand it and use it in your project


### The gRPC API difference with Stream

The main advantage to use async api is the use of not blocking stream. Indeed instead of using a generator as stream answer we can now read and write data from the context where we need to.

The context is an instance of [ServicerContext](https://grpc.github.io/grpc/python/grpc_asyncio.html#grpc.aio.ServicerContext) so for stream instance (methods defined as stream in the proto file) you have acess to read, write or both method depend on if you have your request, response or both marked as stream in the proto file.
