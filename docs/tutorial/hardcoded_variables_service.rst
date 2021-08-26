.. hardcoded_variables_service:

Globals Variables Service
===========================

Sometimes, we need to create globals variables. Instead to copy and paste them on your front-end as JSON
you should use `GlobalsServiceFactory`

Usage
-------

Methods
^^^^^^^^^

- `get_as_choices`: which can be used ie. on Django CharField in `choices` keyword param.

- `get_as_method` will be used on `Meta.grpc_methods` of the corresponding models
  for allow proto method definition.

- `get_as_message` will be used on `Meta.grpc_messages` of the corresponding
  models for allow proto message deinition.

- `get_as_service` must be called on the corresponding ModelService inside a
  simple `List<your class name>` method define by him. 

Attributes
^^^^^^^^^^^^

- `avaible_choices: dict` allow you to do things with attributes you have defined
    exposed py a dict.

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
    class ProductType(metaclass=GlobalsServiceFactory):
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
- `view.py` (or where you hav defined your services)

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
