from google.protobuf.pyext.cpp_message import GeneratedProtocolMessageType


def assert_method_didnt_exist(methods_names: set, name: str, all_attributes: dict) -> None:
    intersect = methods_names.intersection(set(all_attributes.keys()))
    assert (
        not intersect
    ), f"Method(s) {', '.join(list(intersect))} will be automatically implement by\
        'SocioGlobalsServiceFactory'. Don't implement it yourself in {name} or they will be overrided."


class SocioGlobalsServiceFactory(type):
    """
    Metaclass used as a factory for building Class used as
    namespaced model constants variables.
    """

    default_protobuff_map_attribute = "value"
    metaclass_method_definition = set(
        ["avaible_choices", "get_as_choices", "get_as_message", "get_as_service"]
    )

    def __new__(cls, *args, **kwargs):
        name, parents, attributes = args[0], args[1], args[2]
        # Check user contract: no inheritance (unexpected method definition or overriding),
        # no reserved method definition.
        assert not parents, "'SocioGlobalsServiceFactory' type doesn't support inheritance."
        assert_method_didnt_exist(
            SocioGlobalsServiceFactory.metaclass_method_definition, name, attributes
        )

        # Get user defined class attributes
        attributes["avaible_choices"] = {
            attr_name: value
            for attr_name, value in attributes.items()
            if isinstance(value, str) and not attr_name.startswith("__")
        }
        # Building classmethods

        # If user have no defined meta: we create it.
        future_cls_meta = attributes.get("Meta", False)
        assert getattr(
            future_cls_meta, "service_pb2", False
        ), f"'{name}' class must define a Meta with at least `service_pb2` wich contains your grpc module ie. `myapp.grpc.myapp_pb2`"
        print(dir(future_cls_meta))
        # Extract customs from class Meta
        proto_message_name = getattr(future_cls_meta, "proto_message_name", None) or f"{name}"
        protobuff_map_attribute_name = (
            getattr(future_cls_meta, "protobuff_map_attribute_name", False)
            or SocioGlobalsServiceFactory.default_protobuff_map_attribute
        )
        service_method = getattr(future_cls_meta, "service_method_name", None) or f"List{name}"
        service_request = getattr(future_cls_meta, "service_request", None) or {
            "is_stream": False,
            "message": f"{proto_message_name}",
        }
        service_response = getattr(future_cls_meta, "service_response", None) or {
            "is_stream": False,
            "message": f"{proto_message_name}",
        }
        # Record attributes below as private attributes.
        attributes["_proto_message_name"] = proto_message_name
        attributes["_protobuff_map_attribute_name"] = protobuff_map_attribute_name
        attributes["_service_method"] = service_method
        attributes["_service_request"] = service_request
        attributes["_service_response"] = service_response

        # Define proto map attribute name and proto methods
        attributes["get_as_message"] = classmethod(SocioGlobalsServiceFactory.get_as_message)
        attributes["get_as_method"] = classmethod(SocioGlobalsServiceFactory.get_as_method)
        attributes["get_as_service"] = classmethod(SocioGlobalsServiceFactory.get_as_service)
        # Get as choite classmethod
        get_as_choices_method = lambda x: tuple(x.avaible_choices.items())
        attributes["get_as_choices"] = classmethod(get_as_choices_method)
        return type(name, (), attributes)

    def get_as_message(future_cls):
        """
        Build message expected on `grpc_messages` in the Model.
        """

        proto_message_definition = {
            future_cls._proto_message_name: [
                "__custom__map<string, string>__{}__".format(
                    future_cls._protobuff_map_attribute_name
                )
            ]
        }
        return proto_message_definition

    def get_as_choices(future_cls) -> tuple:
        """
        Return tuple for the CharField choices `params`.
        """
        return tuple(future_cls.avaible_choices.items())

    def get_as_service(future_cls) -> GeneratedProtocolMessageType:
        """
        Return a Message that can be used in ModelService
        """
        proto_message = getattr(future_cls.Meta.service_pb2, future_cls._proto_message_name)()
        for key, value in future_cls.avaible_choices.items():
            proto_message.value[key] = value
        return proto_message

    def get_as_method(future_cls) -> dict:
        """
        Build dict expected on `grpc_methods` in the Model. 
        """
        return {
            future_cls._service_method: {
                "request": future_cls._service_request,
                "response": future_cls._service_response,
            }
        }
