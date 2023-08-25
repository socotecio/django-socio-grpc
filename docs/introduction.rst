Introduction
============

Overview
--------
Django Socio Grpc (DSG) is a Python library that allows you to create gRPC services in a Django application.
It is similar to Django Rest Framework (DRF) and provides features for setting up services and data serialization.
It was forked from django-grpc-framework in 2021 and aims to provide all the features of DRF while adding gRPC-specific features.
With DSG, you can create high-performance, scalable, and maintainable gRPC services that integrate seamlessly with your Django application.

Why use DSG ?
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're building a Django application and need to create gRPC services,
Django Socio Grpc is an excellent choice. It provides a familiar and consistent way
to define services and methods, making it easy to get started quickly. Additionally,
it leverages Django's powerful ORM and serialization framework, allowing you to easily
integrate your gRPC services with the rest of your application.

How does it work ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django Socio Grpc works by exposing gRPC services and abstracting away the details of the gRPC protocol.
When a gRPC request is received, Django Socio Grpc maps the request to the appropriate service and action,
and then returns a gRPC message, either directly with built-in serializers or by providing your own.
This makes it easy to create high-performance, scalable,
and maintainable gRPC services that integrate seamlessly with your Django application.
