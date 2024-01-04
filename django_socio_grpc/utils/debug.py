from django_socio_grpc.protobuf.registry_singleton import SingletonMeta

"""
Example of usage:

from django_socio_grpc.utils.constants import REQUEST_SUFFIX, RESPONSE_SUFFIX

ENABLE_PROTO_DEBUG = True
SERVICE_TO_DEBUG = "RelatedFieldModelService"
ACTION_TO_DEBUG = "Retrieve"
PREFIX_TO_DEBUG = "RelatedFieldModel"
SUFFIX_TO_DEBUG = RESPONSE_SUFFIX
FIELD_TO_DEBUG = "many_many"
"""
ENABLE_PROTO_DEBUG = False
SERVICE_TO_DEBUG = ""
ACTION_TO_DEBUG = ""
PREFIX_TO_DEBUG = ""
SUFFIX_TO_DEBUG = ""
FIELD_TO_DEBUG = ""


class ProtoGeneratorPrintHelper(metaclass=SingletonMeta):
    service_name: str = ""
    action_name: str = ""
    prefix: str = ""
    # INFO recursive import event if TYPE_CHECKING
    # message_class: Type[ProtoMessage] | None
    message_class = None
    field_name: str = ""

    @classmethod
    def reset(cls):
        cls.service_name = ""
        cls.action_name = ""
        cls.prefix = ""
        cls.message_class = None
        cls.field_name = ""

    @classmethod
    def set_service_and_action(cls, service_name: str, action_name: str):
        cls.service_name = service_name
        cls.action_name = action_name

    @classmethod
    def set_info_proto_message(cls, prefix: str, message_class):
        """
        message_class: Type[ProtoMessage]
        """
        cls.prefix = prefix
        cls.message_class = message_class

    @classmethod
    def set_field_name(cls, field_name: str):
        cls.field_name = field_name

    @classmethod
    def print(cls, *args, **kwargs):
        if not ENABLE_PROTO_DEBUG:
            return
        if (
            cls.check_service()
            and cls.check_prefix()
            and cls.check_message_suffix()
            and cls.check_action_name()
            and cls.check_field_name()
        ):
            print(*args, **kwargs)

    @classmethod
    def check_service(cls):
        # INFO - AM - 29/12/2023 - if dev not specified the element to debug we dispaly all
        # If code as not yet registered the element we display all too
        if not SERVICE_TO_DEBUG or not cls.service_name:
            return True
        return cls.service_name == SERVICE_TO_DEBUG

    @classmethod
    def check_prefix(cls):
        # INFO - AM - 29/12/2023 - if dev not specified the element to debug we dispaly all
        # If code as not yet registered the element we display all too
        if not PREFIX_TO_DEBUG or not cls.prefix:
            return True
        return cls.prefix == PREFIX_TO_DEBUG

    @classmethod
    def check_message_suffix(cls):
        # INFO - AM - 29/12/2023 - if dev not specified the element to debug we dispaly all
        # If code as not yet registered the element we display all too
        if not SUFFIX_TO_DEBUG or not cls.message_class:
            return True
        return cls.message_class.suffix == SUFFIX_TO_DEBUG

    @classmethod
    def check_action_name(cls):
        # INFO - AM - 29/12/2023 - if dev not specified the element to debug we dispaly all
        # If code as not yet registered the element we display all too
        if not ACTION_TO_DEBUG or not cls.action_name:
            return True
        return cls.action_name == ACTION_TO_DEBUG

    @classmethod
    def check_field_name(cls):
        # INFO - AM - 29/12/2023 - if dev not specified the element to debug we dispaly all
        # If code as not yet registered the element we display all too
        if not FIELD_TO_DEBUG or not cls.field_name:
            return True
        return cls.field_name == FIELD_TO_DEBUG
