# Django Socio Grpc

![https://img.shields.io/pypi/v/django-socio-grpc.svg](https://img.shields.io/pypi/v/django-socio-grpc.svg)

![https://img.shields.io/badge/Maintained%3F-yes-green.svg](https://img.shields.io/badge/Maintained%3F-yes-green.svg)

![https://img.shields.io/pypi/pyversions/django-socio-grpc](https://img.shields.io/pypi/pyversions/django-socio-grpc)

![https://img.shields.io/pypi/l/django-socio-grpc](https://img.shields.io/pypi/l/django-socio-grpc)

Django Socio gRPC is a toolkit for building gRPC services, inspired by djangorestframework. It is base on [django-grpc-framework](https://github.com/fengsp/django-grpc-framework) with all the DRF features enable Auth, Filter, Pagination, more complex proto generation...

## DOCUMENTATION

[https://socotecio.github.io/django-socio-grpc/](https://socotecio.github.io/django-socio-grpc/)

## Requirements

- Python (>= 3.6)
- Django (2.2, >=3.0), Django REST Framework (>=3.10)
- gRPC, gRPC tools, proto3


## Installation

```bash
    pip install django-socio-grpc
```
Add ``django_socio_grpc`` to ``INSTALLED_APPS`` setting:

```python
    INSTALLED_APPS = [
        ...
        'django_socio_grpc',
    ]
```

For more informations follow the quickstart: [https://socotecio.github.io/django-socio-grpc/](https://socotecio.github.io/django-socio-grpc/)

## Launch dev environnement

```python
    docker-compose up --build
    docker-compose exec django-socio-grpc python test_utils/migrate.py
    docker-compose exec django-socio-grpc python test_utils/load_tests.py
    # single test launch
    docker-compose exec django-socio-grpc python test_utils/load_tests.py django_socio_grpc/tests/test_proto_generation.py
```
## Contribute to documentation

Launch in local:
```bash
docker-compose exec django-socio-grpc mkdocs serve -a localhost:6001
# Or just docker-compose up and navigate to localhost:6001
```

Deploy Documentation:

```bash
mkdocs gh-deploy -t readthedocs -m "[ci skip] auto commit with MKDocs"
```