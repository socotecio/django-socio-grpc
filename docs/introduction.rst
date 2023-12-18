Introduction
============

Overview
--------

Django Socio gRPC (*DSG*) is a Python library that allows you to create gRPC services in a Django application.
It is similar to Django Rest Framework (*DRF*) and provides features for setting up services and data serialization.
It was forked from django-grpc-framework in 2021 and aims to provide all the features of DRF while adding gRPC-specific features.
With DSG, you can create high-performance, scalable, and maintainable gRPC services that
integrate seamlessly with your Django application.

Why gRPC ?
~~~~~~~~~~

gRPC is a high-performance, open-source RPC framework developed by Google.

It is also designed to be easy to use, and it provides a number of features that make it a good choice for building microservices.
Some of these features include:

- **Performance**: gRPC is designed to be fast and efficient. It uses HTTP/2,
  which brings lower latency by header data compression, multiplexing and more.
- **Bidirectional streaming**: gRPC supports bidirectional streaming,
  it allows you to build services that can keep a connection open and send messages back and forth.
- **Protobuf**: gRPC uses Protobuf (*Protocol Buffers*) as its serialization format.
  Protobuf is a binary format that is more efficient than JSON.
  It also has an IDL (Interface Definition Language) that allows you to define your data structures
  in a language-agnostic way.


Why use DSG ?
~~~~~~~~~~~~~

If you're building a Django application and need to create gRPC services,
Django Socio Grpc is an excellent choice. It provides a familiar and consistent way
to define services and methods, making it easy to get started quickly with Django and DRF experience.
DSG is also natively supports async Django.

DSG also automatically generate all the protofiles by parsing the python serializers. 
Allowing developers to completely abstract protobuf complexity. 

It implement the following Django/Django REST framework features:

* CRUD Mixins
* Custom actions
* Automatic proto generation
* Authentication / Permissions
* Serializers
* Filters 
* gRPC Exception mapping
* Django like logging
* Django like middleware

How does it work ?
~~~~~~~~~~~~~~~~~~

Django Socio gRPC works by exposing gRPC services and abstracting away the details of the gRPC protocol.
When a gRPC request is received, Django Socio Grpc maps the request to the appropriate service and action,
and then returns a gRPC message (or yields multiple ones in a response-streaming route).
This mapping allows you to interact with the gRPC services in a way that is familiar to Django developers,
making most of the Django and DRF external libraries compatible with DSG.