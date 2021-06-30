## Changelog

#### version 0.8.10

- Update dependency
- Fix async context.write not await and add an FakeAsyncContext for Fake gRPC toolkit
#### version 0.8.9

- Fix raise not found instead of constext.abort

#### version 0.8.8

- Fix context abort await on permission denied
- BaseSerializer now usable directly with default methods

#### version 0.8.7

- Fix concurrency call overriding request and context

#### version 0.8.6

- Use os.environ instead of settings fpr getting project name

#### version 0.8.5

- Add project name in package

#### version 0.8.4

- Add details for generateproto --check command

#### version 0.8.3

- Add option check to generateproto command for ci

#### version 0.8.2

- Fix serializer when reading many data

#### version 0.8.1

- fix async before action in async_handler

#### version 0.8.0

- Refacto the servicer to be a proxy instead of a wrapper to help code structuration
- Write async mixins
- Support async method in FakeGrpc for testing
- Add test for sync mixins and async mixins

### version 0.7.2

- change context key for the auth token from `token` to `auth`
#### version 0.7.1

- Support for array field of json field
#### version 0.7.0

- Support JsonField and ArrayField in proto generation
- Support custom field with the name `__custom__[proto_type]__[proto_field_name]__`
- Remove support for `__link--[proto_type]--[proto_field_name]__`, `__repeated-link--[proto_type]--[proto_field_name]__` and `__count__` as custom is a more generalist way to do it. See [list messages](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/mixins.py#L81) and [test example](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/tests/fakeapp/models.py#L76)
- Add utils [AppHandlerRegistry](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/utils/servicer_register.py#L4) to register easily servicer. See [test for example](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/tests/test_app_handler_registry.py#L32)

#### version 0.6.3

- fix metadata key case -> now ignored, developper can send the key independent of the case

#### version 0.6.2

- fix exceptions messages not serializable
- nested field support

#### version 0.6.1

- fix list mixins return format
- need proto_class_list in serializer
