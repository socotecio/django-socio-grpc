from asgiref.sync import sync_to_async
from google.protobuf import empty_pb2
from rest_framework import serializers

from .decorators import grpc_action
from .grpc_actions.actions import GRPCActionMixin
from .grpc_actions.placeholders import (
    FnPlaceholder,
    LookupField,
    SelfSerializer,
    StrTemplatePlaceholder,
)
from .grpc_actions.utils import get_serializer_base_name
from .protobuf.json_format import message_to_dict
from .settings import grpc_settings
from .utils.constants import DEFAULT_LIST_FIELD_NAME, REQUEST_SUFFIX


############################################################
#   Synchronous mixins                                     #
############################################################
class CreateModelMixin(GRPCActionMixin):
    @grpc_action(request=SelfSerializer, response=SelfSerializer)
    def Create(self, request, context):
        """
        Create a model instance.

        The request should be a proto message of ``serializer.Meta.proto_class``.
        If an object is created this returns a proto message of
        ``serializer.Meta.proto_class``.
        """
        serializer = self.get_serializer(message=request)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return serializer.message

    def perform_create(self, serializer):
        """Save a new object instance."""
        serializer.save()

    @staticmethod
    def get_default_method(model_name):
        return {
            "Create": {
                "request": {"is_stream": False, "message": model_name},
                "response": {"is_stream": False, "message": model_name},
            },
        }

    @staticmethod
    def get_default_message(model_name, fields="__all__"):
        return {
            model_name: fields,
        }


class ListModelMixin(GRPCActionMixin):
    @grpc_action(
        request=[],
        request_name=StrTemplatePlaceholder(
            f"{{}}List{REQUEST_SUFFIX}", get_serializer_base_name
        ),
        response=SelfSerializer,
        use_response_list=True,
    )
    def List(self, request, context):
        """
        List a queryset.  This sends a message array of
        ``serializer.Meta.proto_class`` to the client.

        .. note::

            This is a server streaming RPC.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            if hasattr(serializer.message, "count"):
                serializer.message.count = self.paginator.page.paginator.count
            return serializer.message
        else:
            serializer = self.get_serializer(queryset, many=True)
            return serializer.message

    @staticmethod
    def get_default_method(model_name):
        return {
            "List": {
                "request": {"is_stream": False, "message": f"{model_name}ListRequest"},
                "response": {"is_stream": False, "message": f"{model_name}ListResponse"},
            },
        }

    @staticmethod
    def get_default_message(
        model_name, fields=None, pagination=None, response_field_name=DEFAULT_LIST_FIELD_NAME
    ):
        if fields is None:
            fields = []
        # If user let default choose for pagination we check if there is a default pagination class setted
        if pagination is None:
            pagination = grpc_settings.DEFAULT_PAGINATION_CLASS is not None

        response_fields = [f"__custom__repeated {model_name}__{response_field_name}__"]
        if pagination:
            response_fields += ["__custom__int32__count__"]
        return {
            f"{model_name}ListRequest": fields,
            f"{model_name}ListResponse": response_fields,
        }


class StreamModelMixin(GRPCActionMixin):
    @grpc_action(
        request=[],
        request_name=StrTemplatePlaceholder(
            f"{{}}Stream{REQUEST_SUFFIX}", get_serializer_base_name
        ),
        response=SelfSerializer,
        response_stream=True,
    )
    def Stream(self, request, context):
        """
        List a queryset.  This sends a sequence of messages of
        ``serializer.Meta.proto_class`` to the client.

        .. note::

            This is a server streaming RPC.
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, stream=True)
        else:
            serializer = self.get_serializer(queryset, many=True, stream=True)

        yield from serializer.message

    @staticmethod
    def get_default_method(model_name):
        return {
            "Stream": {
                "request": {"is_stream": False, "message": f"{model_name}StreamRequest"},
                "response": {"is_stream": True, "message": model_name},
            },
        }

    @staticmethod
    def get_default_message(model_name, fields=None):
        if fields is None:
            fields = []
        return {
            f"{model_name}StreamRequest": fields,
        }


class RetrieveModelMixin(GRPCActionMixin):
    @grpc_action(
        request=LookupField,
        request_name=StrTemplatePlaceholder(
            f"{{}}Retrieve{REQUEST_SUFFIX}", get_serializer_base_name
        ),
        response=SelfSerializer,
    )
    def Retrieve(self, request, context):
        """
        Retrieve a model instance.

        The request have to include a field corresponding to
        ``lookup_request_field``.  If an object can be retrieved this returns
        a proto message of ``serializer.Meta.proto_class``.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return serializer.message

    @staticmethod
    def get_default_method(model_name):
        return {
            "Retrieve": {
                "request": {"is_stream": False, "message": f"{model_name}RetrieveRequest"},
                "response": {"is_stream": False, "message": model_name},
            },
        }

    @staticmethod
    def get_default_message(model_name, fields="__pk__"):
        return {
            f"{model_name}RetrieveRequest": fields,
        }


class UpdateModelMixin(GRPCActionMixin):
    @grpc_action(request=SelfSerializer, response=SelfSerializer)
    def Update(self, request, context):
        """
        Update a model instance.

        The request should be a proto message of ``serializer.Meta.proto_class``.
        If an object is updated this returns a proto message of
        ``serializer.Meta.proto_class``.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, message=request)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return serializer.message

    def perform_update(self, serializer):
        """Save an existing object instance."""
        serializer.save()

    @staticmethod
    def get_default_method(model_name):
        return {
            "Update": {
                "request": {"is_stream": False, "message": model_name},
                "response": {"is_stream": False, "message": model_name},
            },
        }

    @staticmethod
    def get_default_message(model_name, fields="__all__"):
        return {
            f"{model_name}UpdateRequest": fields,
        }


def _get_partial_update_request(service):
    serializer_class = service.get_serializer_class()

    class PartialUpdateRequest(serializer_class):
        _partial_update_fields = serializers.ListField(child=serializers.CharField())

        class Meta(serializer_class.Meta):
            ...

    # INFO - L.G. - 19/06/2022 - extra field needs to be appended to
    # the serializer.
    if (fields := serializer_class.Meta.fields) and not isinstance(fields, str):
        PartialUpdateRequest.Meta.fields = (*fields, "_partial_update_fields")

    return PartialUpdateRequest


class PartialUpdateModelMixin(GRPCActionMixin):
    @grpc_action(
        request=FnPlaceholder(_get_partial_update_request),
        request_name=StrTemplatePlaceholder(
            f"{{}}PartialUpdate{REQUEST_SUFFIX}", get_serializer_base_name
        ),
        response=SelfSerializer,
    )
    def PartialUpdate(self, request, context):
        """
        Partial update a model instance.

        Performs a partial update on the given `_partial_update_fields`.
        """

        content = message_to_dict(request)

        data = {k: v for k, v in content.items() if k in request._partial_update_fields}

        instance = self.get_object()

        # INFO - L.G. - 11/07/2022 - We use the data parameter instead of message
        # because we handle a dict not a grpc message.
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_partial_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return serializer.message

    def perform_partial_update(self, serializer):
        """Save an existing object instance."""
        serializer.save()

    @staticmethod
    def get_default_method(model_name):
        return {
            "Update": {
                "request": {"is_stream": False, "message": model_name},
                "response": {"is_stream": False, "message": model_name},
            },
        }

    @staticmethod
    def get_default_message(model_name, fields="__all__"):
        return {
            f"{model_name}PartialUpdateRequest": fields,
        }


class DestroyModelMixin(GRPCActionMixin):
    @grpc_action(
        request=LookupField,
        request_name=StrTemplatePlaceholder(
            f"{{}}Destroy{REQUEST_SUFFIX}", get_serializer_base_name
        ),
        response=[],
    )
    def Destroy(self, request, context):
        """
        Destroy a model instance.

        The request have to include a field corresponding to
        ``lookup_request_field``.  If an object is deleted this returns
        a proto message of ``google.protobuf.empty_pb2.Empty``.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return empty_pb2.Empty()

    def perform_destroy(self, instance):
        """Delete an object instance."""
        instance.delete()

    @staticmethod
    def get_default_method(model_name):
        return {
            "Destroy": {
                "request": {"is_stream": False, "message": f"{model_name}DestroyRequest"},
                "response": {"is_stream": False, "message": "google.protobuf.Empty"},
            },
        }

    @staticmethod
    def get_default_message(model_name, fields="__pk__"):
        return {
            f"{model_name}DestroyRequest": fields,
        }


############################################################
#   Asynchronous mixins                                    #
############################################################


class AsyncCreateModelMixin(CreateModelMixin):
    async def Create(self, request, context):
        async_parent_method = sync_to_async(super().Create)
        return await async_parent_method(request, context)


class AsyncListModelMixin(ListModelMixin):
    async def List(self, request, context):
        async_parent_method = sync_to_async(super().List)
        return await async_parent_method(request, context)


class AsyncStreamModelMixin(StreamModelMixin):
    @sync_to_async
    def _get_list_data(self):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, stream=True)
        else:
            serializer = self.get_serializer(queryset, many=True, stream=True)

        return serializer.message

    async def Stream(self, request, context):
        """
        List a queryset.  This sends a sequence of messages of
        ``serializer.Meta.proto_class`` to the client.

        .. note::

            This is a server streaming RPC.
        """
        messages = await self._get_list_data()
        for message in messages:
            await context.write(message)


class AsyncRetrieveModelMixin(RetrieveModelMixin):
    async def Retrieve(self, request, context):
        async_parent_method = sync_to_async(super().Retrieve)
        return await async_parent_method(request, context)


class AsyncUpdateModelMixin(UpdateModelMixin):
    async def Update(self, request, context):
        async_parent_method = sync_to_async(super().Update)
        return await async_parent_method(request, context)


class AsyncPartialUpdateModelMixin(PartialUpdateModelMixin):
    async def PartialUpdate(self, request, context):
        async_parent_method = sync_to_async(super().PartialUpdate)
        return await async_parent_method(request, context)


class AsyncDestroyModelMixin(DestroyModelMixin):
    async def Destroy(self, request, context):
        async_parent_method = sync_to_async(super().Destroy)
        return await async_parent_method(request, context)


############################################################
#   Default grpc messages                                  #
############################################################


def get_default_grpc_methods(model_name):
    """
    return the default grpc methods generated for a django model.
    """
    return {
        **ListModelMixin.get_default_method(model_name),
        **CreateModelMixin.get_default_method(model_name),
        **RetrieveModelMixin.get_default_method(model_name),
        **UpdateModelMixin.get_default_method(model_name),
        **DestroyModelMixin.get_default_method(model_name),
    }


def get_default_grpc_messages(model_name):
    """
    return the default protobuff message we want to generate
    """
    return {
        **CreateModelMixin.get_default_message(model_name),
        **ListModelMixin.get_default_message(model_name),
        **RetrieveModelMixin.get_default_message(model_name),
        **DestroyModelMixin.get_default_message(model_name),
    }
