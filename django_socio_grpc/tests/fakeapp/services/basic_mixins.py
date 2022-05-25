
from django_socio_grpc.decorators import grpc_action
from django_socio_grpc.grpc_action import GRPCActionMixin
from typing import Any, Dict, Optional

# class TokenMessage:
#     def __init__(self, token_name, name, _type):
#         self.name = name
#         self._type = _type
#         self.token_name = token_name

# ListIds.grpc_dict()

class ListIds(GRPCActionMixin, abstract=True):

    def _grpc_action_registry(service) -> Dict[str, Dict[str, Any]]:
        return {
            "FetchDataForUser": {
                "request":[],
                "response":[{"name": "user_name", "type": "string"}]
            }
        }
    
    # @grpc_action(
    #     request=[],
    #     response=[{"name": "user_name", "type": "string"}]
    # )
    async def FetchDataForUser(self, request, context):
      pass

    # def action_registry(cls, service_class=None):
    #     if not service_class:
    #         service_class = cls
    #     registry = {}
    #     for parent in cls._action_parents[::-1]:
    #         if "grpc_dict" in parent.__dict__:
    #             registry.update(parent.grpc_dict(service_class))

    #     return registry

    # @property
    # def _action_parents(cls):
    #     return [base for base in cls.mro() if issubclass(type(base), ActionMeta)]

    
    
    # def grpc_dict(service):
    #     return {
    #         **service._grpc_dict_from_decorators
    #     }

    # _grpc_dict_from_decorators = {}
    
    # def __init_subclass__(cls, abstract=False) -> None:

    #     # for function_name, grpc_data in cls.grpc_dict(cls):
    #     print(cls)
    #     print(cls.__module__)
    #     # print(dir(cls))

    #     attr_name = "FetchDataForUser"
    #     grpc_action_instance = getattr(cls, attr_name)

    #     print(grpc_action_instance)
    #     print(id(grpc_action_instance))


        # grpc_action_instance.__set_name__(cls, attr_name)

        
        # if not abstract:
        #     for attr_name in dir(cls):
        #         attr = getattr(cls, attr_name)
        #         try:
        #             print("lala", attr_name)
        #             attr.__set_name__(cls, attr_name)
        #             print("lala", attr_name)

        #             # grpc_action(**cls.grpc_dict)(cls.FetchDataForUser).__set_name__()

        #         except Exception:
        #             pass



