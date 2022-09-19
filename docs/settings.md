## Settings


You can specify settings in django settings module in such way:

```python
GRPC_FRAMEWORK = {
    "ROOT_HANDLERS_HOOK": "__YOUR_PROJECT_NAME___.handlers.grpc_handlers",
    "SEPARATE_READ_WRITE_MODEL": False,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissions",
    ],
    "MAP_METADATA_KEYS": {
        "HEADERS": "HEADERS", 
        "PAGINATION": "PAGINATION", 
        "FILTERS": "FILTERS"
    },
}
```

### Authentication and permissions options

It supports standard and Django REST frameworks authentications and permissions management.
So feel free to specify `DEFAULT_AUTHENTICATION_CLASSES` and `DEFAULT_PERMISSION_CLASSES`
as usually. Please read more in [Permissions and authentication](permissions_and_authentication.md) section. 

### Metadata options

Option `MAP_METADATA_KEYS` is not mandatory (in the example default value is shown) and allow
to specify the place in gRPC metadata where to search headers, pagination and filters data. By default
each type of data has appropriate metadata key where data is saved in JSON format. So, in case of Bearer authorization,
you should specify HEADERS metadata item as such JSON value:

```json
{"Authorization": "Bearer xxxxxx", "User-Agent": "for_example"}
```

It's default behaviour. If you would like to have each header in separate metadata item,
you can omit `HEADERS` key in `MAP_METADATA_KEYS` option.  

### Separate read write model option

Option `SEPARATE_READ_WRITE_MODEL` allow to separate request message and response message
in proto file (default is True).