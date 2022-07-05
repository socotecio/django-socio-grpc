from unittest import mock

from django.test import TestCase

from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.generics import GenericService
from django_socio_grpc.grpc_actions.actions import GRPCActionMixin
from django_socio_grpc.grpc_actions.placeholders import (
    AttrPlaceholder,
    FnPlaceholder,
    LookupField,
    SelfSerializer,
    StrTemplatePlaceholder,
)
from django_socio_grpc.proto_serializers import ProtoSerializer


class MyProtoSerializer(ProtoSerializer):
    pass


class MyOtherProtoSerializer(ProtoSerializer):
    pass


class BaseService(GenericService):
    serializer_class = MyProtoSerializer


class TestPlaceholders(TestCase):
    def test_self_serializer(self):
        class MyMixin(GRPCActionMixin):
            @grpc_action(request=SelfSerializer, response=SelfSerializer)
            def MethodOverriden(self, request, context):
                pass

            @grpc_action(request=SelfSerializer, response=SelfSerializer)
            def Method(self, request, context):
                pass

        class MyService(MyMixin, BaseService):
            def get_serializer_class(self):
                if self.action == "MethodOverriden":
                    return MyOtherProtoSerializer
                return super().get_serializer_class()

        self.assertIs(MyService.Method.request, MyProtoSerializer)
        self.assertIs(MyService.Method.response, MyProtoSerializer)

        self.assertIs(MyService.MethodOverriden.request, MyOtherProtoSerializer)
        self.assertIs(MyService.MethodOverriden.response, MyOtherProtoSerializer)

    def test_attr_placeholder(self):
        class MyMixin(GRPCActionMixin):
            @grpc_action(request=AttrPlaceholder("_my_serializer"), response=MyProtoSerializer)
            def Method(self, request, context):
                pass

        class MyService(MyMixin, BaseService):
            _my_serializer = MyOtherProtoSerializer

        self.assertIs(MyService.Method.request, MyOtherProtoSerializer)
        self.assertIs(MyService.Method.response, MyProtoSerializer)

    def test_fn_placeholder(self):
        fn = mock.MagicMock(return_value=MyOtherProtoSerializer)

        class MyMixin(GRPCActionMixin):
            @grpc_action(request=FnPlaceholder(fn), response=MyProtoSerializer)
            def Method(self, request, context):
                pass

        class MyService(MyMixin, BaseService):
            pass

        self.assertIs(MyService.Method.request, MyOtherProtoSerializer)
        self.assertIs(MyService.Method.response, MyProtoSerializer)
        self.assertEqual(fn.call_count, 1)
        self.assertEqual(len(fn.call_args.args), 1)
        self.assertIsInstance(fn.call_args.args[0], MyService)

    @mock.patch(
        "django_socio_grpc.grpc_actions.placeholders.get_lookup_field_from_serializer",
        return_value=("my_name", "my_type"),
    )
    def test_lookup_placeholder(self, _):
        class MyMixin(GRPCActionMixin):
            @grpc_action(
                request=LookupField,
                response=MyProtoSerializer,
            )
            def Method(self, request, context):
                pass

        class MyService(MyMixin, BaseService):
            pass

        lookup_name = MyService.Method.request[0]["name"]
        lookup_type = MyService.Method.request[0]["type"]

        self.assertEqual(lookup_name, "my_name")
        self.assertEqual(lookup_type, "my_type")
        self.assertIs(MyService.Method.response, MyProtoSerializer)

    def test_str_template_placeholder(self):
        def my_name(service):
            return service.__class__.__name__

        class MyMixin(GRPCActionMixin):
            @grpc_action(
                request=[],
                request_name=StrTemplatePlaceholder("{}_{}", my_name, "_id"),
                response=MyProtoSerializer,
            )
            def Method(self, request, context):
                pass

        class MyService(MyMixin, BaseService):
            _id = 3

        self.assertEqual(MyService.Method.request_name, "MyService_3")
        self.assertIs(MyService.Method.response, MyProtoSerializer)
