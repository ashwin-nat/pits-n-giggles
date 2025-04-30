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
from types import MappingProxyType
from typing import Dict, List, Tuple

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class UDPForwarder:
    def __init__(self, forward_addresses: List[Tuple[str, int]], logger: Logger = None):
        """
        Initializes the UDPForwarder instance with forwarding destinations.

        :param forward_addresses: A list of tuples, where each tuple consists of an IP address
                                  (str) and a port number (int) to forward packets to.
        :param logger: Logger instance for logging errors (optional).
        """
        self.m_forward_addresses = forward_addresses
        self.m_logger = logger

    def forward(self, data: bytes) -> None:
        """
        Forwards the given data to all the configured destinations.

        :param data: The data (bytes) to forward, which is the received UDP packet.
        """
        for destination in self.m_forward_addresses:
            self._forwardPacket(data, destination)

    def _forwardPacket(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Forwards the received UDP packet to the specified destination.

        :param data: The data (bytes) to forward, which is the received UDP packet.
        :param destination: A tuple (IP, Port) specifying where the packet should be forwarded.
        """
        forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            forward_socket.sendto(data, destination)
        except OSError as e:
            if self.m_logger:
                self.m_logger.error(f"Error forwarding packet to {destination}: {e}")
        finally:
            forward_socket.close()

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

        # Only attempt to create sockets if addresses are provided
        if forward_addresses:
            for destination in forward_addresses:
                try:
                    # Create UDP socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.setblocking(False)  # Non-blocking socket

                    # Connect the socket to the destination (doesn't send data)
                    sock.connect(destination)

                    # Store socket
                    self.m_sockets[destination] = sock
                except OSError as e:
                    if self.m_logger:
                        self.m_logger.error(f"Error creating socket to {destination}: {e}")
                    # Clean up any sockets created so far
                    self.close()
                    raise

        # Freeze the dictionaries after initialization
        self.m_sockets = MappingProxyType(self.m_sockets)

    def close(self) -> None:
        """
        Safely close all sockets.
        """
        for destination, sock in list(getattr(self, '_sockets', {}).items()):
            try:
                sock.close()
            except Exception as e:
                if self.m_logger:
                    self.m_logger.error(f"Error closing socket to {destination}: {e}")
                raise

    async def send(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Send data to the specified destination.

        :param data: Bytes to send
        :param destination: Destination (IP, Port)
        """
        if destination not in self.m_sockets:
            raise ValueError(f"No pre-initialized socket for destination {destination}")

        # Send asynchronously using the socket
        loop = asyncio.get_running_loop()
        await loop.sock_sendall(self.m_sockets[destination], data)

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

        # Schedule all sends concurrently using create_task (avoiding asyncio.gather overhead)
        for destination in self.m_forward_addresses:
            asyncio.ensure_future(self.m_transport.send(data, destination))

    async def _forwardPacket(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Forwards the received UDP packet to the specified destination.

        :param data: The data (bytes) to forward
        :param destination: A tuple (IP, Port) specifying where the packet should be forwarded
        """
        try:
            await self.m_transport.send(data, destination)
        except Exception as e:
            if self.m_logger:
                self.m_logger.error(f"Error forwarding packet to {destination}: {e}")
            raise
