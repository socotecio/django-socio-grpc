import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from django.db import models
from rest_framework import serializers

from django_socio_grpc.protobuf.exceptions import ProtoRegistrationError
from django_socio_grpc.protobuf.message_name_constructor import MessageNameConstructor
from django_socio_grpc.protobuf.proto_classes import (
    FieldCardinality,
    ProtoEnum,
    ProtoField,
    ProtoMessage,
)
from django_socio_grpc.protobuf.registry_singleton import RegistrySingleton

if TYPE_CHECKING:
    from django_socio_grpc.services import Service

logger = logging.getLogger("django_socio_grpc.generation")


class BaseGenerationPlugin:
    """
    The base class to create generation plugins.
    """

    def check_condition(
        self,
        service: type["Service"],
        request_message: ProtoMessage | str,
        response_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> bool:
        """
        Method that allow to return without modifying the proto if some conditions are not met
        """
        return True

    def transform_request_message(
        self,
        service: type["Service"],
        proto_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        """
        The actual method that transform the request ProtoMessage
        """
        return proto_message

    def transform_response_message(
        self,
        service: type["Service"],
        proto_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        """
        The actual method that transform the response ProtoMessage
        """
        return proto_message

    def run_validation_and_transform(
        self,
        service: type["Service"],
        request_message: ProtoMessage | str,
        response_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> tuple[ProtoMessage, ProtoMessage]:
        """
        The main orchestrator method of the plugin. This is the first entrypoint.
        It check the confition setted by check_condition method and then call transform_request_message and transform_response_message
        """
        if not self.check_condition(
            service, request_message, response_message, message_name_constructor
        ):
            return request_message, response_message

        return self.transform_request_message(
            service, request_message, message_name_constructor
        ), self.transform_response_message(service, response_message, message_name_constructor)


class BaseAddFieldRequestGenerationPlugin(BaseGenerationPlugin):
    """
    Util class to inherit for adding a field in a request proto message.
    By inerhit it and fill field_name, field_cardinality and field_type it will create a plugin that add a field without having to override any method.
    """

    field_name: str
    field_type: str | ProtoMessage
    field_cardinality: FieldCardinality

    def __init__(self, *args, **kwargs):
        error_message = "You try to instanciate a class that inherit from BaseGenerationPlugin. to do that you need to specify a {0} attribute"

        assert self.field_name is not None, error_message.format("field_name")
        assert self.field_cardinality is not None, error_message.format("field_cardinality")
        assert self.field_type is not None, error_message.format("field_type")

    def transform_request_message(
        self,
        service: type["Service"],
        proto_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ):
        if isinstance(proto_message, str):
            logger.warning(
                f"Plugin {self.__class__.__name__} can't be used with a string message. Please use the plugin directly on the grpc_action that generate the message"
            )
        proto_message.fields.append(
            ProtoField.from_field_dict(
                {
                    "name": self.field_name,
                    "type": self.field_type,
                    "cardinality": self.field_cardinality,
                }
            )
        )
        return proto_message


class FilterGenerationPlugin(BaseAddFieldRequestGenerationPlugin):
    """
    Plugin to add the _filters field in the request ProtoMessage. See https://django-socio-grpc.readthedocs.io/en/stable/features/filters.html#djangofilterbackend
    """

    field_name: str = "_filters"
    field_type: str | ProtoMessage = "google.protobuf.Struct"
    field_cardinality: FieldCardinality = FieldCardinality.OPTIONAL

    def __init__(self, display_warning_message=True):
        self.display_warning_message = display_warning_message
        super().__init__()

    def check_condition(
        self,
        service: type["Service"],
        request_message: ProtoMessage | str,
        response_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> bool:
        from django_socio_grpc.settings import (
            FilterAndPaginationBehaviorOptions,
            grpc_settings,
        )

        # INFO - AM - 20/02/2024 - If service don't support filtering we do not add filter field
        if (
            not hasattr(service, "filter_backends")
            or not service.filter_backends
            and not grpc_settings.DEFAULT_FILTER_BACKENDS
        ):
            if self.display_warning_message:
                logger.warning(
                    "You are using FilterGenerationPlugin but no filter_backends as been found on the service. Please set a filter_backends in the service or set it globally with DEFAULT_FILTER_BACKENDS setting."
                )
            return False

        if grpc_settings.FILTER_BEHAVIOR == FilterAndPaginationBehaviorOptions.METADATA_STRICT:
            if self.display_warning_message:
                logger.warning(
                    "You are using FilterGenerationPlugin but FILTER_BEHAVIOR settings is set to 'METADATA_STRICT' so it will have no effect. Please change FILTER_BEHAVIOR."
                )
            return False

        return True


class PaginationGenerationPlugin(BaseAddFieldRequestGenerationPlugin):
    """
    Plugin to add the _pagination field in the request ProtoMessage. See https://django-socio-grpc.readthedocs.io/en/stable/features/pagination.html
    """

    field_name: str = "_pagination"
    field_type: str | ProtoMessage = "google.protobuf.Struct"
    field_cardinality: FieldCardinality = FieldCardinality.OPTIONAL

    def __init__(self, display_warning_message=True):
        self.display_warning_message = display_warning_message
        super().__init__()

    def check_condition(
        self,
        service: type["Service"],
        request_message: ProtoMessage | str,
        response_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> bool:
        from django_socio_grpc.settings import (
            FilterAndPaginationBehaviorOptions,
            grpc_settings,
        )

        # INFO - AM - 20/02/2024 - If service don't support filtering we do not add filter field
        if (
            not hasattr(service, "pagination_class")
            or not service.pagination_class
            and not grpc_settings.DEFAULT_PAGINATION_CLASS
        ):
            if self.display_warning_message:
                logger.warning(
                    "You are using PaginationGenerationPlugin but no pagination_class as been found on the service. Please set a pagination_class in the service or set it globally with DEFAULT_PAGINATION_CLASS setting."
                )
            return False

        if (
            grpc_settings.PAGINATION_BEHAVIOR
            == FilterAndPaginationBehaviorOptions.METADATA_STRICT
        ):
            if self.display_warning_message:
                logger.warning(
                    "You are using PaginationGenerationPlugin but PAGINATION_BEHAVIOR settings is set to 'METADATA_STRICT' so it will have no effect. Please change PAGINATION_BEHAVIOR."
                )
            return False

        return True


@dataclass
class AsListGenerationPlugin(BaseGenerationPlugin):
    """
    Plugin allowing to encapsulate a message into an other message and put it as a repeated field to return multiple instance.
    Do not use directly, use one of it's subclass RequestAsListGenerationPlugin, ResponseAsListGenerationPlugin or RequestAndResponseAsListGenerationPlugin
    """

    list_field_name: str = "results"

    def transform_message_to_list(
        self, service: type["Service"], proto_message: ProtoMessage | str, list_name: str
    ) -> ProtoMessage:
        try:
            list_field_name = proto_message.serializer.Meta.message_list_attr
        except AttributeError:
            list_field_name = self.list_field_name

        fields = [
            ProtoField(
                name=list_field_name,
                field_type=proto_message,
                cardinality=FieldCardinality.REPEATED,
            ),
        ]

        if getattr(service, "pagination_class", None):
            fields.append(
                ProtoField(
                    name="count",
                    field_type="int32",
                )
            )

        list_message = ProtoMessage(
            name=list_name,
            fields=fields,
        )

        # INFO - AM - If the original proto message is a serializer then we keep the comment at the serializer level. Else we put them at the list level
        if not isinstance(proto_message, str) and not proto_message.serializer:
            list_message.comments = proto_message.comments
            proto_message.comments = None

        return list_message


class RequestAsListGenerationPlugin(AsListGenerationPlugin):
    """
    Transform a request ProtoMessage in a list ProtoMessage
    """

    def transform_request_message(
        self,
        service: type["Service"],
        proto_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        list_name = message_name_constructor.construct_request_list_name()
        return self.transform_message_to_list(service, proto_message, list_name)


class ResponseAsListGenerationPlugin(AsListGenerationPlugin):
    """
    Transform a response ProtoMessage in a list ProtoMessage
    """

    def transform_response_message(
        self,
        service: type["Service"],
        proto_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        list_name = message_name_constructor.construct_response_list_name()
        return self.transform_message_to_list(service, proto_message, list_name)


class RequestAndResponseAsListGenerationPlugin(
    RequestAsListGenerationPlugin, ResponseAsListGenerationPlugin
):
    """
    Transform both request and response ProtoMessage in list ProtoMessage
    """

    ...


@dataclass
class ListGenerationPlugin(RequestAsListGenerationPlugin, ResponseAsListGenerationPlugin):
    """
    Transform both request and response ProtoMessage in list ProtoMessage
    """

    request: bool = False
    response: bool = False

    def transform_response_message(
        self,
        service: type["Service"],
        proto_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        if self.response:
            return super().transform_response_message(
                service, proto_message, message_name_constructor
            )
        return proto_message

    def transform_request_message(
        self,
        service: type["Service"],
        proto_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        if self.request:
            return super().transform_request_message(
                service, proto_message, message_name_constructor
            )
        return proto_message


@dataclass
class BaseEnumGenerationPlugin(BaseGenerationPlugin):
    only_generate_non_annotated_for_new_fields: bool = True

    def transform_request_message(
        self,
        service: type["Service"],
        proto_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ):
        if isinstance(proto_message, str):
            return proto_message

        if proto_message.serializer is None:
            return self.handle_field_dict(proto_message, service)
        else:
            return self.handle_serializer(proto_message, service)

    def handle_serializer(self, proto_message: ProtoMessage, service: type["Service"]):
        """Handle enum generation for a ProtoMessage that has a serializer.

        An enum can be generated either from:
        - An Annotated Enum (e.g. Annotated[models.CharField, MyTextChoices])
        - A ChoiceField with string choices (e.g. ["CHOICE_1", "CHOICE_2"])

        For enumerations built from choices, the setting "only_generate_non_annotated_for_new_fields"
        will allow to skip existing fields that were not enums, and keep them as a String, to prevent breaking changes.
        """

        if app_handler := service._app_handler:
            proto_file = app_handler.proto_file

            # No proto_file or message not existing : all fields are considered new
            if (proto_file is None) or (proto_message.name not in proto_file.messages):
                previous_fields_names_to_field = {}
            # Else, we get the previous message fields
            else:
                previous_message = proto_file.messages[proto_message.name]
                previous_fields_names_to_field = {
                    field.name: field for field in previous_message.fields
                }

        # Find serializer fields that contain enums
        field_name_to_type: dict[str:Enum] = {}
        for field_name, field_instance in proto_message.serializer().fields.items():
            if not isinstance(field_instance, serializers.ChoiceField):
                continue

            # Try to get the previous field type in the proto file
            previous_proto_key_type = None
            if field_name in previous_fields_names_to_field:
                previous_proto_key_type = previous_fields_names_to_field[field_name].key_type

            if enum := self.get_enum_from_choice_field(
                field_instance, previous_proto_key_type
            ):
                field_name_to_type[field_name] = enum

        # Map ProtoMessage fields to serializer fields, and handle enums
        for field in proto_message.fields:
            if field.name not in field_name_to_type:
                continue

            self.handle_enum(service, proto_message, field, field_name_to_type[field.name])

        return proto_message

    def handle_field_dict(self, proto_message: ProtoMessage, service: type["Service"]):
        for field in proto_message.fields:
            if isinstance(field.field_type, type) and issubclass(field.field_type, Enum):
                self.handle_enum(service, proto_message, field, field.field_type)
        return proto_message

    def transform_response_message(
        self,
        service: type["Service"],
        proto_message: ProtoMessage | str,
        message_name_constructor: MessageNameConstructor,
    ) -> ProtoMessage:
        return self.transform_request_message(service, proto_message, message_name_constructor)

    def handle_enum(
        self, service: type["Service"], proto_message: ProtoMessage, field: ProtoField, enum: Enum
    ):
        raise NotImplementedError("You need to implement the handle_enum method")

    def choice_field_contain_buildable_enum(self, field: serializers.ChoiceField) -> bool:
        # Skip all non string choices (e.g. IntegerChoices)
        if not isinstance(list(field.choices)[0], str):
            return False

        is_enum = True
        for k in field.choices:
            if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*", k):
                is_enum = False
                break
        return is_enum

    def check_annotated_enum_coherence(self, enum: Enum, field: serializers.ChoiceField):
        # Check if the annotated enum is a subclass of models.IntegerChoices or models.TextChoices
        if not issubclass(enum, models.IntegerChoices) and not issubclass(
            enum, models.TextChoices
        ):
            raise ProtoRegistrationError(
                f"Choice ({field.field_name}) field should be annotated with a class that is a subclass of models.IntegerChoices or models.TextChoices."
            )

        # Check for coherence between the choices and the annotated enum
        if set(field.choices) != set(enum.values):
            raise ProtoRegistrationError(
                f"Choice ({field.field_name}) field should be annotated with the same class as the choices, either on the serializer or the model.\n"
                "Example : `my_field : Annotated[models.CharField, MyTextChoices] = models.CharField(choices=MyTextChoices)`"
            )

    def build_enum_from_choice_field(self, field: serializers.ChoiceField):
        choices = field.choices

        # Build Enum name (SerializerName + FieldName + "Enum")
        serializer_name = field.parent.__class__.__name__
        if serializer_name.endswith("Serializer"):
            serializer_name = serializer_name[:-10]
        field_name_pascal_case = field.field_name.replace("_", " ").title().replace(" ", "")
        enum_name = f"{serializer_name}{field_name_pascal_case}Enum"

        return models.TextChoices(enum_name, choices)

    def get_enum_from_choice_field(
        self, field: serializers.ChoiceField, previous_proto_key_type: str | None
    ) -> Enum | None:
        # First we try to get the enum from the annotation
        enum = ProtoEnum.get_enum_from_annotation(field)

        # If we didn't get the enum from annotation
        # And if we only build enums for new fields, we have to skip existing fields that are not enums
        if (
            enum is None
            and self.only_generate_non_annotated_for_new_fields
            and previous_proto_key_type == "string"
        ):
            return None

        # handle annotated enums coherence checks
        if enum is not None:
            self.check_annotated_enum_coherence(enum, field)
        # If we don't have an annotated enum, we build an enum from the choices
        elif self.choice_field_contain_buildable_enum(field):
            enum = self.build_enum_from_choice_field(field)

        return enum


@dataclass
class InMessageEnumGenerationPlugin(BaseEnumGenerationPlugin):
    def handle_enum(
        self, service: type["Service"], proto_message: ProtoMessage, field: ProtoField, enum: Enum
    ):
        field.field_type = ProtoEnum(enum, False, enum.__name__)
        proto_message.proto_extra_tools.enums.append(field.field_type)

@dataclass
class InMessageWrappedEnumGenerationPlugin(BaseEnumGenerationPlugin):
    def handle_enum(
        self, service: type["Service"], proto_message: ProtoMessage, field: ProtoField, enum: Enum
    ):
        field.field_type = ProtoEnum(enum, True, f"{enum.__name__}.Enum")
        proto_message.proto_extra_tools.enums.append(field.field_type)


@dataclass
class GlobalScopeEnumGenerationPlugin(BaseEnumGenerationPlugin):
    def handle_enum(
        self, service: type["Service"], proto_message: ProtoMessage, field: ProtoField, enum: Enum
    ):
        field.field_type = ProtoEnum(enum, False, enum.__name__)
        service._app_handler.proto_extra_tools.enums.append(field.field_type)
        field.field_type_str = f"{field.field_type.__name__}"


@dataclass
class GlobalScopeWrappedEnumGenerationPlugin(BaseEnumGenerationPlugin):
    def handle_enum(
        self, service: type["Service"], proto_message: ProtoMessage, field: ProtoField, enum: Enum
    ):
        field.field_type = ProtoEnum(enum, True, f"{enum.__name__}.Enum")
        service._app_handler.proto_extra_tools.enums.append(field.field_type)