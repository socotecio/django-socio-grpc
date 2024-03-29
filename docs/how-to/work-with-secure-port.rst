.. _work-with-secure-port:

Work with secure port
======================


Description
-----------


If you try to authenticate your servers with certificates you may have read the `gRPC Auth documentation <https://grpc.io/docs/guides/auth/>`_ or the `python example <https://github.com/grpc/grpc/tree/master/examples/python/auth>`_ and wonder how to do the same with DSG.

As DSG is just a wrapper around the gRPC server we expose settings to deal with the options you usualy pass to `grpc.ssl_server_credentials <https://grpc.github.io/grpc/python/grpc.html#create-server-credentials>`_.

To enable it you need to fill the :ref:`settings-private-key-certificate_chain-pairs-path` setting. This will fill the ``private_key_certificate_chain_pairs`` arguments and enable the usage of `add_secure_port <https://grpc.github.io/grpc/python/grpc.html#grpc.Server.add_secure_port>`_ instead of `add_insecure_port <https://grpc.github.io/grpc/python/grpc.html#grpc.Server.add_insecure_port>`_.

In the same logic :ref:`settings-root-certificates-path` and :ref:`settings-require-client-auth` allow you to fill ``root_certificates`` and  ``require_client_auth`` args


Usage
-----

Server:

.. code-block:: python

    # settings.py
    GRPC_FRAMEWORK = {
        "PRIVATE_KEY_CERTIFICATE_CHAIN_PAIRS_PATH": [("/path/to/server-key.pem", "/path/to/server.pem")],
        "ROOT_CERTIFICATES_PATH": "/path/to/certificates.pem",
        "REQUIRE_CLIENT_AUTH": True,
    }

Client:

.. code-block:: python

    import asyncio
    import grpc

    def create_client_channel(addr: str) -> grpc.aio.Channel:

        with open("/path/to/certificates.pem", "rb") as certificate_file:
        # Channel credential will be valid for the entire channel. See https://grpc.github.io/grpc/python/grpc.html#grpc.ssl_channel_credentials
            channel_credential = grpc.ssl_channel_credentials(
                certificate_file.read()
            )
        channel = grpc.aio.secure_channel(addr, channel_credential)
        return channel

    async def main() -> None:
        channel = create_client_channel("localhost:50051")

        # Mock method that make an RPC. If don't know how to make a rpc call see Examples section
        await send_rpc(channel)
        await channel.close()


    if __name__ == "__main__":
        asyncio.run(main())
