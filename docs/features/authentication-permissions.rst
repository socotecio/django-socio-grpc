.. _authentication-permissions:

Authentication/Permissions
==========================

Description
-----------
Authentication and permissions are **handled in the same way** as in DRF. In this in mind you logically can have project-wide default authentication and authorization classes and / or service-specific ones.
please refer to :

- `DRF Permissions <https://www.django-rest-framework.org/api-guide/permissions/>`_

- `DRF Authentication <https://www.django-rest-framework.org/api-guide/authentication/>`_


However, there are a couple of details that add behavior to default DRF ``Permission`` / ``Authentication`` classes.

For instance, :func:`auth_without_session_middleware<django_socio_grpc.middlewares.auth_without_session_middleware>` (see: :ref:`middlewares <middlewares>` )
will call the service :func:`perform_authentication<django_socio_grpc.services.base_service.Service.perform_authentication>` method which will inject ``user`` into ``context`` arg accessible to
service methods and permission classes. The :func:`perform_authentication<django_socio_grpc.services.base_service.Service.perform_authentication>` will then call all the :func:`authentication_classes<django_socio_grpc.services.base_service.Service.authentication_classes>` of the service as in DRF to try to authenticate user.

The distinction is simple however it's worth to note that while django-rest-framework `BasePermission <https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions>`_ will have ``request, view`` as args,
DSG ``GRPCActionBasePermission`` (that inherits from django-rest-framework `BasePermission <https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions>`_) will have ``context`` (:func:`GRPCInternalProxyContext<django_socio_grpc.request_transformer.grpc_internal_proxy.GRPCInternalProxyContext>`), ``service`` (:func:`Service<django_socio_grpc.services.base_service.Service>`) args instead


Authentication Example
----------------------

To specify an Authentication methods there is two ways as in DRF:

- Globaly, by settings the :ref:`DEFAULT_AUTHENTICATION_CLASSE<default_authentication_classes>` settings

.. code-block:: python

    GRPC_FRAMEWORK = {
        ...
        # oidc_auth package comes from https://github.com/ByteInternet/drf-oidc-auth
        # If you want to use an other auth package and having issue using it please open an issue we will be happy to help
        "DEFAULT_AUTHENTICATION_CLASSES": ["oidc_auth.authentication.JSONWebTokenAuthentication"],
        ...
    }

- By service, by settings the :func:`authentication_classes<django_socio_grpc.services.base_service.Service.authentication_classes>` attributes:

.. code-block:: python

    # oidc_auth package comes from https://github.com/ByteInternet/drf-oidc-auth
    # If you want to use an other auth package and having issue using it please open an issue we will be happy to help
    from oidc_auth.authentication import JSONWebTokenAuthentication
    from rest_framework.permissions import IsAuthenticated
    from django_socio_grpc.generics import AsyncModelService

    class ExampleService(AsyncModelService):
        authentication_classes = [JSONWebTokenAuthentication]
        permission_classes = [IsAuthenticated]


Permission Example
------------------

.. code-block:: python

    from django_socio_grpc.permissions import GRPCActionBasePermission
    from django_socio_grpc.generics import AsyncModelService
    from rest_framework.permissions import SAFE_METHODS

    class OnlySafeOrAdminOrOwner(GRPCActionBasePermission):
        def has_permission(self, context, service):
            if self.context.method in SAFE_METHODS:
                return True
            if context.grpc_action == "SomeCustomSafeEndpoint":
                return True
            return context.user.is_superuser

        def has_object_permission(self, context, service, obj):
            if self.context.method in SAFE_METHODS:
                return True
            if str(obj.created_by) == str(request.user.pk):
                return True
            return context.user.is_superuser

    class ExampleService(AsyncModelService):
        permission_classes = [OnlySafeOrAdminOrOwner]


Python Client Example
---------------------

To use the authentication system in our client you need to pass the the value of the headers as you would do in classic DRF in the metadata ``headers`` key (See :ref:`settings for key configuration<settings-map-medata-keys>`):

.. code-block:: python
    :emphasize-lines: 10,13

    import json
    import asyncio
    import grpc
    from datetime import datetime
    from myapp.grpc import my_app_pb2_grpc, my_app_pb2

    async def main():
        async with grpc.aio.insecure_channel("localhost:50051") as channel:
            my_service_client = my_app_pb2_grpc.MyServiceControllerStub(channel)
            metadata = (("headers", json.dumps({"Authorization": "faketoken"})),)
            request = my_app_pb2.MyServiceListRequest()

            response = await my_service_client.List(request, metadata=metadata)

    if __name__ == "__main__":
        asyncio.run(main())


Web Client Example
------------------

See :ref:`gRPC-web Documentation page <how-to-web>` for more information.

.. code-block:: Javascript
    :emphasize-lines: 12,17

    import { MyServiceController } from '../gen/example_bib_app_connect'

    import { createPromiseClient } from "@connectrpc/connect";
    import { createGrpcWebTransport } from "@connectrpc/connect-web";

    const transport = createGrpcWebTransport({
        baseUrl: "http://localhost:9001",
    });

    const authorClient = createPromiseClient(MyServiceController, transport);

    let headers = {"headers": JSON.stringify({"Authorization": "faketoken"})}

    // See https://connectrpc.com/docs/web/headers-and-trailers
    const res = await authorClient.list(
        {},
        {headers: headers}
    )
    console.log(res)
    let items = res.results
