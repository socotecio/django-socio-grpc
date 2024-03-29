.. _services-registry:

Services Registry
=================

In the goal of automating most of the gRPC complexity (proto generation and server routing),
DSG needs to be **aware of all the services your application wants to serve**.
To achieve this, we require DSG users to register the services.
This page describes how this **registration is done and how it works**.

.. note::
    We are currently considering improvements in `this issue <https://github.com/socotecio/django-socio-grpc/issues/223>`_.
    If you have any recommendations, please feel free to participate. This also means that this interface has a chance to change in the future.

Description
-----------

To register all the services the DSG user wants, we use the :func:`RegistrySingleton <django_socio_grpc.protobuf.registry_singleton.RegistrySingleton>` class.
This class is a Singleton, ensuring that we only have one registry.

To populate this registry, we provide a helper class: :func:`AppHandlerRegistry <django_socio_grpc.services.app_handler_registry.AppHandlerRegistry>`

To make it work, you need to **create one instance of** :func:`AppHandlerRegistry <django_socio_grpc.services.app_handler_registry.AppHandlerRegistry>` **per app**.
By instantiating it, it adds itself to the :func:`RegistrySingleton <django_socio_grpc.protobuf.registry_singleton.RegistrySingleton>` class.
This is similar to adding your app to the ``INSTALLED_APPS`` Django settings but for DSG. We are considering using ``INSTALLED_APPS`` or a specific setting in DSG to do that in the future.
For now, the ``grpc_handlers`` method populated with the server argument is called by the :ref:`ROOT_HANDLER_HOOK setting<root-handler-hook-setting>`.

As the :func:`AppHandlerRegistry <django_socio_grpc.services.app_handler_registry.AppHandlerRegistry>` interface is likely to change in the near future, options are not documented. You can `read the source code <https://github.com/socotecio/django-socio-grpc/blob/master/django_socio_grpc/services/app_handler_registry.py>`_ to understand options or see :ref:`specific how-to if you are trying to register an app from external dependencies <define-proto-and-service-in-a-shared-library>`.

.. code-block:: python

  from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry

  def grpc_handlers(server):
    app_registry = AppHandlerRegistry("quickstart", server)


:func:`AppHandlerRegistry <django_socio_grpc.services.app_handler_registry.AppHandlerRegistry>` has a :func:`register <django_socio_grpc.services.app_handler_registry.AppHandlerRegistry.register>` method that registers the services. The idea is the same as `django routing` or `DRF router` and will leverage two main actions that will be detailed in specific sub-documentation sections:

* **Introspect the Service, Model, and Serializer classes to transform them into ProtoService, ProtoRpc, and ProtoMessage**, which are just Python object representations of protobuf file information. They are used by the :ref:`generateproto <proto-generation>` command.
* **Map our Service to the gRPC server**. The gRPC pb2 generated file provides a method to map a Servicer with the gRPC server. We automatically import this method and call it with the correct arguments.

.. _services-registry-recommendation-for-positioning-handler:

Recommendation for positioning handler
--------------------------------------

The method that register all the services is set in the :ref:`ROOT_HANDLERS_HOOK setting<root-handler-hook-setting>`. This can be a method declared anywhere and it can declare service from anywhere.

The recommandation to avoid having complex method structure is to create a ``handlers.py`` file in your django project directory. And in this handlers file importing ``grpc_handlers`` method from ``handlers.py`` of each app of the project.

Example:

::

    backend
    ├── my_project
    │   ├── handlers.py
    ├── my_first_app
    │   └── handlers.py
    ├── my_second_app
    │   └── handlers.py


.. code-block:: python

    # my_first_app.handlers.py
    from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
    from my_first_app.service import MyFirstAppService

    def grpc_handlers(server):
        app_registry = AppHandlerRegistry("my_first_app", server)
        app_registry.register(MyFirstAppService)


.. code-block:: python

    # my_second_app.handlers.py
    from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
    from my_second_app.service import MyFirstAppService

    def grpc_handlers(server):
        app_registry = AppHandlerRegistry("my_second_app", server)
        app_registry.register(MyFirstAppService)


.. code-block:: python

    # my_project.handlers.py
    from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry
    from my_first_app.handlers import grpc_handlers as my_first_app_grpc_handlers
    from my_second_app.handlers import grpc_handlers as my_second_app_grpc_handlers

    def grpc_handlers(server):
        my_first_app_grpc_handlers()
        my_second_app_grpc_handlers()


.. code-block:: python

    # my_project.settings.py
    ...
    GRPC_FRAMEWORK = {
        ...
        "ROOT_HANDLERS_HOOK": "my_project.handlers.grpc_handlers",
        ...
    }
    ...

Service Introspection
---------------------

To be able to automatically generate proto files, DSG has a complex introspection system that can generate everything
from just a Django app name and a Service class.

We use the class :func:`GRPCAction <django_socio_grpc.grpc_actions.actions.GRPCAction>` to populate the different actions
of a service into the service through the :func:`proto_service <django_socio_grpc.grpc_actions.actions.GRPCActionMixin.proto_service>` property.

The :func:`proto_service <django_socio_grpc.grpc_actions.actions.GRPCActionMixin.proto_service>` property exists
because :func:`Mixins <django_socio_grpc.grpc_actions.mixins>` and :func:`Service<django_socio_grpc.services.base_service.Service>`
base classes inherit from :func:`GRPCActionMixin <django_socio_grpc.grpc_actions.actions.GRPCActionMixin>`.

The :func:`grpc_action<django_socio_grpc.decorators.grpc_action>` decorator directly calls
the :func:`GRPCAction<django_socio_grpc.grpc_actions.actions.GRPCAction>` class, while the actions coming
from mixins are auto-discovered by calling the :func:`GRPCActionMixin.register_actions <django_socio_grpc.grpc_actions.actions.GRPCActionMixin.register_actions>`.
This method is called in the :func:`AppHandlerRegistry.register <django_socio_grpc.services.app_handler_registry.AppHandlerRegistry.register>` when calling in the ``handler`` function..

So, when it's all registered, DSG can add the service class property
:func:`proto_service <django_socio_grpc.grpc_actions.actions.GRPCActionMixin.proto_service>`
created by :func:`GRPCAction <django_socio_grpc.grpc_actions.actions.GRPCAction>`
into the :func:`proto_services <django_socio_grpc.services.app_handler_registry.AppHandlerRegistry.proto_services>`
attribute of the :func:`AppHandlerRegistry <django_socio_grpc.services.app_handler_registry.AppHandlerRegistry>` instance of the app.

As this instance of :func:`AppHandlerRegistry <django_socio_grpc.services.app_handler_registry.AppHandlerRegistry>`
is set in the :func:`RegistrySingleton.registered_apps <django_socio_grpc.protobuf.registry_singleton.RegistrySingleton.registered_apps>`,
we have all the :func:`ProtoService<django_socio_grpc.protobuf.proto_classes.ProtoService>`
instances in the :func:`RegistrySingleton <django_socio_grpc.protobuf.registry_singleton.RegistrySingleton>`: ``my_registry.registered_apps[app_name].proto_services``.

This is how we register all the :func:`ProtoService<django_socio_grpc.protobuf.proto_classes.ProtoService>`
instances into the :func:`RegistrySingleton <django_socio_grpc.protobuf.registry_singleton.RegistrySingleton>`
that are then used for proto generation. To understand how the :func:`ProtoRpc<django_socio_grpc.protobuf.proto_classes.ProtoRpc>` and
:func:`ProtoMessage<django_socio_grpc.protobuf.proto_classes.ProtoMessage>` that constitute the
:func:`ProtoService<django_socio_grpc.protobuf.proto_classes.ProtoService>` are created,
you need to look at the :func:`GRPCAction.make_proto_rpc <django_socio_grpc.grpc_actions.actions.GRPCAction.make_proto_rpc>`.
And even if the code can be complex, it's straightforward and easily testable in unit tests to understand its behavior.

Mapping Service to gRPC server
------------------------------

Each Python ``*_pb2_grpc.py`` file generated by the ``generateproto`` command
has a method called ``add_<ServiceName>ControllerServicer_to_server``.
This method is used to make the link between the gRPC server and the DSG service.

You can find a basic example of an agnostic Python gRPC in the `gRPC documentation <https://grpc.io/docs/languages/python/basics/>`_
**in the Starting the server section**.

DSG wants to simplify this logic for developers, and as it is generating the proto file and the Python file,
it **already knows all the information it needs to find this generated method and call it**.

And this is basically all it does: **finding the correct method in the correct file and calling it for you**.
