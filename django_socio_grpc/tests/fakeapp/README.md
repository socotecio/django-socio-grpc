Test application
==================

Proto generation
-----------------

Command to compile proto file to python file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

```shell
    docker-compose run django-socio-grpc python -m grpc_tools.protoc --proto_path=./ --python_out=./ --grpc_python_out=./ ./django_socio_grpc/tests/grpc_test_utils/unittest.proto
    # or if docker already run
    docker-compose exec django-socio-grpc python -m grpc_tools.protoc --proto_path=./ --python_out=./ --grpc_python_out=./ ./django_socio_grpc/tests/grpc_test_utils/unittest.proto
```

Generating protos for FakeApp
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

```shell
    docker-compose exec django-socio-grpc python test_utils/generateproto.py
```
