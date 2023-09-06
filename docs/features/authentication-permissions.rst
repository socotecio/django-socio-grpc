Authentication/Permissions
==========================

Description
-----------
Authentication and permissions are handled in the same way as in django-rest-framework,
just as in DRF, you can have project-wide default authentication and authorization classes and / or service-specific ones.
please refer to :

- `DRF Permissions <https://www.django-rest-framework.org/api-guide/permissions/>`_ 
  
- `DRF Authentication <https://www.django-rest-framework.org/api-guide/authentication/>`_ 


However, there are a couple of details that add behavior to default DRF ``Permission`` / ``Authentication`` classes.

For instance, ``auth_without_session_middleware`` (see: :ref:`middleware <middleware>` )
will call the service ``perform_authentication()`` method which will inject ``user`` into ``context`` arg accessible to 
service methods and permission classes.

The distinction is simple however it's worth to note that while django-rest-framework ``BasePermission`` will have ``request, view``` as args,
django-socio-grpc ``GRPCActionBasePermission`` (that inherits from django-rest-framework ``BasePermission``) will have ``context, service`` args instead
