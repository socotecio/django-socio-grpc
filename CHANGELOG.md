# Changelog

## 0.19.4

- Add support for serializer adata

## 0.19.3

- Fix Auth middleware not async safe

## 0.19.2

- Fix recursive serializer
- Fix some async issue with filter_queryset

## 0.19.1

- Add SAFE_ACTIONS Tuple

## 0.19.0

- Make django middleware working or at least not crashing inside grpc_middleware
- Adding logic for extra log context if needed.
- Refactoring some of the internal container/proxy/http classes to have cleaner logic

## 0.18.1

- Fix calling root handler with good sync/async context in generateproto

## 0.18.0

- Fix typo in AlreadyExist Exception
- Add locale middleware support
- Merge ROOT metadata key into HEADERS proxy context without needed to use HEADERS metadat key
- Force ROOT_HANDLERS_HOOK to be called in sync mode if not coroutine to be able to make db call inside it
- Fix exception in logging for python 3.11 & use github action with multiple python version to verify integrity in multiple python version
- Refactor proto generation to support optional
- Deprecate the use of cardinality keywork in "type" key in grpc action decorator and introduce the new "cardinality" key.
- Add async function like afilter_queryset, aget_object, aget_serializer, amessage & acheck_object_permissions
- Support first middleware logic

## 0.10.21

- Fix the reuse old number that was not working because of `__custom__` field

## 0.10.2O

- Avoid breaking changes with fields number changes by trying to reuse old number

## 0.10.19

- Display log when getting an unexpected exception in a grpc call


## 0.10.18

- Uniformize the status code returned by exceptions


## 0.10.16

- Test and improve logger emitter and exception catcher


## 0.10.7

- Add log when receiving an incoming grpc-request

## 0.10.6

- Add log when receiving an incoming grpc-request

## 0.10.5

- Not stop current thread to send a log if server is launch in sync mode

## 0.10.4

- Fix a log call to not be send

## 0.10.3

- Add option to not send log to server

## 0.10.2

- Allow logging to work in async mode

## 0.10.1

- Fix metadata not send in async stub for test (FakeGrpcClass)

## 0.10.0

- Integrate handle exception to improve monitoring if you want to

## 0.9.0

- Integrate logging handler option

## 0.8.11

- Close old connection on get_autocommit True to avoid production bug of db already closed
- use w+ when generating proto and r+ when checking

## 0.8.10

- Update dependency
- Fix async context.write not await and add an FakeAsyncContext for Fake gRPC toolkit

## 0.8.9

- Fix raise not found instead of constext.abort

## 0.8.8

- Fix context abort await on permission denied
- BaseSerializer now usable directly with default methods

## 0.8.7

- Fix concurrency call overriding request and context

## 0.8.6

- Use os.environ instead of settings fpr getting project name

## 0.8.5

- Add project name in package

## 0.8.4

- Add details for generateproto --check command

## 0.8.3

- Add option check to generateproto command for ci

## 0.8.2

- Fix serializer when reading many data

## 0.8.1

- fix async before action in async_handler

## 0.8.0

- Refacto the servicer to be a proxy instead of a wrapper to help code structuration
- Write async mixins
- Support async method in FakeGrpc for testing
- Add test for sync mixins and async mixins

## 0.7.2

- change context key for the auth token from `token` to `auth`
## 0.7.1

- Support for array field of json field
## 0.7.0

- Support JsonField and ArrayField in proto generation
- Support custom field with the name `__custom__[proto_type]__[proto_field_name]__`
- Remove support for `__link--[proto_type]--[proto_field_name]__`, `__repeated-link--[proto_type]--[proto_field_name]__` and `__count__` as custom is a more generalist way to do it. See [list messages](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/mixins.py#L81) and [test example](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/tests/fakeapp/models.py#L76)
- Add utils [AppHandlerRegistry](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/utils/servicer_register.py#L4) to register easily servicer. See [test for example](https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/tests/test_app_handler_registry.py#L32)

## 0.6.3

- fix metadata key case -> now ignored, developper can send the key independent of the case

## 0.6.2

- fix exceptions messages not serializable
- nested field support

## 0.6.1

- fix list mixins return format
- need proto_class_list in serializer
