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
from typing import Awaitable, Callable, Optional

from .base_receiver import TelemetryTransport

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TcpTransport(TelemetryTransport):
    """TCP server transport that handles one connection at a time.

    Attributes:
        m_buffer_size (int): The buffer size being used.
        m_port (int): The TCP port that this server is bound to.
        m_bind_ip (str): The IP address this TCP server is bound to.
        m_socket (socket.socket): The socket object handle associated with this server.
        m_connection: The current connection object.
    """

    def __init__(self, port: int, bind_ip: str, buffer_size: int = 16384) -> None:
        """
        Args:
            port (int): The port number to initialise this server to.
            bind_ip (str): The IP address this server must be bound to.
            buffer_size (int, optional): The buffer size to be specified. Defaults to 16 kb.
        """
        self.m_buffer_size = buffer_size
        self.m_port = port
        self.m_bind_ip = bind_ip

        self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.m_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.m_socket.bind((self.m_bind_ip, self.m_port))
        self.m_socket.listen(1)
        self.m_socket.setblocking(False)

        self.m_connection = None
        self._reader = None
        self._writer = None
        self._callback: Optional[Callable[[bytes], Awaitable[None]]] = None

    def on_packet(self, callback: Callable[[bytes], Awaitable[None]]) -> Callable[[bytes], Awaitable[None]]:
        """Decorator to register the packet callback."""
        self._callback = callback
        return callback

    async def run(self) -> None:
        """Run until cancelled, delivering packets to the registered callback."""
        while True:
            await self._ensure_connection()
            try:
                length_bytes = await self._reader.readexactly(4)
                message_length = struct.unpack('!I', length_bytes)[0]
                message = await self._reader.readexactly(message_length)
                await self._callback(message)
            except (asyncio.IncompleteReadError, ConnectionError):
                await self._drop_connection()

    async def _ensure_connection(self) -> None:
        """Accept a new connection if none is active."""
        if self.m_connection is not None:
            return
        try:
            conn, _ = await asyncio.get_event_loop().sock_accept(self.m_socket)
            self.m_connection = conn
            self.m_connection.setblocking(False)
            self._reader, self._writer = await asyncio.open_connection(sock=conn)
        except OSError as e:
            print(f"Connection error: {e}")
            await self._ensure_connection()

    async def _drop_connection(self) -> None:
        """Close and forget the current connection."""
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except ConnectionResetError:
                pass
        self.m_connection = None
        self._reader = None
        self._writer = None

    async def close(self) -> None:
        """Close the transport and any active connection."""
        await self._drop_connection()
        if self.m_socket:
            self.m_socket.close()
        self.m_socket = None
