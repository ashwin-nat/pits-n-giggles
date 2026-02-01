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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import socket
import platform
from lib.error_status import is_port_in_use_error, PngHttpPortInUseError

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_socket_for_uvicorn(port: int) -> socket.socket:
    """Get a socket for Uvicorn to use. Handles port in use error.

    Args:
        port (int): The port to bind to.

    Returns:
        socket.socket: The socket object.

    Raises:
        PngHttpPortInUseError: If the specified port is already in use.
        OSError: If the server fails to start and error is not a port in use error.
    """

    # Create a socket manually
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Platform-specific socket options:
    # - Unix/Linux/macOS: SO_REUSEADDR allows binding to TIME_WAIT ports (safe for quick restart)
    if platform.system() == "Windows":
        # SO_EXCLUSIVEADDRUSE prevents binding to a port already in use on Windows.
        # Without it, bind() silently succeeds even if another socket owns the port.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    else:
        # Unix/Linux/macOS: SO_REUSEADDR allows binding to TIME_WAIT ports (safe for quick restart)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(("0.0.0.0", port))
    except OSError as e:
        sock.close()
        if is_port_in_use_error(e.errno):
            raise PngHttpPortInUseError() from e
        raise  # Re-raise if it's a different OSError

    sock.listen(1024)
    sock.setblocking(False)
    return sock
