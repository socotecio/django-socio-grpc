import asyncio
import signal
from unittest import mock

import grpc
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings

from django_socio_grpc.management.commands.grpcrunaioserver import Command
from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.tests.utils import patch_open


class TestRunServer(TestCase):
    @override_settings(
        GRPC_FRAMEWORK={
            **settings.GRPC_FRAMEWORK,
            "ROOT_HANDLERS_HOOK": mock.AsyncMock(),
        }
    )
    @mock.patch("grpc.aio.server")
    def test_server_launch(self, grpc_aio_server_mock):
        """
        Testing that the grpc server is lauching in its more basic way.
        It verifies that all the needed grpc methods are correctly called
        """
        # Mocking
        fake_async_aio_server = mock.MagicMock(spec=grpc.aio._server.Server)
        grpc_aio_server_mock.return_value = fake_async_aio_server

        # launch command
        call_command("grpcrunaioserver")

        # assert handler function launched
        grpc_settings.ROOT_HANDLERS_HOOK.assert_called_with(fake_async_aio_server)

        # assert grpc server launch with corrects args
        grpc_aio_server_mock.assert_called_with(mock.ANY, interceptors=None, options=None)

        # assert we addes the insecure port correctly
        fake_async_aio_server.add_insecure_port.assert_called_with("[::]:50051")
        # Asser we call the start and wait_for_termination function to be sure server is running
        fake_async_aio_server.start.assert_called()
        fake_async_aio_server.wait_for_termination.assert_called()

        # Verify that GRPC_ASYNC settings is correctly set to True
        self.assertTrue(grpc_settings.GRPC_ASYNC)

    @override_settings(
        GRPC_FRAMEWORK={
            **settings.GRPC_FRAMEWORK,
            "ROOT_HANDLERS_HOOK": mock.MagicMock(),
        }
    )
    @mock.patch("grpc.aio.server")
    def test_server_launch_handler_sync(self, grpc_aio_server_mock):
        """
        Just testing that grpcrunaioserver also work with a sync handler
        """
        # Mocking
        fake_async_aio_server = mock.MagicMock(spec=grpc.aio._server.Server)
        grpc_aio_server_mock.return_value = fake_async_aio_server

        # launch command
        call_command("grpcrunaioserver")

        # assert handler function launched
        grpc_settings.ROOT_HANDLERS_HOOK.assert_called_with(fake_async_aio_server)

        # Verify that GRPC_ASYNC settings is correctly set to True
        self.assertTrue(grpc_settings.GRPC_ASYNC)

    @override_settings(
        GRPC_FRAMEWORK={
            **settings.GRPC_FRAMEWORK,
            "ROOT_HANDLERS_HOOK": mock.AsyncMock(),
            "SERVER_INTERCEPTORS": ["FakeInterceptor"],
            "SERVER_OPTIONS": [
                ("grpc.max_metadata_size", 1024 * 1024),
                ("grpc.max_send_message_length", 100 * 1024 * 1024),
                ("grpc.max_receive_message_length", 100 * 1024 * 1024),
            ],
        }
    )
    @mock.patch("grpc.aio.server")
    def test_server_launch_with_interceptors_and_options(self, grpc_aio_server_mock):
        """
        Testing that the grpc server is lauching with interceptors and options passed as settings
        """
        # Mocking
        fake_async_aio_server = mock.MagicMock(spec=grpc.aio._server.Server)
        grpc_aio_server_mock.return_value = fake_async_aio_server

        # launch command
        call_command("grpcrunaioserver")

        # assert grpc server launch with corrects args
        grpc_aio_server_mock.assert_called_with(
            mock.ANY,
            interceptors=["FakeInterceptor"],
            options=[
                ("grpc.max_metadata_size", 1048576),
                ("grpc.max_send_message_length", 104857600),
                ("grpc.max_receive_message_length", 104857600),
            ],
        )

    @override_settings(
        GRPC_FRAMEWORK={
            **settings.GRPC_FRAMEWORK,
            "ROOT_HANDLERS_HOOK": mock.AsyncMock(),
            "PRIVATE_KEY_CERTIFICATE_CHAIN_PAIRS_PATH": [("server-key.pem", "server.pem")],
        }
    )
    @mock.patch("grpc.aio.server")
    @mock.patch("grpc.ssl_server_credentials")
    def test_secure_connection(self, mock_ssl_server_credentials, grpc_aio_server_mock):
        """
        Testing that if PRIVATE_KEY_CERTIFICATE_CHAIN_PAIRS_PATH correctly set then we launch a secure server
        """

        # Mocking
        fake_async_aio_server = mock.MagicMock(spec=grpc.aio._server.Server)
        grpc_aio_server_mock.return_value = fake_async_aio_server

        server_credentials_fake_return_value = "Fake"
        mock_ssl_server_credentials.return_value = server_credentials_fake_return_value

        read_file_mock_data = "fakefiledata"

        with patch_open(read_data=read_file_mock_data) as mocked_open:
            # launch command
            call_command("grpcrunaioserver")

        # verfiy open mock to be sure cert file are correctly read and passed to ssl_server_credentials
        """
        mocked_open.mock_calls look like:
        [call('server-key.pem', 'rb'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call('server.pem', 'rb'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None)
        ]
        don't ask me why
        """
        self.assertEqual(mocked_open.mock_calls[0].args[0], "server-key.pem")
        self.assertEqual(mocked_open.mock_calls[0].args[1], "rb")

        self.assertEqual(mocked_open.mock_calls[4].args[0], "server.pem")
        self.assertEqual(mocked_open.mock_calls[4].args[1], "rb")

        # verfiy that we added a secure port
        fake_async_aio_server.add_secure_port.assert_called_with(
            "[::]:50051", server_credentials_fake_return_value
        )

        # assert ssl_server_credentials has been called with correct arguments
        mock_ssl_server_credentials.assert_called_with(
            private_key_certificate_chain_pairs=[[read_file_mock_data, read_file_mock_data]],
            root_certificates=None,
            require_client_auth=False,
        )

    @override_settings(
        GRPC_FRAMEWORK={
            **settings.GRPC_FRAMEWORK,
            "ROOT_HANDLERS_HOOK": mock.AsyncMock(),
            "PRIVATE_KEY_CERTIFICATE_CHAIN_PAIRS_PATH": [("server-key.pem", "server.pem")],
            "ROOT_CERTIFICATES_PATH": "certificates.pem",
            "REQUIRE_CLIENT_AUTH": True,
        }
    )
    @mock.patch("grpc.aio.server")
    @mock.patch("grpc.ssl_server_credentials")
    def test_secure_connection_with_certificate_paths(
        self, mock_ssl_server_credentials, grpc_aio_server_mock
    ):
        """
        Testing that if ROOT_CERTIFICATES_PATH and REQUIRE_CLIENT_AUTH correctly set then we set them with the secure server
        """

        # Mocking
        fake_async_aio_server = mock.MagicMock(spec=grpc.aio._server.Server)
        grpc_aio_server_mock.return_value = fake_async_aio_server

        server_credentials_fake_return_value = "Fake"
        mock_ssl_server_credentials.return_value = server_credentials_fake_return_value

        read_file_mock_data = "fakefiledata"

        with patch_open(read_data=read_file_mock_data) as mocked_open:
            # launch command
            call_command("grpcrunaioserver")

        # verfiy open mock to be sure cert file are correctly read and passed to ssl_server_credentials
        """
        mocked_open.mock_calls look like:
        [
            call('server-key.pem', 'rb'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call('server.pem', 'rb'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None),
            call('certificates.pem', 'rb'),
            call().__enter__(),
            call().read(),
            call().__exit__(None, None, None)
        ]
        don't ask me why
        """
        self.assertEqual(mocked_open.mock_calls[0].args[0], "server-key.pem")
        self.assertEqual(mocked_open.mock_calls[0].args[1], "rb")

        self.assertEqual(mocked_open.mock_calls[4].args[0], "server.pem")
        self.assertEqual(mocked_open.mock_calls[4].args[1], "rb")

        self.assertEqual(mocked_open.mock_calls[8].args[0], "certificates.pem")
        self.assertEqual(mocked_open.mock_calls[8].args[1], "rb")

        # verfiy that we added a secure port
        fake_async_aio_server.add_secure_port.assert_called_with(
            "[::]:50051", server_credentials_fake_return_value
        )

        # assert ssl_server_credentials has been called with correct arguments
        mock_ssl_server_credentials.assert_called_with(
            private_key_certificate_chain_pairs=[[read_file_mock_data, read_file_mock_data]],
            root_certificates=read_file_mock_data,
            require_client_auth=True,
        )

    @mock.patch("signal.signal")
    @mock.patch("grpc.aio.server")
    @override_settings(
        GRPC_FRAMEWORK={
            **settings.GRPC_FRAMEWORK,
            "ROOT_HANDLERS_HOOK": mock.AsyncMock(),
        }
    )
    def test_sigterm_signal_handler_setup(self, grpc_aio_server_mock, signal_mock):
        """Test that SIGTERM signal handler is properly set up."""
        fake_async_aio_server = mock.MagicMock(spec=grpc.aio._server.Server)
        grpc_aio_server_mock.return_value = fake_async_aio_server

        # Launch command
        call_command("grpcrunaioserver", grace_period=10.0)

        # Verify signal handler was set up for SIGTERM in handle method
        # Check all calls to signal.signal() for SIGTERM
        sigterm_calls = [
            call for call in signal_mock.call_args_list if call[0][0] == signal.SIGTERM
        ]
        self.assertTrue(len(sigterm_calls) > 0, "SIGTERM signal handler was not set up")

        # Verify the SIGTERM handler is callable
        sigterm_call = sigterm_calls[0]
        self.assertTrue(callable(sigterm_call[0][1]))

    @mock.patch("signal.signal")
    @mock.patch("grpc.aio.server")
    @override_settings(
        GRPC_FRAMEWORK={
            **settings.GRPC_FRAMEWORK,
            "ROOT_HANDLERS_HOOK": mock.AsyncMock(),
        }
    )
    def test_sigterm_signal_calls_stop_server_with_grace_period(
        self, grpc_aio_server_mock, signal_mock
    ):
        """Test that SIGTERM signal handler calls stop_server with configured grace period."""

        fake_async_aio_server = mock.MagicMock(spec=grpc.aio._server.Server)
        grpc_aio_server_mock.return_value = fake_async_aio_server

        with mock.patch.object(Command, "stop_server") as mock_stop_server:
            # Mock the async method to return an AsyncMock
            mock_stop_server.return_value = mock.AsyncMock()

            # Launch command with specific grace period
            call_command("grpcrunaioserver", grace_period=15.0)

            # Extract the SIGTERM signal handler that was registered
            sigterm_calls = [
                call for call in signal_mock.call_args_list if call[0][0] == signal.SIGTERM
            ]
            self.assertTrue(len(sigterm_calls) > 0, "SIGTERM signal handler was not set up")

            signal_handler = sigterm_calls[0][0][1]

            # Simulate SIGTERM signal being received
            signal_handler(signal.SIGTERM, None)

            # Verify stop_server was called with the configured grace period
            mock_stop_server.assert_called_with(grace_period=15.0)

    @mock.patch("grpc.aio.server")
    @override_settings(
        GRPC_FRAMEWORK={
            **settings.GRPC_FRAMEWORK,
            "ROOT_HANDLERS_HOOK": mock.AsyncMock(),
        }
    )
    def test_keyboard_interrupt_calls_stop_server_with_zero_grace(self, grpc_aio_server_mock):
        """Test that KeyboardInterrupt calls stop_server with 0 grace period (immediate shutdown)."""
        fake_async_aio_server = mock.MagicMock(spec=grpc.aio._server.Server)
        grpc_aio_server_mock.return_value = fake_async_aio_server

        # Mock wait_for_termination to raise KeyboardInterrupt
        fake_async_aio_server.wait_for_termination.side_effect = KeyboardInterrupt()

        with mock.patch.object(Command, "stop_server") as mock_stop_server:
            # Mock the async method to return an AsyncMock
            mock_stop_server.return_value = mock.AsyncMock()

            # Launch command and expect KeyboardInterrupt to be handled
            call_command("grpcrunaioserver", grace_period=10.0)

            # Verify stop_server was called with 0 grace period (immediate shutdown for user interrupt)
            mock_stop_server.assert_called_with(grace_period=0)

    def test_stop_server_method_calls_server_stop_correctly(self):
        """Test that the stop_server method calls server.stop() with the correct grace period."""
        command = Command()
        mock_server = mock.AsyncMock()
        command.server = mock_server  # Set the server on the command instance

        grace_period = 30.0
        mock_server.reset_mock()

        # Run the async method
        async def run_test():
            await command.stop_server(grace_period=grace_period)

        asyncio.run(run_test())

        # Verify server.stop was called with correct grace period
        mock_server.stop.assert_called_once_with(grace=grace_period)
