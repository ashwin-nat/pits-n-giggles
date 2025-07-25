
from contextlib import closing
import socket
import os
import sys
import platform

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.port_check import is_port_available

# ----------------------------------------------------------------------------------------------------------------------

class TestPortAvailability(F1TelemetryUnitTestsBase):

    def test_available_port(self):
        """Test that a random unused port is reported as available."""
        # Use a port temporarily to find a free one, then release it before testing
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as temp_sock:
            temp_sock.bind(('127.0.0.1', 0))  # Let OS pick an unused port
            free_port = temp_sock.getsockname()[1]

        # Now it should be available to bind again
        self.assertTrue(is_port_available(free_port), f"Expected port {free_port} to be available")

    def test_unavailable_port(self):
        """Test that a port currently bound is reported as unavailable."""
        bound_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if platform.system() == "Windows":
                bound_sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            bound_sock.bind(('127.0.0.1', 0))
            used_port = bound_sock.getsockname()[1]
            bound_sock.listen(1)

            self.assertFalse(is_port_available(used_port), f"Expected port {used_port} to be unavailable")
        finally:
            bound_sock.close()
