import django
from asgiref.sync import sync_to_async
from django.dispatch import Signal

if django.VERSION < (5, 0):

    class Signal(Signal):
        async def asend(self, *args, **kwargs):
            return sync_to_async(super().send)(*args, **kwargs)


# INFO - AM - 22/08/2024 - grpc_action_register is a signal send for each grpc action when the grpc action is registered. Each grpc action need to be registered to generate proto. It allow us to make action as registration or cache deleter signals as this features need the name of the service
grpc_action_register = Signal()

grpc_action_started = Signal()
"""
Equivalent to `request_started`, args: `sender`, `context`
"""
grpc_action_finished = Signal()
"""
Equivalent to `request_finished`, args: `sender`
"""
