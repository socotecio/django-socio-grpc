import grpc

from django_socio_grpc.settings import grpc_settings


def load_credential_from_file(file_path):
    with open(file_path, "rb") as f:
        return f.read()


def map_certificate_path_to_file_content():
    """
    Transform a pair of path to a pair of file content
    [path, path] -> [file_content, file_contetn]
    """
    return [
        [
            load_credential_from_file(certificate_chain_pair[0]),
            load_credential_from_file(certificate_chain_pair[1]),
        ]
        for certificate_chain_pair in grpc_settings.PRIVATE_KEY_CERTIFICATE_CHAIN_PAIRS_PATH
    ]


def get_server_credentials():
    """
    Return None of grpc.ssl_server_credentials(https://grpc.github.io/grpc/python/grpc.html#create-server-credentials) depending of if grpc_settings.PRIVATE_KEY_CERTIFICATE_CHAIN_PAIRS_PATH is set or no
    """

    if not grpc_settings.PRIVATE_KEY_CERTIFICATE_CHAIN_PAIRS_PATH:
        return None

    private_key_certificate_chain_pairs = map_certificate_path_to_file_content()

    root_certificates = None
    if grpc_settings.ROOT_CERTIFICATES_PATH:
        root_certificates = load_credential_from_file(grpc_settings.ROOT_CERTIFICATES_PATH)

    return grpc.ssl_server_credentials(
        private_key_certificate_chain_pairs=private_key_certificate_chain_pairs,
        root_certificates=root_certificates,
        require_client_auth=grpc_settings.REQUIRE_CLIENT_AUTH,
    )
