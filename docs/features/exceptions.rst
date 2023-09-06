Exceptions
==========

Description
-----------

In Django, exceptions are raised when something unexpected or erroneous occurs during the execution of a web application. 
Those exceptions are related to a specific status_code. you can find more information (`here <https://grpc.github.io/grpc/core/md_doc_statuscodes.html>`_).
Django provides a set of built-in exceptions and allows you to create custom exceptions as needed.
Django-Socio-GRPC provides gRPC exceptions which are essential for handling gRPC errors and providing informative responses to users. 


Usage
-----

Here's an explanation of each exception :

============
ErrorDetail
============

This is not an exception but a custom class that represents a string-like object with an optional error code. It's used to encapsulate error details.

===========================
ProtobufGenerationException
===========================

An exception class for handling errors related to protobuf generation within the Socio gRPC framework. It can be raised with specific information about the app name, model name, and a detail message.

==============
GRPCException
==============

A base class for Socio gRPC framework runtime exceptions. Subclasses should provide .status_code and .default_detail properties. It has two methods for getting error codes and full error details.

================
Unauthenticated
================

Subclass of GRPCException representing the UNAUTHENTICATED gRPC status code. It indicates that authentication credentials were not provided.

================
PermissionDenied
================

Subclass of GRPCException representing the PERMISSION_DENIED gRPC status code. It indicates that the user does not have permission to perform a certain action.

=========
NotFound
=========

Subclass of GRPCException representing the NOT_FOUND gRPC status code. It indicates that the requested resource was not found.

============
AlreadyExist
============

Subclass of GRPCException representing the ALREADY_EXISTS gRPC status code. It indicates that the requested resource already exists.

===============
InvalidArgument
===============

Subclass of GRPCException representing the INVALID_ARGUMENT gRPC status code. It indicates that an invalid argument was provided.

=============
Unimplemented
=============

Subclass of GRPCException representing the UNIMPLEMENTED gRPC status code. It indicates that the requested operation is not yet implemented.


The code also includes utility functions _get_error_details, _get_codes, and _get_full_details for processing error details, error codes, and full error details, respectively.

Overall, these custom exceptions and utilities allow for more precise and structured error handling when dealing with gRPC-related exceptions in the specified Python project.



Example
-------


.. code-block:: python

    from django_socio_grpc.exceptions import NotFound

    @grpc_action(
        request=[{"name": "project_uuid", "type": "string"}],
        request_name="RetrieveProjectPerimeterRequest",
        response=PerimeterProtoSerializer,
    )
    async def RetrieveProjectPerimeter(self, request, context):
        try:
            perimeter = await Perimeter.objects.aget(project=request.project_uuid)
        except Perimeter.DoesNotExist:
            raise NotFound()

        serializer = PerimeterProtoSerializer(perimeter)
        return await serializer.amessage

.. code-block:: python

    from django_socio_grpc.exceptions import GRPCException

    class AsyncDestroyIfNotExistInReportMixin(mixins.AsyncDestroyModelMixin):
        async def aperform_destroy(self, instance):
            instance = await self.aget_object()
            request_filter = {"status": "SENT", "related_objects": [str(instance.uuid)]}
            report_grpc_api = ReportGrpcApi()
            exists = await report_grpc_api.check_exists(request_filter=request_filter)

            if exists:
                raise GRPCException(
                    {
                        "code": "exists_in_report",
                        "message": "The asset can't be deleted beacause it's already sent in a report",
                    }
                )

            return await super().aperform_destroy(instance)