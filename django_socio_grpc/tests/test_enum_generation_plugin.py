from typing import Annotated
from django.test import TestCase

from django_socio_grpc import proto_serializers
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.generics import GenericService
from django_socio_grpc.protobuf.exceptions import ProtoRegistrationError
from django_socio_grpc.protobuf.generation_plugin import GlobalScopeEnumGenerationPlugin, GlobalScopeWrappedEnumGenerationPlugin
from django_socio_grpc.protobuf.registry_singleton import RegistrySingleton
from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
from django.db import models
from rest_framework import serializers

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
    VALUE_3 : Annotated[str, "My comment"] = "VALUE_3"

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
    def setUp(self):
        RegistrySingleton().clean_all()
        AppHandlerRegistry(app_name="fakeapp", server=None)
    
    def test_proto_enum_generation_from_field_dict(self):
        class MyService(GenericService):
            @grpc_action(
                request=[{"name": "enum", "type": MyIntEnum}],
                response=[{"name": "enum", "type": MyIntEnum}],
                use_generation_plugins=[GlobalScopeEnumGenerationPlugin()],
            )
            async def MyIntAction(self, request, context): ...
            
                        
            @grpc_action(
                request=[{"name": "enum", "type": MyStrEnum}],
                response=[{"name": "enum", "type": MyStrEnum}],
                use_generation_plugins=[GlobalScopeWrappedEnumGenerationPlugin()],
            )
            async def MyStrAction(self, request, context): ...
                    
        fakeapp_handler_registry = RegistrySingleton().registered_apps["fakeapp"]
        fakeapp_handler_registry.register(MyService)
        
        
        proto_rpc_int = fakeapp_handler_registry.proto_services[0].rpcs[0]
        
        assert proto_rpc_int.request["enum"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.request["enum"].field_type.wrap_in_message == False
        assert proto_rpc_int.request["enum"].field_type.enum == MyIntEnum
        
        assert proto_rpc_int.response["enum"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.response["enum"].field_type.wrap_in_message == False
        assert proto_rpc_int.response["enum"].field_type.enum == MyIntEnum
        
        proto_rpc_str = fakeapp_handler_registry.proto_services[0].rpcs[1]
        
        assert proto_rpc_str.request["enum"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.request["enum"].field_type.wrap_in_message == True
        assert proto_rpc_str.request["enum"].field_type.enum == MyStrEnum
        
        assert proto_rpc_str.response["enum"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.response["enum"].field_type.wrap_in_message == True
        assert proto_rpc_str.response["enum"].field_type.enum == MyStrEnum
         
    def test_proto_enum_generation_from_annotated_model(self):
        class MyService(GenericService):
             
            @grpc_action(
                request=MyAnnotatedIntModelSerializer,
                response=MyAnnotatedIntModelSerializer,
                use_generation_plugins=[GlobalScopeEnumGenerationPlugin()],
            )
            async def MyIntAction(self, request, context): ...
            
            @grpc_action(
                request=MyAnnotatedStrModelSerializer,
                response=MyAnnotatedStrModelSerializer,
                use_generation_plugins=[GlobalScopeWrappedEnumGenerationPlugin()],
            )
            async def MyStrAction(self, request, context): ...
            

        fakeapp_handler_registry = RegistrySingleton().registered_apps["fakeapp"]
        fakeapp_handler_registry.register(MyService)
        
        proto_rpc_int = fakeapp_handler_registry.proto_services[0].rpcs[0]
        
        assert proto_rpc_int.request["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.request["choice_field"].field_type.wrap_in_message == False
        assert proto_rpc_int.request["choice_field"].field_type.enum == MyIntEnum
        
        assert proto_rpc_int.response["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.response["choice_field"].field_type.wrap_in_message == False
        assert proto_rpc_int.response["choice_field"].field_type.enum == MyIntEnum
        
        proto_rpc_str = fakeapp_handler_registry.proto_services[0].rpcs[1]
        
        assert proto_rpc_str.request["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.request["choice_field"].field_type.wrap_in_message == True
        assert proto_rpc_str.request["choice_field"].field_type.enum == MyStrEnum
        
        assert proto_rpc_str.response["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.response["choice_field"].field_type.wrap_in_message == True
        assert proto_rpc_str.response["choice_field"].field_type.enum == MyStrEnum

    def test_proto_enum_generation_from_annotated_serializer(self):
        class MyService(GenericService):
             
            @grpc_action(
                request=MyAnnotatedIntSerializer,
                response=MyAnnotatedIntSerializer,
                use_generation_plugins=[GlobalScopeEnumGenerationPlugin()],
            )
            async def MyIntAction(self, request, context): ...
            
            @grpc_action(
                request=MyAnnotatedStrSerializer,
                response=MyAnnotatedStrSerializer,
                use_generation_plugins=[GlobalScopeWrappedEnumGenerationPlugin()],
            )
            async def MyStrAction(self, request, context): ...
            

        fakeapp_handler_registry = RegistrySingleton().registered_apps["fakeapp"]
        fakeapp_handler_registry.register(MyService)
        
        proto_rpc_int = fakeapp_handler_registry.proto_services[0].rpcs[0]
        
        assert proto_rpc_int.request["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.request["choice_field"].field_type.wrap_in_message == False
        assert proto_rpc_int.request["choice_field"].field_type.enum == MyIntEnum
        
        assert proto_rpc_int.response["choice_field"].field_type.name == "MyIntEnum"
        assert proto_rpc_int.response["choice_field"].field_type.wrap_in_message == False
        assert proto_rpc_int.response["choice_field"].field_type.enum == MyIntEnum
        
        proto_rpc_str = fakeapp_handler_registry.proto_services[0].rpcs[1]
        
        assert proto_rpc_str.request["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.request["choice_field"].field_type.wrap_in_message == True
        assert proto_rpc_str.request["choice_field"].field_type.enum == MyStrEnum
        
        assert proto_rpc_str.response["choice_field"].field_type.name == "MyStrEnum.Enum"
        assert proto_rpc_str.response["choice_field"].field_type.wrap_in_message == True
        assert proto_rpc_str.response["choice_field"].field_type.enum == MyStrEnum
        
    def test_proto_enum_generation_from_non_annotated_model(self):
        class MyService(GenericService):
             
            @grpc_action(
                request=MyStrModelSerializer,
                response=MyStrModelSerializer,
                use_generation_plugins=[GlobalScopeEnumGenerationPlugin()],
            )
            async def MyStrAction(self, request, context): ...
        
        fakeapp_handler_registry = RegistrySingleton().registered_apps["fakeapp"]
        fakeapp_handler_registry.register(MyService)
        
        proto_rpc_str = fakeapp_handler_registry.proto_services[0].rpcs[0]
        
        assert proto_rpc_str.request["choice_field"].field_type.name == "MyStrModelChoiceFieldEnum"
        assert proto_rpc_str.request["choice_field"].field_type.wrap_in_message == False
        assert "VALUE_1" in proto_rpc_str.request["choice_field"].field_type.enum.__members__
        
        assert proto_rpc_str.response["choice_field"].field_type.name == "MyStrModelChoiceFieldEnum"
        assert proto_rpc_str.response["choice_field"].field_type.wrap_in_message == False
        assert "VALUE_1" in proto_rpc_str.response["choice_field"].field_type.enum.__members__

    def test_proto_enum_generation_raises_error_on_wrong_annotation(self):
        class MyService(GenericService):
             
            @grpc_action(
                request=MyWronglyAnnotatedIntModelSerializer,
                response=MyWronglyAnnotatedIntModelSerializer,
                use_generation_plugins=[GlobalScopeEnumGenerationPlugin()],
            )
            async def MyIntAction(self, request, context): ...
        
        fakeapp_handler_registry = RegistrySingleton().registered_apps["fakeapp"]
        
        with self.assertRaises(ProtoRegistrationError):
            fakeapp_handler_registry.register(MyService)