Advanced ASync Example
=======================

All the example describred here can be found in the `example repository <https://github.com/socotecio/django-socio-grpc-example>`_

This page is still in Work in progress

Overview
--------

This is an advanced example to demonstrates DSG usages(in asynchronous mode).

We will generate a simple bibliographic service, that illustrates many aspects of DSG.

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

.. code-block:: python

    from django.db import models

    # Author class
    class Author(models.Model):
        author_id = models.UUIDField(primary_key=True)
        name_first = models.CharField(max_length=100)
        name_last = models.CharField(max_length=100)
        birth_date = models.DateField()


    class Publisher(models.Model):
        publisher_id = models.UUIDField(primary_key=True)
        name = models.CharField(max_length=100)
        address = models.CharField(max_length=100)
        city = models.CharField(max_length=100)
        state_province = models.CharField(max_length=100)
        country = models.CharField(max_length=100)
        website = models.URLField()


    class Book(models.Model):
        book_id = models.UUIDField(primary_key=True)
        title = models.CharField(max_length=100)
        authors = models.ManyToManyField(Author)
        isbn = models.CharField(max_length=20)
        publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
        publication_date = models.DateField()


The `Book` model is a simple Django model, with a few fields.

Serializers
-----------

The next step is to define the serializers that will be used to serialize the data.

The `BookSerializer` is defined in `serializers.py`:


Code Walkthrough
----------------
