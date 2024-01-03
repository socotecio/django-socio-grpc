.. _define-proto-and-service-in-a-shared-library:


Define proto and service in a shared library
=============================================

Description
-----------
The objective of this documentation is to demonstrate how to create a **service within a library and share it among various applications**.

Django, by definition, is a modular system that allows you to divide a project into several applications. This functionality is important to us,
this is why **in DSG we left the possibility for users to maintain this behavior**.

This behavior can lead us to have services on an external application or library that we wish to reuse in another. Follow
this guide to importing external services to your application with DSG.

See :ref:`Service registry handler positioning recommandation<services-registry-recommendation-for-positioning-handler>` to understand how to work with ``handlers.py`` files.

Usage
-----

To define a shared service in a library that can be reused across different projects, you will first need to create your service with its functions. 
To ensure the service can be shared, you must use the ``to_root_grpc`` argument in the `handler` and set it to ``True`` 
as shown in the example below.

This argument allows the proto generation to create a ``.proto`` and ``_pb2.py`` file in a **special folder at the root of the library**, with the path defined
in :ref:`grpc_settings.ROOT_GRPC_FOLDER <root_grpc_folder_settings>` from django-socio-grpc. (by default, the name of this folder will be ``grpc_folder`` at the root of your application).

Example
-------

In this specific case, ``my_external_library`` is an external library.

.. code-block:: python

  # my_app/handlers.py

  from my_external_library import ExternalService

  def grpc_handlers(server):
      registry = AppHandlerRegistry(
          app_name="my_external_library", server=server, to_root_grpc=True
      )
      app_registry.register(ExternalService)

By defining here, ``to_root_grpc=True``, when you generate your protos, they will be added in a folder with the name and path defined in your
setting :ref:`grpc_settings.ROOT_GRPC_FOLDER <root_grpc_folder_settings>`. (by default ``grpc_folder`` at the root of your application).
