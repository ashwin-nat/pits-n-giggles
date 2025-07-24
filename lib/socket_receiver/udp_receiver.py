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

from .base_receiver import TelemetryReceiver

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class UdpReceiver(TelemetryReceiver):
    """An async-friendly UDP socket listener.

    Attributes:
        m_buffer_size (int): The buffer size used for receiving data.
        m_port (int): The UDP port this client is bound to.
        m_bind_ip (str): The IP address this client is bound to.
        m_socket (socket.socket): The underlying UDP socket object.
    """

    def __init__(self, port: int, bind_ip: str, buffer_size: int = 16384) -> None:
        """
        Initialize the UDP listener.

        Args:
            port (int): Port number to bind to.
            bind_ip (str): IP address to bind to (e.g., '127.0.0.1').
            buffer_size (int, optional): Size of the receive buffer. Defaults to 16384 bytes.
        """
        self.m_buffer_size = buffer_size
        self.m_port = port
        self.m_bind_ip = bind_ip
        self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.m_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.m_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.m_socket.setblocking(False)
        self.m_socket.bind((self.m_bind_ip, self.m_port))
        self._loop = asyncio.get_event_loop()

    async def getNextMessage(self) -> bytes:
        """
        Wait asynchronously for the next UDP message.

        Returns:
            bytes: The raw message bytes.
        """
        message, _ = await self._loop.sock_recvfrom(self.m_socket, self.m_buffer_size)
        return message

    async def close(self) -> None:
        """
        Close the UDP socket.
        """
        self.m_socket.close()
