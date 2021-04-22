# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2

from django_socio_grpc.tests.fakeapp.grpc import (
    fakeapp_pb2 as django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2,
)


class UnitTestModelControllerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.List = channel.unary_unary(
            "/fakeapp.UnitTestModelController/List",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelListRequest.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelListResponse.FromString,
        )
        self.Create = channel.unary_unary(
            "/fakeapp.UnitTestModelController/Create",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.FromString,
        )
        self.Retrieve = channel.unary_unary(
            "/fakeapp.UnitTestModelController/Retrieve",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelRetrieveRequest.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.FromString,
        )
        self.Update = channel.unary_unary(
            "/fakeapp.UnitTestModelController/Update",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.FromString,
        )
        self.Destroy = channel.unary_unary(
            "/fakeapp.UnitTestModelController/Destroy",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelDestroyRequest.SerializeToString,
            response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
        )


class UnitTestModelControllerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def List(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Create(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Retrieve(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Destroy(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_UnitTestModelControllerServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "List": grpc.unary_unary_rpc_method_handler(
            servicer.List,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelListRequest.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelListResponse.SerializeToString,
        ),
        "Create": grpc.unary_unary_rpc_method_handler(
            servicer.Create,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.SerializeToString,
        ),
        "Retrieve": grpc.unary_unary_rpc_method_handler(
            servicer.Retrieve,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelRetrieveRequest.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.SerializeToString,
        ),
        "Update": grpc.unary_unary_rpc_method_handler(
            servicer.Update,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.SerializeToString,
        ),
        "Destroy": grpc.unary_unary_rpc_method_handler(
            servicer.Destroy,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelDestroyRequest.FromString,
            response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "fakeapp.UnitTestModelController", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class UnitTestModelController(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def List(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.UnitTestModelController/List",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelListRequest.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelListResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Create(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.UnitTestModelController/Create",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Retrieve(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.UnitTestModelController/Retrieve",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelRetrieveRequest.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Update(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.UnitTestModelController/Update",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModel.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Destroy(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.UnitTestModelController/Destroy",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.UnitTestModelDestroyRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )


class ForeignModelControllerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.List = channel.unary_unary(
            "/fakeapp.ForeignModelController/List",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelListRequest.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelListResponse.FromString,
        )
        self.Retrieve = channel.unary_unary(
            "/fakeapp.ForeignModelController/Retrieve",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelRetrieveRequestCustom.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelRetrieveRequestCustom.FromString,
        )


class ForeignModelControllerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def List(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Retrieve(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_ForeignModelControllerServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "List": grpc.unary_unary_rpc_method_handler(
            servicer.List,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelListRequest.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelListResponse.SerializeToString,
        ),
        "Retrieve": grpc.unary_unary_rpc_method_handler(
            servicer.Retrieve,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelRetrieveRequestCustom.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelRetrieveRequestCustom.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "fakeapp.ForeignModelController", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class ForeignModelController(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def List(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.ForeignModelController/List",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelListRequest.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelListResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Retrieve(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.ForeignModelController/Retrieve",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelRetrieveRequestCustom.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ForeignModelRetrieveRequestCustom.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )


class ManyManyModelControllerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.List = channel.unary_unary(
            "/fakeapp.ManyManyModelController/List",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelListRequest.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelListResponse.FromString,
        )
        self.Create = channel.unary_unary(
            "/fakeapp.ManyManyModelController/Create",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.FromString,
        )
        self.Retrieve = channel.unary_unary(
            "/fakeapp.ManyManyModelController/Retrieve",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelRetrieveRequest.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.FromString,
        )
        self.Update = channel.unary_unary(
            "/fakeapp.ManyManyModelController/Update",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.FromString,
        )
        self.Destroy = channel.unary_unary(
            "/fakeapp.ManyManyModelController/Destroy",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelDestroyRequest.SerializeToString,
            response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
        )


class ManyManyModelControllerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def List(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Create(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Retrieve(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Destroy(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_ManyManyModelControllerServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "List": grpc.unary_unary_rpc_method_handler(
            servicer.List,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelListRequest.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelListResponse.SerializeToString,
        ),
        "Create": grpc.unary_unary_rpc_method_handler(
            servicer.Create,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.SerializeToString,
        ),
        "Retrieve": grpc.unary_unary_rpc_method_handler(
            servicer.Retrieve,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelRetrieveRequest.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.SerializeToString,
        ),
        "Update": grpc.unary_unary_rpc_method_handler(
            servicer.Update,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.SerializeToString,
        ),
        "Destroy": grpc.unary_unary_rpc_method_handler(
            servicer.Destroy,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelDestroyRequest.FromString,
            response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "fakeapp.ManyManyModelController", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class ManyManyModelController(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def List(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.ManyManyModelController/List",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelListRequest.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelListResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Create(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.ManyManyModelController/Create",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Retrieve(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.ManyManyModelController/Retrieve",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelRetrieveRequest.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Update(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.ManyManyModelController/Update",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModel.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Destroy(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.ManyManyModelController/Destroy",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.ManyManyModelDestroyRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )


class RelatedFieldModelControllerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.List = channel.unary_unary(
            "/fakeapp.RelatedFieldModelController/List",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelListRequest.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelListResponse.FromString,
        )
        self.Create = channel.unary_unary(
            "/fakeapp.RelatedFieldModelController/Create",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.FromString,
        )
        self.Retrieve = channel.unary_unary(
            "/fakeapp.RelatedFieldModelController/Retrieve",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelRetrieveRequest.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.FromString,
        )
        self.Update = channel.unary_unary(
            "/fakeapp.RelatedFieldModelController/Update",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.SerializeToString,
            response_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.FromString,
        )
        self.Destroy = channel.unary_unary(
            "/fakeapp.RelatedFieldModelController/Destroy",
            request_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelDestroyRequest.SerializeToString,
            response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
        )


class RelatedFieldModelControllerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def List(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Create(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Retrieve(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Destroy(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_RelatedFieldModelControllerServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "List": grpc.unary_unary_rpc_method_handler(
            servicer.List,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelListRequest.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelListResponse.SerializeToString,
        ),
        "Create": grpc.unary_unary_rpc_method_handler(
            servicer.Create,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.SerializeToString,
        ),
        "Retrieve": grpc.unary_unary_rpc_method_handler(
            servicer.Retrieve,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelRetrieveRequest.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.SerializeToString,
        ),
        "Update": grpc.unary_unary_rpc_method_handler(
            servicer.Update,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.FromString,
            response_serializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.SerializeToString,
        ),
        "Destroy": grpc.unary_unary_rpc_method_handler(
            servicer.Destroy,
            request_deserializer=django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelDestroyRequest.FromString,
            response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "fakeapp.RelatedFieldModelController", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class RelatedFieldModelController(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def List(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.RelatedFieldModelController/List",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelListRequest.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelListResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Create(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.RelatedFieldModelController/Create",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Retrieve(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.RelatedFieldModelController/Retrieve",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelRetrieveRequest.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Update(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.RelatedFieldModelController/Update",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.SerializeToString,
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModel.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def Destroy(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/fakeapp.RelatedFieldModelController/Destroy",
            django__socio__grpc_dot_tests_dot_fakeapp_dot_grpc_dot_fakeapp__pb2.RelatedFieldModelDestroyRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
