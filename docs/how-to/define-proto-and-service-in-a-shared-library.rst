.. _define-proto-and-service-in-a-shared-library:


Define proto and service in a shared library
=============================================

Description
-----------
The objective of this documentation is to demonstrate how to create a service within a library and share it among various applications.

Django, by definition, is a modular system that allows you to divide a project into several applications. This functionality is important to us, 
this is why in django-socio-grpc we left the possibility for users to maintain this behavior.

This behavior can lead us to have services on an external application or library that we wish to reuse in another. Follow
this guide to importing external services to your application with django-socio-grpc.

# :TODO: please explain, where the handler should reside (recommendation / best practice) in the django project structure, e.g. project root, etc.

Usage
-----
To define a shared service in a library that can be reused across different projects, you will first need to create your service with its functions. 
To ensure the service can be shared, you must use the `to_root_grpc` argument in the handler and set it to "True," 
as shown in the example below.

This argument allows the proto generation to create a .proto and pb2 file in a special folder at the root of the library, with the path defined 
in :ref:`grpc_settings.ROOT_GRPC_FOLDER <_root_grpc_folder_settings>` from django-socio-grpc. (by default, the name of this folder will be grpc_folder at the root of your application).

Example
-------

In this specific case, my_external_library is an external library.

.. code-block:: python

  # :TODO: location of this code ?

  from my_external_library import ExternalService

  def handler(server):
      registry = AppHandlerRegistry(
          app_name="my_external_library", server=server, to_root_grpc=True
      )
      app_registry.register(ExternalService)

By defining here, "to_root_grpc=True", when you generate your protos, they will be added in a folder with the name and path defined in your 
setting grpc_settings.ROOT_GRPC_FOLDER. (by default grpc_folder at the root of your application).


# :TODO: 
Comment:

In our case of an Django Project, with variable number of apps and the gRPC interface in a separate package (we do not want to install the whole django app, when we only need the gRPC interface), 
we have to register each handler in each app, like this:


from .subscriptions import AppHandlerRegistryWithModelSignalDispatchers

def grpc_handlers(server):
    app_registry = AppHandlerRegistryWithModelSignalDispatchers("my_django_app_1", server)

    app_registry.get_grpc_module = lambda: "my_django_app_1_grpc.v1"

    app_registry.register(Example1Service)
    app_registry.register(Example2Service) 
    ...


Each app has its own grpc_handlers.py file, and we have to register each handler in each app in the settings.py file, like this:

.. code-block:: python
    # in urls.py of each app we have to register the handlers

    # register handlers in settings
    grpc_settings.user_settings["GRPC_HANDLERS"] += [
    "my_django_app_1.grpc.handlers.grpc_handlers"]


and in the django project root we have a file grpc_handlers.py, where we import all the grpc_handlers from each app, like this:

.. code-block:: python
    import logging
    from django.utils.module_loading import import_string
    from django_socio_grpc.settings import grpc_settings

    logger = logging.getLogger(__name__)

    def grpc_handlers(server):
        """
        Add servicers to the server
        """

        logger.info(f"adding grpc handlers now:\n {grpc_settings.user_settings['GRPC_HANDLERS']}")
        print(f"****Adding servicers: \n{grpc_settings.user_settings['GRPC_HANDLERS']}")

        if len(grpc_settings.user_settings['GRPC_HANDLERS']) == 0:
            logger.warning(
                "No servicers configured. Did you add GRPC_HANDLERS list to GRPC_FRAMEWORK settings?")

        for handler_str in grpc_settings.user_settings['GRPC_HANDLERS']:
            logger.debug(f"Adding servicers from {handler_str}")
            print(f"****Adding servicers from {handler_str}")
            register_handler = import_string(handler_str)
            register_handler(server)  # calling each handler registration


    