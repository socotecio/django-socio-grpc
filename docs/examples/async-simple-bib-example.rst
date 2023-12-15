Simple ASync Example
=================

Overview
--------

This simple example demonstrates the socio-grpc framework (in asynchronous mode).

We will generate a simple bibliographic service, that illustrates many aspects of socio-grpc.

The service will be a simple CRUD service, with a single entity type, `Book`.


Django models
-------------

The first step is to define the Django models that will be used to store the data.

The `Book` model is defined in `models.py`:

```python
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20)
    publisher = models.CharField(max_length=100)
    publication_date = models.DateField()
```

The `Book` model is a simple Django model, with a few fields.



Code Walkthrough
----------------
