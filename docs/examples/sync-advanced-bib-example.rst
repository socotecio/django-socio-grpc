Advanced Sync Example
=====================


Overview
--------

This is an advanced example demonstrates the socio-grpc framework (in synchronous mode).

We will generate a simple bibliographic service, that illustrates many aspects of socio-grpc.

The service will be a simple CRUD service, with a single entity type, `Book`.


The following socio-grpc features are illustrated:

 * UUID primary keys
 * serialization of different field types (datetype, char, integer, float, boolean)
 * Foreing key relationship serialization
 * Many-to-many relationships serialization
 * Custom gRPC commands
 * Filtersets
 * Synchronous mode



Django models
-------------

The first step is to define the Django models that will be used to store the data.

The `Book` model is defined in `models.py`:

```python

from django.db import models

# Author class
class Author(models.Model):
    name_first = models.CharField(max_length=100)
    name_last = models.CharField(max_length=100)
    birth_date = models.DateField()

# publisher class

class Publisher(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    website = models.URLField()


class Book(models.Model):
    title = models.CharField(max_length=100)
    authors = models.ManyToManyField(Author)

    isbn = models.CharField(max_length=20)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    publication_date = models.DateField()


```

The `Book` model is a simple Django model, with a few fields.

Serializers
-----------

The next step is to define the serializers that will be used to serialize the data.

The `BookSerializer` is defined in `serializers.py`:

```python


Code Walkthrough
----------------
