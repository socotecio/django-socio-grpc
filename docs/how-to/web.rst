Web
===

Description
-----------

It's possible to use gRPC in a broswer considering some limitations (See `state-of-grpc-web <https://grpc.io/blog/state-of-grpc-web/>`_.
Using it allow you to have only one interface for all your customer. It also enable server side streams that is not existing in classic REST protocols.

All the next step described here can be found in the `dsg-example repository <https://github.com/socotecio/django-socio-grpc-example>`_ in the `frontend/grpc-web-example <https://github.com/socotecio/django-socio-grpc-example/frontend/grpc-web-example>`_ directory.

We will use `BUF <https://buf.build/>`_ to generate the JS api files. See :ref:`understanding differences in the grpc-web ecosystem<Understanding differences in the grpc-web ecosystem>`.

It work the same as traditionnal gRPC except that a proxy is charged to transform traditional request into enforced HTTP/2 gRPC compatible one.

Depending on the backend you use `you may even not need a proxy but just some middleware<https://github.com/grpc/grpc-web#ecosystem>`_. But in Python it's still needed for now. The goal is that gRPC-web support directly in language-specific web framework following `their roadmap<https://github.com/grpc/grpc-web/blob/master/doc/roadmap.md>`_.

If you are considering a production deployement on a kubernetes cluster please read :ref:`Istio config`. For local development follow next steps.


Understanding differences in the grpc-web ecosystem
-----------

First step is to understand the differences between the concepts.

1. Protocol for gRPC in browser

The protocol is the technical way to encapsulate grpc request/response into compatible broswer request that are then converted by a proxy to HTTP/2 grpc requests/response.

The existing protocols are:
- `gRPC-WEB<https://github.com/grpc/grpc-web>`_: the first one created to make gRPC API work in browser
- `BUF Connect<https://connectrpc.com/>`_: The new kid on the block that implement it's own protocol that aim to include all the differents protocols automatically in one. It now support Go, Node & Browser, Swift, Kotlin. So we can't use it with DSG for now.

2. The Protocol buffer compiler plugins for browser

One of gRPC framework core functionnality is the generation of the client code from the proto file in different langage to make the RPC works.

To compile proto file into langage specific code files you need to use the `Protocol Buffer Compiler or protoc<https://grpc.io/docs/protoc-installation/>`. But as gRPC is not supporting browser by default it need plugin to work with.

The different exisiting pugins are:
- protoc-gen-grpc-web `directly on the grpc-web release page<https://github.com/grpc/grpc-web#code-generator-plugin>`_
- protobuf-javascript `The protobuf open source project for compiling into js <https://github.com/protocolbuffers/protobuf-javascript>`
- `BUF cli<https://buf.build/product/cli>`_ with:
    - @connectrpc/protoc-gen-connect-es `The BUF plugin for generating Service <https://github.com/connectrpc/connect-es>`_
    - @bufbuild/protoc-gen-es `The buf plugin for request and message <https://github.com/bufbuild/protobuf-es>`_


3. The Import style of the client generation

In Browser JS the ecosystem is wylde and there is a lot of differents import system like: `ESM <https://nodejs.org/api/esm.html>`_, `CommonJs <https://nodejs.org/api/modules.html>`, `Closure <https://github.com/google/closure-library/wiki/goog.module:-an-ES6-module-like-alternative-to-goog.provide>`
And you also have the Typescript/Javascript difference depending of your project.

Each tool have it own import style (or target) possible:
- protoc-gen-grpc-web: closure, commonjs, commonjs+dts, typescript
- protobuf-javascript: Closure, commonjs
- @connectrpc/protoc-gen-connect-es: ESM, in js or ts
- @bufbuild/protoc-gen-es: ESM, in js or ts

Note: `Vite<https://vitejs.dev/>`_ do not support commonjs as it aim to increase speed of js compilation by using only ESM module. `See <https://github.com/grpc/grpc-web/issues/1242>`_.

4. The client

To use the generated files there is multiple options:
- gRPC-web generated class directly. `Example <https://github.com/grpc/grpc-web#option-using-promises-limited-features>`_
- Improbable. `Example <https://github.com/improbable-eng/grpc-web#example>`_
- BUF connect. `Example <https://connectrpc.com/docs/web/using-clients/>`_

Improbable work with grpc-web generated files, BUF connect work with BUF CLI generated files

5. The DSG recommendation

Regarding the progress in the grpc ecosystem lately here is what we recommend as the DSG core team:
- Protocol:             gRPC-web    - Connect does not support python as I write this lines
- Generator plugin :    BUF cli     - Support ESM format, the only one compatible with Vite. See :ref:`Generating JS client<Generating JS client>` for usage.
- Import style:         ESM         - As we recommend BUF cli there is only ESM as import style. Choose js or ts depending of your project.
- Client:               Buf connect - Support gRPC-web protocol but with better message and response manipulation.


The Envoy Proxy & docker image
-----------

The default recommended proxy is `Envoy <https://www.envoyproxy.io/>`_. The doc of `grpc-web <https://github.com/grpc/grpc-web>`_ document how to use it and even give you a example config file: `envoy.yaml <https://github.com/grpc/grpc-web/blob/master/net/grpc/gateway/examples/echo/envoy.yaml>`_

In this example file the importante lines you need to know beacause you may need to change them are:
- l.10: specify the listening port
- l.60 & 61: specify the address and port of the grpc-server
- l.26 & 48: cluster name need to match together

To help you understand how to launch it you can have a look in our example repository:
- `Envoy configuration and dockerfile <https://github.com/socotecio/django-socio-grpc-example/envoy>`_
- `Docker compose conf <https://github.com/socotecio/django-socio-grpc-example/envoy#L33>`_

This can also be launched in production environment but if the envoy proxy is not located in the same local network it can bring latency. Please consider using `Istio <https://istio.io/>`_ if in kubernetes deployement

Generating JS client
-----------

By using BUF you can upload your proto files directly to `BSR <https://buf.build/product/bsr>`_ and use their SDK to `dynamically generate files while pushing to registry <https://buf.build/docs/bsr/generated-sdks/npm>`_.

But to help understand how it work and making simple example we will use `locally generated files <https://connectrpc.com/docs/web/generating-code#local-generation>`_
Here is the step needed:

- Install dependencies (3 in dev mode and 3 in normal mode ). `Example <https://github.com/socotecio/django-socio-grpc-example/frontend/grpc-web-example/package.json>`_
- Create the buf.gen.yaml with at least the es and the connect-es plugin. Even if it can be anywhere we recommend you to put it at the root of your js folder or your API folder. The example will only work if at the root of a vue vite/webpack project as it expect a src folder to exist.  `Example <https://github.com/socotecio/django-socio-grpc-example/frontend/grpc-web-example/buf.gen.yaml>`_
- Copy the proto file into a proto directory created in the folder of the buf.gen.yaml file. `Example <https://github.com/socotecio/django-socio-grpc-example/frontend/grpc-web-example/proto>`_
- Launch the command: npx buf generate proto `Explanation <https://github.com/socotecio/django-socio-grpc-example/README.md#how-to-update-the-js-file-when-api-update>`_
- A src/gen folder should create with two file. _connect.js file with the Services/Controllers file and _pb.js with request and response message file `Example <https://github.com/socotecio/django-socio-grpc-example/frontend/grpc-web-example/src/gen>`_

Once this two file are generated you are good to go to the next step


Using JS client
-----------

BUF already documented this part: `Using clients <https://connectrpc.com/docs/web/using-clients>`_.

But there is some details that can be confusing:
- You need to use the `createGrpcWebTransport protocol <https://connectrpc.com/docs/web/choosing-a-protocol>_`.
- If proto was generated by DSG then the _connect.js file export Service name with Controller instead of Service name. In the BUF doc ElizaService should have been ElizaController
- If API field use snake_case they should be setted and getted by camelCase if using the createGrpcWebTransport as grpc-web automatically convert fields.

See `our DSG example for more explicit example <https://github.com/socotecio/django-socio-grpc-example/src/components/APIExample.vue>`_


Istio config
-----------

For production deploiement you may consider the usage of `Istio <https://istio.io/>`_ that produce a `grpc-web proxy out of the box <https://istio.io/latest/docs/ops/configuration/traffic-management/protocol-selection/>`_.

You will only need to configure the corsPolicy of your Istio VirtualService to allow request and headers specific to gRPC-web and DSG:

.. code-block:: yaml
    ---
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

Learn more about VirtualService in the `Istio documentation<https://istio.io/latest/docs/reference/config/networking/virtual-service/>`_