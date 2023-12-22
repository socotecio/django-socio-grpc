Simple ASync Example
====================

All the example describred here can be found in the `example repository <https://github.com/socotecio/django-socio-grpc-example>`_

This page is still in Work in progress

Overview
--------

This is a simple example to demonstrates DSG usages(in asynchronous mode).

We will generate a simple bibliographic service, that illustrates many aspects of DSG.

The service will be a simple CRUD service, with a single entity type, `Book`.


Django models
-------------

The first step is to define the Django models that will be used to store the data.

The `Book` model is defined in `models.py`:


.. code-block:: python

    class Book(models.Model):
        title = models.CharField(max_length=100)
        author = models.CharField(max_length=100)
        isbn = models.CharField(max_length=20)
        publisher = models.CharField(max_length=100)
        publication_date = models.DateField()


The `Book` model is a simple Django model, with a few fields.



Code Walkthrough
----------------
