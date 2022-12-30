# gRPC sever and services registration


## grpcrunserver && grpcrunaioserver

As Django Socio gRPC use gRPC and so HTTP2 it use the grpc lib to launch the server and not wsgi or asgi.

grpcrunserver is the django command launching a synchrone server and grpcrunaioserver the async server.

For performance issue and Stream availability we recommend you to always use grpcrunaioserver

Run a grpc server:

```bash
python manage.py grpcrunaioserver
```

Run a grpc development server, this tells Django to use the auto-reloader and run checks:

```bash
python manage.py grpcrunaioserver --dev
```

Run the server with a certain address:

```bash
python manage.py grpcrunaioserver 127.0.0.1:8000 --max-workers 5
```

## Service Registration

To be able to serve endpoint we need to register our endpoint into the gRPC server for that we need a handler hook function.

```python
def grpc_handlers(server):
    ...
```

Then we need to set the ROOT_HANDLERS_HOOK settings with the path to this handler method:

```python
GRPC_FRAMEWORK = {
    ...
    'ROOT_HANDLERS_HOOK': 'path.to.your.grpc_handlers',
}
```

Once defined you need to register your service. To easily do that we provide a class helper, AppHandlerRegistry. It allow to register Services for a particular app.


```python
from django_socio_grpc.utils.servicer_register import AppHandlerRegistry
from my_app_name.services.my_service import MyService

def grpc_handlers(server):
    app_registry = AppHandlerRegistry("my_app_name", server)
    app_registry.register(MyService)
```


AppHandlerRegistry also support dynamic import by name but it can imply error as it expect to find the file to a correct location (by default `<app_name>/services/<service_name>_service.py`) that can be changed with undocumented arguments:

```python
from django_socio_grpc.utils.servicer_register import AppHandlerRegistry

def grpc_handlers(server):
    app_registry = AppHandlerRegistry("my_app_name", server)
    app_registry.register("MyService")
```

## To go deeper

Under the hood AppHandlerRegistry register method will use the name of the app and the name of the service to import the correct method from the pb2_grpc file generated automatically by the generateproto command.

This helper is also the entrypoint for the registration of the service for the proto generation. So even if you can use Django Socio gRPC without it the automatic registration and so the automatic proto generation will not work.

Code snippet to explain how we use the function from the pb2_grpc file

```python
pb2_grpc = import_module(
    f"{self.app_name}.{self.grpc_folder}.{self.app_name}_pb2_grpc"
)

controller_name = service_class.get_controller_name()
add_server = getattr(
    pb2_grpc, f"add_{controller_name}Servicer_to_server"
)

add_server(service_class.as_servicer(), self.server)
```
