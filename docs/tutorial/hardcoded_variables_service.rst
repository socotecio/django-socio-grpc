.. hardcoded_variables_service:

Constants Service
===========================

Sometimes, we need to create shared constants variables. Instead to copy and paste them on your front-end as JSON
you should use `ConstantsToMapMessageServiceFactory`

Usage
-------

Define a class inherit from `ConstantsToMapMessageServiceFactory` in ex you managing stock and you want to define status for your product:
 
```python
    class ProductType(metaclass=ConstantsToMapMessageServiceFactory):
        # product status code = food status label
        DF = "Dry Food"
        PF = "Perishable Food"
        NE = "No edible"
```

and this class (here ProductType) will offer attributes and methods below. 

Methods
^^^^^^^^^

- `get_as_choices`: which can be used ie. on Django CharField in `choices` keyword param.
  in our `ProductType` class a tuple containing `(("DF", "Dry Food",)("PF", "Perishable Food",),)`

- `get_as_method` that you must be use on `Meta.grpc_methods` of the corresponding models
  for generate proto method definition.

- `get_as_message`  that you must be use on `Meta.grpc_messages` of the corresponding
  models for generate proto message definition.

- `get_as_service` must be called on the corresponding `ModelService` inside the method `List<your class name>` method you will define. 

Attributes
^^^^^^^^^^^^

- `available_choices: dict` allow you to READ attributes you have defined as dict. 

Customize
^^^^^^^^^^^^

By default, the class will create a message named "<your child class name>" and a service with "List<your child class name>"
If you want twist it, your child can redefined this attributes (and more) in `class Meta`.


- `protobuff_map_attribute` (default: `value`) root key returned in
    gRPC response (message attribute on proto).

- `service_method_name` (default: `List<your child class name>`) gRPC
    method name. Will you must define in your ModelService.

- `proto_message_name` (default: `<your class name>`) proto message as it will be defined on .proto

- `service_request` (default: `{"is_stream": False, "message": <your child class name>}`) 

- `service_response` (default: `{"is_stream": False, "message": <your child class name>}`)



Example
---------

For example we want to define product type for our product models. 

- `models.py`

```python
    class ProductType(metaclass=ConstantsToMapMessageServiceFactory):
        DF = "Dry Food"
        PF = "Perishable Food"
        NE = "No edible"

    class Product(BaseModel):
        ProductType = ProductType
        product_type = models.CharField(
            choices=ProductType.get_as_choices()
        )
        class Meta:
            grpc_messages = {
                **ProductType.get_as_message(),
            }
            grpc_methods = {**ProductType.get_as_method()}

```
- `view.py` (or where you havedefined your services)

```python
    from product.models import Product

    class ProductService(generics.ModelService):

        def ListProductsType(self, *args):
            return Product.ProductType.get_as_service()
```
- GRPC call on `ListProductsType` will return:

```json
    {
    "value": {
        "DF" : "Dry Food"
        "PF" : "Perishable Food"
        "NE" : "No edible"
        }
    }
```
