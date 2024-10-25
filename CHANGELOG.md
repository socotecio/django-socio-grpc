# Changelog

## 0.23.1

- Adding a new filters.OrderingFilter to allow array ordering using list directly as supported by gRPC
- Changing lark-parser dependency to lark
- Support for Decimal type in type hints for proto generation

## 0.23.0

- Dropping not working support for Django < 4
- Dropping support for python < 3.10
- Add Django version into the CI to assure that supporting version still works
- Made Internal Proxy Request/Response inherit from django Request/Response
- Create Request Meta and Response Headers interceptor/proxy to be able to get/set correctly headers for both request and response
- Create the http_to_grpc decorator to provide a way to use django decorator in DSG
- Add cache_enpoint, cache_endpoint_with_deleter, vary_on_metadata decorator
- Stop allowing metadata that doesn't have lower case key and metadata values that are not str or bytes in FakeGrpc testing tool

## 0.22.9

- Security dependencies update
- Minor documentation fixes

## 0.22.8

- Add new "add_registered_method_handlers" method in FakeServer class for test

## 0.22.7

- use "including_default_value_fields" or "always_print_fields_with_no_presence" depending of protobuf version

## 0.22.6

- Fix the capacity to read from iterator stream in tests

## 0.22.5

- Fix circular import

## 0.22.4

- Improve message to data logic

## 0.22.3

- Fix serializer using Django model property not correctly finding the good proto type

## 0.22.2

- Fix stream response tests

## 0.22.1

- Fix _get_resource_file_name from protoc depend of grpc tools version

## 0.22.0

- Change the logic for default value when data are not set or set to default value in grpc message to be close of what a DRF user could expect
- Add extra options to the runserver command to allow custom parameters to grpcrunaioserver
- Fix ProtoMessage can be string in generation plugin
- Fix pagination_class attr of service can be set to None isntead of not set at all
- Change linter to ruff
- Add healthcheck support
- Improve Stream request unit test and example

## 0.21.5

- Fix type hints not correctly working for python >3.10

## 0.21.3 & 0.21.4

- Fix wrong import

## 0.21.2

- Fix old args compatibility in grpc_action decorator and not only GrpcAction class

## 0.21.1

- Fix docs build

## 0.21.0

- Add possibility to filter with request args instead of metadata
- Present a new generation plugin system
- Present a proto NameConstructor interace to customize the proto message names

## 0.20.3

- Add the new reworked documentation using read the docs

## 0.20.2

- Fix python packege incompatibility

## 0.20.1

- Clean some tests
- Rework gRPC exception to inherit from rest_framework exception instead of python base Exception

## 0.20.0

- Improve logging system and tooling to be more generic and overridable

## 0.19.6

- Fix wrongly formated import

## 0.19.5

- Add async serializer methods as asave, ais_valid, acreate and aupdate
- Update minor doc
- Add some HTTP request functionnality to InternalHttpRequest

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
