# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
from logging import Logger
from typing import Dict, List, Optional, Set, Tuple

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class AsyncUDPTransport:
    """Abstraction layer for UDP transport management."""
    def __init__(self, forward_addresses: List[Tuple[str, int]], logger: Logger = None):
        """
        Initialize transports for known destinations synchronously.

        :param forward_addresses: List of (IP, Port) tuples to initialize transports for
        :param logger: Logger
        """
        self.m_transports: Dict[Tuple[str, int], asyncio.DatagramTransport] = {}
        self.m_sockets: Dict[Tuple[str, int], socket.socket] = {}
        self.m_logger = logger

        for destination in forward_addresses:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setblocking(False)
                sock.connect(destination)
                self.m_sockets[destination] = sock
            except OSError as e:
                if self.m_logger:
                    self.m_logger.error("Error creating socket to %s: %s", destination, e)
                self.close()
                raise

    def close(self) -> None:
        """Safely close all sockets."""
        for destination, sock in list(self.m_sockets.items()):
            try:
                sock.close()
            except OSError as e:
                if self.m_logger:
                    self.m_logger.error("Error closing socket to %s: %s", destination, e)

    def update_targets(self, new_targets: List[Tuple[str, int]]) -> None:
        """Update forwarding destinations without restarting the task.

        This method is intentionally synchronous — no await means asyncio's cooperative
        scheduler cannot interleave it with concurrent send() calls, so no lock is needed.
        Any in-flight sock_sendall on a removed socket will raise OSError, which
        _send_to_destination already catches and logs.

        :param new_targets: The complete new list of (host, port) destinations.
        """
        new_set: Set[Tuple[str, int]] = set(new_targets)
        old_set: Set[Tuple[str, int]] = set(self.m_sockets.keys())

        for dest in new_set - old_set:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setblocking(False)
                sock.connect(dest)
                self.m_sockets[dest] = sock
            except OSError as e:
                if self.m_logger:
                    self.m_logger.error("Error creating socket to %s: %s", dest, e)
                raise

        for dest in old_set - new_set:
            old_sock = self.m_sockets.pop(dest)
            try:
                old_sock.close()
            except OSError as e:
                if self.m_logger:
                    self.m_logger.error("Error closing socket to %s: %s", dest, e)

    async def send(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Send data to the specified destination.

        :param data: Bytes to send
        :param destination: Destination (IP, Port)
        """
        sock: Optional[socket.socket] = self.m_sockets.get(destination)
        if sock is None:
            return

        loop = asyncio.get_running_loop()
        await loop.sock_sendall(sock, data)

class AsyncUDPForwarder:
    def __init__(self, forward_addresses: List[Tuple[str, int]], logger: Logger = None):
        """
        Initializes the AsyncUDPForwarder with forwarding destinations.

        :param forward_addresses: A list of tuples, each consisting of an IP address
                                  and a port number to forward packets to.
        :param logger: Logger
        """
        self.m_forward_addresses = forward_addresses
        self.m_transport = AsyncUDPTransport(forward_addresses, logger)
        self.m_logger = logger

    async def forward(self, data: bytes) -> None:
        """
        Concurrently forwards the given data to all configured destinations.

        :param data: The data (bytes) to forward
        """
        if not self.m_forward_addresses:
            return

        await asyncio.gather(*(
            self._send_to_destination(data, dest)
            for dest in self.m_forward_addresses
        ))

    async def _send_to_destination(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Send data to a single destination and handle potential OS-level errors.

        :param data: The data to send
        :param destination: The destination (IP, Port)
        """
        try:
            await self.m_transport.send(data, destination)
        except OSError as e:
            if self.m_logger:
                self.m_logger.error("Error forwarding packet to %s: %s", destination, e)

    def update_targets(self, new_targets: List[Tuple[str, int]]) -> None:
        """Update forwarding destinations at runtime without restarting.

        :param new_targets: The complete new list of (host, port) destinations.
        """
        self.m_forward_addresses = new_targets
        self.m_transport.update_targets(new_targets)

    def close(self) -> None:
        """Safely close the transport."""
        self.m_transport.close()
