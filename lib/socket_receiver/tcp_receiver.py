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

import asyncio
import socket
import struct

from .base_receiver import TelemetryReceiver

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TcpReceiver(TelemetryReceiver):
    """This class represents a TCP server that handles one connection at a time.
    Attributes:
    - m_buffer_size - The buffer size being used
    - m_port - The TCP port that this server is bound to
    - m_bind_ip - The IP address this TCP server is bound to
    - m_socket - The socket object handle associated with this server
    - m_connection - The current connection object
    Methods:
    - getNextMessage()
    """
    def __init__(self, port: int, bind_ip: str, buffer_size: int = 16384) -> None:
        """Construct a TCPListener object
        Args:
            port (int): The port number to initialise this server to
            bind_ip (str): The IP address this server must be bound to
            buffer_size (int, optional): The buffer size to be specified. Defaults to 16 kb.
        """
        self.m_buffer_size = buffer_size
        self.m_port = port
        self.m_bind_ip = bind_ip

        # Create and configure the server socket
        self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.m_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.m_socket.bind((self.m_bind_ip, self.m_port))
        self.m_socket.listen(1)  # One connection queue
        self.m_socket.setblocking(False)  # Non-blocking mode

        self.m_connection = None
        self._reader = None
        self._writer = None

    async def getNextMessage(self) -> bytes:
        """
        Asynchronously waits until the next message arrives on the current connection
        or establishes a new connection, then returns it.
        Returns:
        bytes: The raw bytes that were received.
        """
        # Accept a new connection if needed
        if self.m_connection is None:
            try:
                # Wait for a connection - this yields to the event loop
                conn, _ = await asyncio.get_event_loop().sock_accept(self.m_socket)
                self.m_connection = conn
                self.m_connection.setblocking(False)
                # Use streams for easier reading
                self._reader, self._writer = await asyncio.open_connection(sock=conn)
            except (OSError) as e:
                print(f"Connection error: {e}")
                return await self.getNextMessage()  # Try again
            except asyncio.CancelledError:
                # Propagate the cancellation
                raise

        try:
            # Read length prefix (4 bytes)
            length_bytes = await self._reader.readexactly(4)
            message_length = struct.unpack('!I', length_bytes)[0]

            # Read the message of specified length
            return await self._reader.readexactly(message_length)

        except (asyncio.IncompleteReadError, ConnectionError):
            # Connection closed or error
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
            self.m_connection = None
            self._reader = None
            self._writer = None

            # Try again with a new connection
            return await self.getNextMessage()

        except asyncio.CancelledError:
            # Propagate the cancellation
            raise

    async def close(self) -> None:
        """Closes the socket receiver and any active connection."""
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()

        if self.m_socket:
            self.m_socket.close()

        self.m_connection = None
        self._reader = None
        self._writer = None

        self.m_socket = None