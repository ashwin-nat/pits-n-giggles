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
from types import MappingProxyType
from typing import List, Tuple, Dict

from src.png_logger import getLogger

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

png_logger = getLogger()

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class UDPForwarder:
    def __init__(self, forward_addresses: List[Tuple[str, int]]):
        """
        Initializes the UDPForwarder instance with forwarding destinations.

        :param forward_addresses: A list of tuples, where each tuple consists of an IP address
                                  (str) and a port number (int) to forward packets to.
        """
        self.m_forward_addresses = forward_addresses

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
            png_logger.error(f"Error forwarding packet to {destination}: {e}")
        finally:
            forward_socket.close()

class AsyncUDPTransport:
    """Abstraction layer for UDP transport management."""
    def __init__(self, forward_addresses: List[Tuple[str, int]]):
        """
        Initialize transports for known destinations.

        :param forward_addresses: List of (IP, Port) tuples to initialize transports for
        """
        self._transports: Dict[Tuple[str, int], asyncio.DatagramTransport] = {}

        # Only attempt to create transports if addresses are provided
        if forward_addresses:
            # Use async method to create transports
            asyncio.run(self._initialize_transports(forward_addresses))

        # Freeze the dictionary after initialization
        self._transports = MappingProxyType(self._transports)

        # Store transports for safe cleanup
        self._cleanup_transports = list(self._transports.values())

    async def _initialize_transports(self, destinations: List[Tuple[str, int]]) -> None:
        """
        Asynchronously create transports for all specified destinations.

        :param destinations: List of (IP, Port) tuples to create transports for
        """
        # Use asyncio.gather to create transports concurrently
        await asyncio.gather(
            *[self._create_transport(destination) for destination in destinations]
        )

    async def _create_transport(self, destination: Tuple[str, int]) -> None:
        """
        Create a UDP transport for a specific destination.

        :param destination: A tuple (IP, Port) specifying the destination.
        """
        try:
            loop = asyncio.get_running_loop()
            transport, _ = await loop.create_datagram_endpoint(
                lambda: asyncio.DatagramProtocol(),
                remote_addr=destination
            )
            self._transports[destination] = transport
        except OSError as e:
            png_logger.error(f"Error creating transport to {destination}: {e}")
            raise

    def close(self) -> None:
        """
        Safely close all transports.
        """
        for transport in self._cleanup_transports:
            try:
                if not transport.is_closing():
                    transport.close()
            except Exception as e:
                png_logger.error(f"Error closing transport: {e}")

    async def send(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Send data to the specified destination.

        :param data: Bytes to send
        :param destination: Destination (IP, Port)
        """
        if destination not in self._transports:
            raise ValueError(f"No pre-initialized transport for destination {destination}")

        # Send outside of the lock to minimize lock duration
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self._transports[destination].sendto(data)
        )

class AsyncUDPForwarder:
    def __init__(self, forward_addresses: List[Tuple[str, int]]):
        """
        Initializes the AsyncUDPForwarder with forwarding destinations.

        :param forward_addresses: A list of tuples, each consisting of an IP address
                                  and a port number to forward packets to.
        """
        self.m_forward_addresses = forward_addresses
        self._transport = AsyncUDPTransport(forward_addresses)

    async def forward(self, data: bytes) -> None:
        """
        Concurrently forwards the given data to all configured destinations.

        :param data: The data (bytes) to forward
        """
        # Do nothing if no destinations are configured
        if not self.m_forward_addresses:
            return

        # Use asyncio.gather to send to all destinations concurrently
        await asyncio.gather(
            *[self._forwardPacket(data, destination)
              for destination in self.m_forward_addresses]
        )

    async def _forwardPacket(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Forwards the received UDP packet to the specified destination.

        :param data: The data (bytes) to forward
        :param destination: A tuple (IP, Port) specifying where the packet should be forwarded
        """
        try:
            await self._transport.send(data, destination)
        except Exception as e:
            png_logger.error(f"Error forwarding packet to {destination}: {e}")
