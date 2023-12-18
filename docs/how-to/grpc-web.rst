.. _how-to-web:
gRPC-Web
=========

Description
-----------

It's possible to use gRPC in a browser, considering some limitations (See `state-of-grpc-web <https://grpc.io/blog/state-of-grpc-web/>`_). Using it allows you to have only one interface for all your customers. It also enables server-side streams that do not exist in classic REST protocols.

All the next steps described here can be found in the `dsg-example repository <https://github.com/socotecio/django-socio-grpc-example>`_ in the `frontend/grpc-web-example <https://github.com/socotecio/django-socio-grpc-example/tree/main/frontend/grpc-web-example>`_ directory.

We will use `BUF <https://buf.build/>`_ to generate the JS API files. See :ref:`Understanding differences in the grpc-web ecosystem`.

It works the same as traditional gRPC, except that a proxy is charged with transforming traditional requests into enforced HTTP/2 gRPC-compatible ones.

Depending on the backend you use, `you may even not need a proxy but just some middleware <https://github.com/grpc/grpc-web#ecosystem>`_. But in Python, it's still needed for now. The goal is that gRPC-web supports directly in language-specific web framework following `their roadmap <https://github.com/grpc/grpc-web/blob/master/doc/roadmap.md>`_.

If you are considering a production deployment on a Kubernetes cluster, please read :ref:`Istio Config`. For local development, follow the next steps.

.. _Understanding differences in the grpc-web ecosystem:

Understanding differences in the grpc-web ecosystem
---------------------------------------------------

The first step is to understand the differences between the concepts.

1. Protocol for gRPC in the browser

  The protocol is the technical way to encapsulate gRPC request/response into compatible browser requests that are then converted by a proxy to HTTP/2 gRPC requests/response.

  The existing protocols are:

  * `gRPC-WEB <https://github.com/grpc/grpc-web>`_: the first one created to make gRPC API work in the browser
  * `BUF Connect <https://connectrpc.com/>`_: The new kid on the block that implements its own protocol that aims to include all the different protocols automatically in one. It now supports Go, Node & Browser, Swift, Kotlin. So we can't use it with DSG for now.

2. The Protocol buffer compiler plugins for the browser

  One of the gRPC framework core functionalities is the generation of the client code from the proto file in different languages to make the RPC work.

  To compile proto files into language-specific code files, you need to use the `Protocol Buffer Compiler or protoc <https://grpc.io/docs/protoc-installation/>`. But as gRPC is not supporting the browser by default, it needs a plugin to work with.

  The different existing plugins are:
  * protoc-gen-grpc-web `directly on the grpc-web release page <https://github.com/grpc/grpc-web#code-generator-plugin>`_
  * protobuf-javascript `The protobuf open source project for compiling into js <https://github.com/protocolbuffers/protobuf-javascript>`
  * `BUF cli <https://buf.build/product/cli>`_ with:

    * @connectrpc/protoc-gen-connect-es `The BUF plugin for generating Service <https://github.com/connectrpc/connect-es>`_
    * @bufbuild/protoc-gen-es `The buf plugin for request and message <https://github.com/bufbuild/protobuf-es>`_

3. The Import style of the client generation

  In Browser JS, the ecosystem is wild, and there are a lot of different import systems like: `ESM <https://nodejs.org/api/esm.html>`_, `CommonJs <https://nodejs.org/api/modules.html>`, `Closure <https://github.com/google/closure-library/wiki/goog.module:-an-ES6-module-like-alternative-to-goog.provide>`. And you also have the Typescript/Javascript difference depending on your project.

  Each tool has its own import style (or target) possible:

  * protoc-gen-grpc-web: closure, commonjs, commonjs+dts, typescript
  * protobuf-javascript: Closure, commonjs
  * @connectrpc/protoc-gen-connect-es: ESM, in js or ts
  * @bufbuild/protoc-gen-es: ESM, in js or ts

  Note: `Vite <https://vitejs.dev/>`_ does not support commonjs as it aims to increase the speed of js compilation by using only ESM module. `See <https://github.com/grpc/grpc-web/issues/1242>`_.

4. The client

  To use the generated files, there are multiple options:

  * gRPC-web generated class directly. `Example <https://github.com/grpc/grpc-web#option-using-promises-limited-features>`_
  * Improbable. `Example <https://github.com/improbable-eng/grpc-web#example>`_
  * BUF connect. `Example <https://connectrpc.com/docs/web/using-clients/>`_

  Improbable works with grpc-web generated files, BUF connect works with BUF CLI generated files

5. The DSG recommendation

  Regarding the progress in the grpc ecosystem lately, here is what we recommend as the DSG core team:

  * Protocol:             gRPC-web    - Connect does not support python as I write these lines
  * Generator plugin :    BUF cli     - Support ESM format, the only one compatible with Vite. See :ref:`Generating JS client<Generating JS client>` for usage.
  * Import style:         ESM         - As we recommend BUF cli there is only ESM as import style. Choose js or ts depending on your project.
  * Client:               Buf connect - Support gRPC-web protocol but with better message and response manipulation.


The Envoy Proxy & docker image
-------------------------------

The default recommended proxy is `Envoy <https://www.envoyproxy.io/>`_. The doc of `grpc-web <https://github.com/grpc/grpc-web>`_ documents how to use it and even gives you an example config file: `envoy.yaml <https://github.com/grpc/grpc-web/blob/master/net/grpc/gateway/examples/echo/envoy.yaml>`_

In this example file, the important lines you need to know because you may need to change them are:

* l.10: specify the listening port
* l.60 & 61: specify the address and port of the grpc-server
* l.26 & 48: cluster name needs to match together

To help you understand how to launch it, you can have a look in our example repository:

* `Envoy configuration and dockerfile <https://github.com/socotecio/django-socio-grpc-example/envoy>`_
* `Docker compose conf <https://github.com/socotecio/django-socio-grpc-example/envoy#L33>`_

This can also be launched in a production environment, but if the envoy proxy is not located in the same local network it can bring latency. Please consider using `Istio <https://istio.io/>`_ if in a Kubernetes deployment

Generating JS Client
---------------------

By using BUF, you can upload your proto files directly to `BSR <https://buf.build/product/bsr>`_ and use their SDK to `dynamically generate files while pushing to registry <https://buf.build/docs/bsr/generated-sdks/npm>`_.

To better understand how it works and to provide a simple example, we will use `locally generated files <https://connectrpc.com/docs/web/generating-code#local-generation>`_.

Here are the steps needed:

#. Install dependencies (3 in dev mode and 3 in normal mode). `Example <https://github.com/socotecio/django-socio-grpc-example/tree/main/frontend/grpc-web-example/package.json>`_
#. Create the `buf.gen.yaml` file with at least the `es` and the `connect-es` plugin. Even if it can be anywhere, we recommend putting it at the root of your JS folder or your API folder. The example will only work if at the root of a Vue Vite/Webpack project as it expects an existing `src` folder. `Example <https://github.com/socotecio/django-socio-grpc-example/tree/main/frontend/grpc-web-example/buf.gen.yaml>`_
#. Copy the proto file into a `proto` directory created in the folder of the `buf.gen.yaml` file. `Example <https://github.com/socotecio/django-socio-grpc-example/tree/main/frontend/grpc-web-example/proto>`_
#. Launch the command: `npx buf generate proto` `Explanation <https://github.com/socotecio/django-socio-grpc-example/README.md#how-to-update-the-js-file-when-api-update>`_
#. A `src/gen` folder should be created with two files: `_connect.js` file with the Services/Controllers file and `_pb.js` with request and response message files. `Example <https://github.com/socotecio/django-socio-grpc-example/tree/main/frontend/grpc-web-example/src/gen>`_

Once these two files are generated, you are good to go to the next step.

.. _using_js_client:
Using JS Client
----------------

BUF has already documented this part: `Using clients <https://connectrpc.com/docs/web/using-clients>`_.

However, there are some details that can be confusing:

* You need to use the `createGrpcWebTransport` protocol. `Example <https://connectrpc.com/docs/web/choosing-a-protocol>`_
* If the proto was generated by DSG, then the `_connect.js` file exports the Service name with Controller instead of Service name. In the BUF doc, ElizaService should have been ElizaController.
* If API fields use snake_case, they should be set and get by camelCase when using the `createGrpcWebTransport` as grpc-web automatically converts fields.

See `our DSG example for a more explicit example <https://github.com/socotecio/django-socio-grpc-example/src/components/APIExample.vue>`_.

.. _Istio Config:

Istio Config
-------------

For production deployment, you may consider the usage of `Istio <https://istio.io/>`_ that produces a `grpc-web proxy out of the box <https://istio.io/latest/docs/ops/configuration/traffic-management/protocol-selection/>`_.

You will only need to configure the `corsPolicy` of your Istio VirtualService to allow requests and headers specific to gRPC-web and DSG:

.. code-block:: yaml
  :emphasize-lines: 12

  apiVersion: networking.istio.io/v1alpha3
  kind: VirtualService
  metadata:
    name: ...
    labels: ...
  spec:
    hosts: ...
    gateways: ...
    http:
        - match: ...
        route: ...
        corsPolicy:
          allowOrigin:
            - "*"
          allowMethods:
            - POST
            - GET
            - OPTIONS
            - PUT
            - DELETE
          allowHeaders:
            - grpc-timeout
            - content-type
            - keep-alive
            - user-agent
            - cache-control
            - content-type
            - content-transfer-encoding
            - custom-header-1
            - x-accept-content-transfer-encoding
            - x-accept-response-streaming
            - x-user-agent
            - x-grpc-web
            - filters
            - pagination
            - headers
          maxAge: 1728s
          exposeHeaders:
            - custom-header-1
            - grpc-status
            - grpc-message
            - filters
            - pagination
            - headers
          allowCredentials: true

Learn more about VirtualService in the `Istio documentation <https://istio.io/latest/docs/reference/config/networking/virtual-service/>`_.