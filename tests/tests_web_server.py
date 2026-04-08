# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# pylint: skip-file

import errno
import logging
import os
import socket
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.error_status import PngHttpPortInUseError
from lib.web_server.server import BaseWebServer
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestWebServerBase(F1TelemetryUnitTestsBase):
    """Base class for web server tests."""

class TestSocketBinding(TestWebServerBase):
    """Test socket creation and multi-port binding logic."""

    def _make_server(self, additional_ports=None, bind_address="0.0.0.0"):
        """Create a BaseWebServer with mocked internals to isolate socket logic."""
        logger = logging.getLogger("test_web_server")
        with patch.object(BaseWebServer, '__init__', lambda self_, *a, **kw: None):
            server = BaseWebServer.__new__(BaseWebServer)
            server.m_logger = logger
            server.m_port = 8000
            server.m_additional_ports = additional_ports or []
            server.m_port_labels = {e["port"]: e.get("label", "") for e in server.m_additional_ports}
            server.m_cert_path = None
            server.m_key_path = None
            server.m_bind_address = bind_address
            server.m_sio_app = MagicMock()
            server._post_start_callback = None
            server.m_app = MagicMock()
            return server

    def test_create_socket_success(self):
        """_create_socket returns a socket on successful bind."""
        server = self._make_server()
        with patch('lib.web_server.server.socket.socket') as MockSocket:
            mock_sock = MagicMock()
            MockSocket.return_value = mock_sock

            result = server._create_socket(9000)

            self.assertIs(result, mock_sock)
            mock_sock.bind.assert_called_once_with(("0.0.0.0", 9000))
            mock_sock.listen.assert_called_once_with(1024)
            mock_sock.setblocking.assert_called_once_with(False)

    def test_create_socket_port_in_use_returns_none(self):
        """_create_socket returns None when port is already in use."""
        server = self._make_server()
        with patch('lib.web_server.server.socket.socket') as MockSocket:
            mock_sock = MagicMock()
            MockSocket.return_value = mock_sock
            mock_sock.bind.side_effect = OSError(98, "Address already in use")

            result = server._create_socket(9000)

            self.assertIsNone(result)
            mock_sock.close.assert_called_once()

    def test_create_socket_other_os_error_raises(self):
        """_create_socket re-raises OSError for non-port-in-use errors."""
        server = self._make_server()
        with patch('lib.web_server.server.socket.socket') as MockSocket:
            mock_sock = MagicMock()
            MockSocket.return_value = mock_sock
            mock_sock.bind.side_effect = OSError(13, "Permission denied")

            with self.assertRaises(OSError) as ctx:
                server._create_socket(9000)

            self.assertEqual(ctx.exception.errno, 13)
            mock_sock.close.assert_called_once()

    async def test_run_primary_port_in_use_raises(self):
        """run() raises PngHttpPortInUseError when primary port is busy."""
        server = self._make_server()
        with patch.object(server, '_create_socket', return_value=None):
            with self.assertRaises(PngHttpPortInUseError):
                await server.run()

    async def test_run_additional_port_failure_skipped(self):
        """run() skips additional ports that fail to bind, continues with primary."""
        server = self._make_server(additional_ports=[
            {"port": 8001, "label": "Session 2"},
            {"port": 8002, "label": "Session 3"},
        ])

        primary_sock = MagicMock()
        extra_sock_ok = MagicMock()

        def fake_create_socket(port):
            if port == 8000:
                return primary_sock
            if port == 8001:
                return None  # simulate failure
            if port == 8002:
                return extra_sock_ok
            return None

        with patch.object(server, '_create_socket', side_effect=fake_create_socket), \
             patch('lib.web_server.server.uvicorn') as mock_uvicorn:
            mock_server_instance = MagicMock()
            mock_server_instance.serve = MagicMock(return_value=None)
            # Make serve a coroutine
            async def fake_serve(sockets=None):
                pass
            mock_server_instance.serve = fake_serve
            mock_uvicorn.Config.return_value = MagicMock()
            mock_uvicorn.Server.return_value = mock_server_instance

            await server.run()

            # Uvicorn should have been called with primary + 8002 (8001 skipped)
            # Server.serve was called — verify via mock_uvicorn.Server
            mock_uvicorn.Server.assert_called_once()

    def test_create_socket_uses_bind_address(self):
        """_create_socket binds to configured bind_address instead of hardcoded 0.0.0.0."""
        server = self._make_server(bind_address="127.0.0.1")
        with patch('lib.web_server.server.socket.socket') as MockSocket:
            mock_sock = MagicMock()
            MockSocket.return_value = mock_sock
            result = server._create_socket(9000)
            self.assertIs(result, mock_sock)
            mock_sock.bind.assert_called_once_with(("127.0.0.1", 9000))

    def test_cors_wildcard_when_bind_all(self):
        """CORS returns '*' when bound to 0.0.0.0 (LAN mode)."""
        server = self._make_server(bind_address="0.0.0.0")
        self.assertEqual(server._compute_cors_origins(), "*")

    def test_cors_restricted_when_localhost(self):
        """CORS returns restricted origins when bound to 127.0.0.1."""
        server = self._make_server(bind_address="127.0.0.1")
        origins = server._compute_cors_origins()
        self.assertIsInstance(origins, list)
        self.assertIn("http://localhost:8000", origins)
        self.assertIn("http://127.0.0.1:8000", origins)

    def test_cors_restricted_includes_additional_ports(self):
        """CORS restricted origins include additional ports."""
        server = self._make_server(
            bind_address="127.0.0.1",
            additional_ports=[{"port": 8001, "label": "S2"}]
        )
        origins = server._compute_cors_origins()
        self.assertIn("http://localhost:8001", origins)
        self.assertIn("http://127.0.0.1:8001", origins)

    def test_cors_restricted_with_https(self):
        """CORS restricted origins use https scheme when cert_path is set."""
        server = self._make_server(bind_address="127.0.0.1")
        server.m_cert_path = "/path/to/cert.pem"
        origins = server._compute_cors_origins()
        self.assertIn("https://localhost:8000", origins)
        self.assertIn("https://127.0.0.1:8000", origins)
