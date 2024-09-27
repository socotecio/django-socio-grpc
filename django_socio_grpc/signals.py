from django.dispatch import Signal

# INFO - AM - 22/08/2024 - grpc_action_register is a signal send for each grpc action when the grpc action is registered. Each grpc action need to be registered to generate proto. It allow us to make action as registration or cache deleter signals as this features need the name of the service
grpc_action_register = Signal()
