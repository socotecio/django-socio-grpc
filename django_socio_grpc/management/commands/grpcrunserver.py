import errno
import logging
import os
import signal
import sys
import time
from concurrent import futures
from time import perf_counter

import grpc
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import autoreload
from grpc_health.v1 import health, health_pb2_grpc

from django_socio_grpc.settings import grpc_settings
from django_socio_grpc.utils.ssl_credentials import get_server_credentials

logger = logging.getLogger("django_socio_grpc.internal")


class Command(BaseCommand):
    help = "Starts a gRPC server."

    # Validation is called explicitly each time the server is reloaded.
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "address",
            nargs="?",
            default=f"[::]:{grpc_settings.GRPC_CHANNEL_PORT}",
            help="Optional address for which to open a port.",
        )
        parser.add_argument(
            "--max-workers",
            type=int,
            default=10,
            dest="max_workers",
            help="Number of maximum worker threads.",
        )
        parser.add_argument(
            "--grace-period",
            type=float,
            default=10.0,
            help="Time of grace period when receiving a SIGTERM signal.",
        )
        parser.add_argument(
            "--dev",
            action="store_true",
            dest="development_mode",
            help=(
                "Run the server in development mode.  This tells Django to use "
                "the auto-reloader and run checks."
            ),
        )

    def handle(self, *args, **options):
        """
        GRPC Server main Handle
        """

        self.address = options["address"]
        self.development_mode = options["development_mode"]
        self.max_workers = options["max_workers"]
        self.grace_period = options["grace_period"]
        self.server = None

        # set GRPC_ASYNC to "False" in order to start server synchronously
        grpc_settings.GRPC_ASYNC = False

        # Set up signal handler after server is created
        signal.signal(
            signal.SIGTERM,
            lambda signum, frame: self.stop_server(grace_period=self.grace_period),
        )

        self.run(**options)

    def run(self, **options):
        """Run the server, using the autoreloader if needed."""
        if self.development_mode:
            if hasattr(autoreload, "run_with_reloader"):
                autoreload.run_with_reloader(self.inner_run, **options)
            else:
                autoreload.main(self.inner_run, None, options)
        else:
            self._serve()

    def stop_server(self, grace_period: float = 10.0):
        logger.info(
            f"Shutdown signal received (KeyboardInterrupt/SIGTERM), shutting down the server gracefully with {grace_period=}..."
        )
        start_time = time.time()
        try:
            if self.server:
                self.server.stop(grace=grace_period)
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")
        elapsed_time = time.time() - start_time
        logger.info(f"Server gracefully shut down with  in {elapsed_time:.2f} seconds.")

    def _serve(self):
        try:
            logger.info(
                (f"Starting gRPC server at {self.address}... \n"),
                extra={"emit_to_server": False},
            )
            server_launch_time = perf_counter()
            # ----------------------------------------------
            # --- Instantiate the gRPC server itself     ---
            server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=self.max_workers),
                interceptors=grpc_settings.SERVER_INTERCEPTORS,
                options=grpc_settings.SERVER_OPTIONS,
            )
            self.server = server

            if grpc_settings.ENABLE_HEALTH_CHECK:
                health_pb2_grpc.add_HealthServicer_to_server(health.HealthServicer(), server)

            # ------------------------------------------------------------
            # ---  add PB2 GRPC handler (Services) to the gRPC server  ---
            grpc_settings.ROOT_HANDLERS_HOOK(server)

            # ------------------------------------------------
            # ---  common start of the gRPC server itself  ---
            ssl_server_credentials = get_server_credentials()
            if ssl_server_credentials:
                server.add_secure_port(self.address, ssl_server_credentials)
            else:
                server.add_insecure_port(self.address)
            server.start()
            server_launched_time = perf_counter()
            logger.info(
                f"Server started in {server_launched_time - server_launch_time} second and is now ready to accept incoming request"
            )
            server.wait_for_termination()
        except OSError as e:
            # Use helpful error messages instead of ugly tracebacks.
            ERRORS = {
                errno.EACCES: "You don't have permission to access that port.",
                errno.EADDRINUSE: "That port is already in use.",
                errno.EADDRNOTAVAIL: "That IP address can't be assigned to.",
            }
            try:
                error_text = ERRORS[e.errno]
            except KeyError:
                error_text = e
            error_data = f"Error: {error_text}"
            logger.error(error_data)
            # Need to use an OS exit because sys.exit doesn't work in a thread
            os._exit(1)

        # ---------------------------------------
        # ----  EXIT OF GRPC SERVER           ---
        except KeyboardInterrupt:
            # Shuts down the server with 0 seconds of grace period because it's an user interrupt action.
            self.stop_server(grace_period=0)

    def inner_run(self, *args, **options):
        # ------------------------------------------------------------------------
        # If an exception was silenced in ManagementUtility.execute in order
        # to be raised in the child process, raise it now.
        # ------------------------------------------------------------------------
        autoreload.raise_last_exception()
        logger.info('"Performing system checks...\n\n')
        self.check(display_num_errors=True)

        # -----------------------------------------------------------
        # Need to check migrations here, so can't use the
        # requires_migrations_check attribute.
        # -----------------------------------------------------------
        self.check_migrations()
        quit_command = "CTRL-BREAK" if sys.platform == "win32" else "CONTROL-C"
        server_start_data = (
            f"Django version {self.get_version()}, using settings {settings.SETTINGS_MODULE}\n"
            f"Starting development gRPC server at {self.address}\n"
            f"Quit the server with {quit_command}s.\n"
        )

        # --------------------------------------------
        # ---  START GRPC   SERVER                 ---
        # --------------------------------------------
        logger.info(server_start_data)
        self._serve()
