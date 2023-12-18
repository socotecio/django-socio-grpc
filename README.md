# Django Socio Grpc

![https://img.shields.io/pypi/v/django-socio-grpc.svg](https://img.shields.io/pypi/v/django-socio-grpc.svg)
![https://img.shields.io/badge/Maintained%3F-yes-green.svg](https://img.shields.io/badge/Maintained%3F-yes-green.svg)
![https://img.shields.io/pypi/pyversions/django-socio-grpc](https://img.shields.io/pypi/pyversions/django-socio-grpc)
![https://img.shields.io/pypi/l/django-socio-grpc](https://img.shields.io/pypi/l/django-socio-grpc)

Django Socio gRPC is a toolkit for building gRPC services, inspired by Django REST framework. It is based on [django-grpc-framework](https://github.com/fengsp/django-grpc-framework) and includes all the DRF features such as authentication, filtering, pagination, and more complex proto generation.


## Documentation

The documentation can be found [here](https://django-socio-grpc.readthedocs.io/en/latest/).


## Requirements

- Python (>= 3.8)
- Django (2.2, >=3.0), Django REST Framework (>=3.10)
- grpcio-tools (>=1.50.0)


## Installation

Run the following command using pip:
```bash
    pip install django-socio-grpc
```
Then, add ``django_socio_grpc`` to your ``INSTALLED_APPS`` setting:

```python
    INSTALLED_APPS = [
        ...
        'django_socio_grpc',
    ]
```

## Contributing
