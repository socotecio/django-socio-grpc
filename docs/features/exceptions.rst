.. _exceptions:

Exceptions
==========

Description
-----------

Similar to Django and DRF, DSG provides a set of exceptions that can be used to handle errors in your gRPC services.

DSG services can handle these exceptions and **automatically return the appropriate gRPC status code associated to the exception**.

DSG exceptions handling works like `DRF exceptions <https://www.django-rest-framework.org/api-guide/exceptions/>`_.


The handled exceptions are:

* Subclasses of ``GRPCException`` raised inside DSG.
* Subclasses of ``APIException ``raised inside DRF.
* Django's ``Http404`` exception.
* Django's ``PermissionDenied`` exception.

In each case, DSG will abort the gRPC context with an appropriate status code and details. The gRPC message returned by the gRPC abort method will have the code and details key populate with the correct data adapted to the exception.

You can find the different gRPC abort status codes `here <https://grpc.github.io/grpc/core/md_doc_statuscodes.html>`_.

.. note::
    As DSG handles Subclasses of DRF ``APIException`` means, you can raise exceptions imported from DRF as you are used to using DRF.


Example
-------

.. code-block:: python

    # server
    from django_socio_grpc.exceptions import InvalidArgument

    class RaiseCustomErrorService(GenericService):

        @grpc_action()
        async def RaiseError(self, request, context):
            raise InvalidArgument()

    # client
    import asyncio
    import grpc

    async def main():
        async with grpc.aio.insecure_channel("localhost:50051") as channel:
            my_app_client = my_app_pb2_grpc.RaiseCustomErrorControllerStub(channel)

            request = my_app_pb2.RaiseErrorRequest()

            try:
                await my_app_client.RaiseError(request)
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())

    if __name__ == "__main__":
        asyncio.run(main())


Creating custom Error Code and Error Details
------------------------------------------------

.. code-block:: python

    from django_socio_grpc.exceptions import GRPCException

    class CustomError(GRPCException):
        status_code = grpc.StatusCode.INVALID_ARGUMENT
        default_detail = "Custom error message"
        default_code = "custom_error_code"

    class RaiseCustomErrorService(GenericService):

        @grpc_action()
        async def RaiseError(self, request, context):
            raise CustomError()


**Find all the predefined exceptions and their usage in the** :func:`Exceptions APIReference<django_socio_grpc.exceptions>`

Overall, these custom exceptions and utilities allow for more precise and structured error handling when dealing with gRPC-related exceptions in the specified Python project.
