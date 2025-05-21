from typing import Annotated

from django.db import models
from django.test import TestCase
from rest_framework import serializers

from django_socio_grpc import proto_serializers
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.generics import GenericService
from django_socio_grpc.grpc_actions.utils import (
    get_partial_update_request_from_serializer_class,
)
from django_socio_grpc.protobuf.exceptions import ProtoRegistrationError
from django_socio_grpc.protobuf.generation_plugin import (
    GlobalScopeEnumGenerationPlugin,
    GlobalScopeWrappedEnumGenerationPlugin,
    InMessageEnumGenerationPlugin,
    InMessageWrappedEnumGenerationPlugin,
)
from django_socio_grpc.protobuf.proto_classes import ProtoEnumLocations

# -- INT ENUM --


class MyIntEnum(models.IntegerChoices):
    """My int choices"""

    ONE = 1
    TWO = 2
    THREE: Annotated[int, "My comment"] = 3


class MyIntModel(models.Model):
    choice_field = models.IntegerField(
        choices=[(1, "One"), (2, "Two"), (3, "Three")],
        default=1,
    )


class MyIntModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = MyIntModel
        fields = "__all__"


class MyWronglyAnnotatedModel(models.Model):
    class WrongAnnotation:
        pass

    choice_field: Annotated[models.IntegerField, WrongAnnotation] = models.IntegerField(
        choices=MyIntEnum.choices,
        default=MyIntEnum.ONE,
    )


class MyWronglyAnnotatedIntModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = MyWronglyAnnotatedModel
        fields = "__all__"


class MyAnnotatedIntModel(models.Model):
    choice_field: Annotated[models.IntegerField, MyIntEnum] = models.IntegerField(
        choices=MyIntEnum.choices,
        default=MyIntEnum.ONE,
    )


class MyAnnotatedIntModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = MyAnnotatedIntModel
        fields = "__all__"


class MyAnnotatedIntSerializer(proto_serializers.ProtoSerializer):
    choice_field: Annotated[serializers.ChoiceField, MyIntEnum] = serializers.ChoiceField(
        choices=MyIntEnum.choices,
    )

    class Meta:
        fields = "__all__"


# -- STR ENUM --


class MyStrEnum(models.TextChoices):
    """My str choices"""

    VALUE_1 = "VALUE_1"
    VALUE_2 = "VALUE_2"
    VALUE_3: Annotated[str, "My comment"] = "VALUE_3"


class MyStrModel(models.Model):
    choice_field = models.CharField(
        choices=MyStrEnum.choices,
        default=MyStrEnum.VALUE_1,
    )


class MyStrModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = MyStrModel
        fields = "__all__"


class MyAnnotatedStrModel(models.Model):
    choice_field: Annotated[models.CharField, MyStrEnum] = models.CharField(
        choices=MyStrEnum.choices,
        default=MyStrEnum.VALUE_1,
    )


class MyAnnotatedStrModelSerializer(proto_serializers.ModelProtoSerializer):
    class Meta:
        model = MyAnnotatedStrModel
        fields = "__all__"


class MyAnnotatedStrSerializer(proto_serializers.ProtoSerializer):
    choice_field: Annotated[serializers.ChoiceField, MyStrEnum] = serializers.ChoiceField(
        choices=MyStrEnum.choices,
    )

    class Meta:
        fields = "__all__"


class TestEnumGenerationPlugin(TestCase):
    def test_proto_enum_generation_from_field_dict(self):
        class MyService(GenericService):
            @grpc_action(
                request=[{"name": "enum", "type": MyIntEnum}],
                response=[{"name": "enum", "type": MyIntEnum}],
                use_generation_plugins=[InMessageEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyIntAction(self, request, context): ...

            @grpc_action(
                request=[{"name": "enum", "type": MyStrEnum}],
                response=[{"name": "enum", "type": MyStrEnum}],
                use_generation_plugins=[GlobalScopeEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyStrAction(self, request, context): ...

        proto_rpc_int = MyService.MyIntAction.make_proto_rpc("MyIntAction", MyService)

        assert proto_rpc_int.request["enum"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.request["enum"].field_type.wrap_in_message is False
        assert proto_rpc_int.request["enum"].field_type.enum == MyIntEnum
        assert proto_rpc_int.request["enum"].field_type.location == ProtoEnumLocations.MESSAGE

        assert proto_rpc_int.response["enum"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.response["enum"].field_type.wrap_in_message is False
        assert proto_rpc_int.response["enum"].field_type.enum == MyIntEnum
        assert proto_rpc_int.response["enum"].field_type.location == ProtoEnumLocations.MESSAGE

        proto_rpc_str = MyService.MyStrAction.make_proto_rpc("MyStrAction", MyService)

        assert proto_rpc_str.request["enum"].field_type.name == "MyStrEnum"
        assert proto_rpc_str.request["enum"].field_type.wrap_in_message is False
        assert proto_rpc_str.request["enum"].field_type.enum == MyStrEnum
        assert proto_rpc_str.request["enum"].field_type.location == ProtoEnumLocations.GLOBAL

        assert proto_rpc_str.response["enum"].field_type.name == "MyStrEnum"
        assert proto_rpc_str.response["enum"].field_type.wrap_in_message is False
        assert proto_rpc_str.response["enum"].field_type.enum == MyStrEnum
        assert proto_rpc_str.response["enum"].field_type.location == ProtoEnumLocations.GLOBAL

    def test_proto_enum_generation_from_annotated_model(self):
        class MyService(GenericService):
            @grpc_action(
                request=MyAnnotatedIntModelSerializer,
                response=MyAnnotatedIntModelSerializer,
                use_generation_plugins=[InMessageEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyIntAction(self, request, context): ...

            @grpc_action(
                request=MyAnnotatedStrModelSerializer,
                response=MyAnnotatedStrModelSerializer,
                use_generation_plugins=[InMessageWrappedEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyStrAction(self, request, context): ...

        proto_rpc_int = MyService.MyIntAction.make_proto_rpc("MyIntAction", MyService)

        assert proto_rpc_int.request["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.request["choice_field"].field_type.wrap_in_message is False
        assert proto_rpc_int.request["choice_field"].field_type.enum == MyIntEnum
        assert (
            proto_rpc_int.request["choice_field"].field_type.location
            == ProtoEnumLocations.MESSAGE
        )

        assert proto_rpc_int.response["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.response["choice_field"].field_type.wrap_in_message is False
        assert proto_rpc_int.response["choice_field"].field_type.enum == MyIntEnum
        assert (
            proto_rpc_int.response["choice_field"].field_type.location
            == ProtoEnumLocations.MESSAGE
        )

        proto_rpc_str = MyService.MyStrAction.make_proto_rpc("MyStrAction", MyService)

        assert proto_rpc_str.request["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.request["choice_field"].field_type.wrap_in_message is True
        assert proto_rpc_str.request["choice_field"].field_type.enum == MyStrEnum
        assert (
            proto_rpc_str.request["choice_field"].field_type.location
            == ProtoEnumLocations.MESSAGE
        )

        assert proto_rpc_str.response["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.response["choice_field"].field_type.wrap_in_message is True
        assert proto_rpc_str.response["choice_field"].field_type.enum == MyStrEnum
        assert (
            proto_rpc_str.response["choice_field"].field_type.location
            == ProtoEnumLocations.MESSAGE
        )

    def test_proto_enum_generation_from_annotated_serializer(self):
        class MyService(GenericService):
            @grpc_action(
                request=MyAnnotatedIntSerializer,
                response=MyAnnotatedIntSerializer,
                use_generation_plugins=[GlobalScopeEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyIntAction(self, request, context): ...

            @grpc_action(
                request=MyAnnotatedStrSerializer,
                response=MyAnnotatedStrSerializer,
                use_generation_plugins=[GlobalScopeWrappedEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyStrAction(self, request, context): ...

        proto_rpc_int = MyService.MyIntAction.make_proto_rpc("MyIntAction", MyService)

        assert proto_rpc_int.request["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.request["choice_field"].field_type.wrap_in_message is False
        assert proto_rpc_int.request["choice_field"].field_type.enum == MyIntEnum
        assert (
            proto_rpc_int.request["choice_field"].field_type.location
            == ProtoEnumLocations.GLOBAL
        )

        assert proto_rpc_int.response["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.response["choice_field"].field_type.wrap_in_message is False
        assert proto_rpc_int.response["choice_field"].field_type.enum == MyIntEnum
        assert (
            proto_rpc_int.response["choice_field"].field_type.location
            == ProtoEnumLocations.GLOBAL
        )

        proto_rpc_str = MyService.MyStrAction.make_proto_rpc("MyStrAction", MyService)

        assert proto_rpc_str.request["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.request["choice_field"].field_type.wrap_in_message is True
        assert proto_rpc_str.request["choice_field"].field_type.enum == MyStrEnum
        assert (
            proto_rpc_str.request["choice_field"].field_type.location
            == ProtoEnumLocations.GLOBAL
        )

        assert proto_rpc_str.response["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.response["choice_field"].field_type.wrap_in_message is True
        assert proto_rpc_str.response["choice_field"].field_type.enum == MyStrEnum
        assert (
            proto_rpc_str.response["choice_field"].field_type.location
            == ProtoEnumLocations.GLOBAL
        )

    def test_proto_enum_generation_from_annotated_serializer_in_partial_update(self):
        class MyService(GenericService):
            @grpc_action(
                request=get_partial_update_request_from_serializer_class(
                    MyAnnotatedIntSerializer
                ),
                response=MyAnnotatedIntSerializer,
                use_generation_plugins=[GlobalScopeEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyIntActionPartial(self, request, context): ...

            @grpc_action(
                request=get_partial_update_request_from_serializer_class(
                    MyAnnotatedStrSerializer
                ),
                response=MyAnnotatedStrSerializer,
                use_generation_plugins=[GlobalScopeWrappedEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyStrActionPartial(self, request, context): ...

        proto_rpc_int = MyService.MyIntActionPartial.make_proto_rpc(
            "MyIntActionPartial", MyService
        )

        assert proto_rpc_int.request["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.request["choice_field"].field_type.wrap_in_message is False
        assert proto_rpc_int.request["choice_field"].field_type.enum == MyIntEnum
        assert (
            proto_rpc_int.request["choice_field"].field_type.location
            == ProtoEnumLocations.GLOBAL
        )
        assert "_partial_update_fields" in proto_rpc_int.request

        assert proto_rpc_int.response["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.response["choice_field"].field_type.wrap_in_message is False
        assert proto_rpc_int.response["choice_field"].field_type.enum == MyIntEnum
        assert (
            proto_rpc_int.response["choice_field"].field_type.location
            == ProtoEnumLocations.GLOBAL
        )

        proto_rpc_str = MyService.MyStrActionPartial.make_proto_rpc(
            "MyStrActionPartial", MyService
        )

        assert proto_rpc_str.request["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.request["choice_field"].field_type.wrap_in_message is True
        assert proto_rpc_str.request["choice_field"].field_type.enum == MyStrEnum
        assert (
            proto_rpc_str.request["choice_field"].field_type.location
            == ProtoEnumLocations.GLOBAL
        )
        assert "_partial_update_fields" in proto_rpc_str.request

        assert proto_rpc_str.response["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.response["choice_field"].field_type.wrap_in_message is True
        assert proto_rpc_str.response["choice_field"].field_type.enum == MyStrEnum
        assert (
            proto_rpc_str.response["choice_field"].field_type.location
            == ProtoEnumLocations.GLOBAL
        )

    def test_proto_enum_generation_from_non_annotated_model(self):
        class MyService(GenericService):
            @grpc_action(
                request=MyStrModelSerializer,
                response=MyStrModelSerializer,
                use_generation_plugins=[
                    InMessageEnumGenerationPlugin(non_annotated_generation=True)
                ],
                override_default_generation_plugins=True,
            )
            async def MyStrAction(self, request, context): ...

        proto_rpc_str = MyService.MyStrAction.make_proto_rpc("MyStrAction", MyService)

        assert (
            proto_rpc_str.request["choice_field"].field_type.name
            == "MyStrModelChoiceFieldEnum"
        )
        assert proto_rpc_str.request["choice_field"].field_type.wrap_in_message is False
        assert (
            proto_rpc_str.request["choice_field"].field_type.location
            == ProtoEnumLocations.MESSAGE
        )
        assert "VALUE_1" in proto_rpc_str.request["choice_field"].field_type.enum.__members__

        assert (
            proto_rpc_str.response["choice_field"].field_type.name
            == "MyStrModelChoiceFieldEnum"
        )
        assert proto_rpc_str.response["choice_field"].field_type.wrap_in_message is False
        assert (
            proto_rpc_str.response["choice_field"].field_type.location
            == ProtoEnumLocations.MESSAGE
        )
        assert "VALUE_1" in proto_rpc_str.response["choice_field"].field_type.enum.__members__

    def test_non_annotated_generation_false(self):
        class MyService(GenericService):
            @grpc_action(
                request=MyStrModelSerializer,
                response=MyStrModelSerializer,
                use_generation_plugins=[InMessageEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyStrAction(self, request, context): ...

        proto_rpc_str = MyService.MyStrAction.make_proto_rpc("MyStrAction", MyService)

        assert proto_rpc_str.request["choice_field"].field_type == "string"
        assert proto_rpc_str.response["choice_field"].field_type == "string"

    def test_proto_enum_generation_raises_error_on_wrong_annotation(self):
        class MyService(GenericService):
            @grpc_action(
                request=MyWronglyAnnotatedIntModelSerializer,
                response=MyWronglyAnnotatedIntModelSerializer,
                use_generation_plugins=[GlobalScopeEnumGenerationPlugin()],
                override_default_generation_plugins=True,
            )
            async def MyIntAction(self, request, context): ...

        with self.assertRaises(ProtoRegistrationError):
            MyService.MyIntAction.make_proto_rpc("MyIntAction", MyService)
