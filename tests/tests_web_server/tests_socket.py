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
import socket
from unittest.mock import MagicMock, patch

import pytest

from lib.error_status import PngHttpPortInUseError
from lib.web_server.socket import get_socket_for_uvicorn

# ----------------------------------------------------------------------------------------------------------------------

pytestmark = pytest.mark.serial


class TestGetSocketForUvicorn:

    def test_returns_non_blocking_socket(self):
        sock = get_socket_for_uvicorn(port=0, host="127.0.0.1")
        try:
            assert isinstance(sock, socket.socket)
            # Non-blocking sockets have a timeout of 0.0
            assert sock.gettimeout() == 0.0
        finally:
            sock.close()

    def test_returned_socket_is_listening(self):
        sock = get_socket_for_uvicorn(port=0, host="127.0.0.1")
        try:
            # Confirm the OS assigned a real port (> 0)
            bound_port = sock.getsockname()[1]
            assert bound_port > 0
        finally:
            sock.close()

    def test_port_in_use_raises_png_error(self):
        # Bind a socket to a port, then try to bind the same port again.
        holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            holder.bind(("127.0.0.1", 0))
            holder.listen(1)
            used_port = holder.getsockname()[1]
            with pytest.raises(PngHttpPortInUseError):
                get_socket_for_uvicorn(port=used_port, host="127.0.0.1")
        finally:
            holder.close()

    def test_other_oserror_is_reraised(self):
        # Simulate an OSError that is NOT a port-in-use error (e.g. EACCES on a
        # privileged port - errno 13 on Linux, but NOT the Windows 10013 variant
        # we treat as port-in-use). We patch sock.bind to raise a generic OSError.
        generic_err = OSError(errno.ENOENT, "no such file or directory")
        with patch("lib.web_server.socket.socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock_cls.return_value = mock_sock
            mock_sock.bind.side_effect = generic_err
            with pytest.raises(OSError) as exc_info:
                get_socket_for_uvicorn(port=9999, host="127.0.0.1")
            assert exc_info.value is generic_err
