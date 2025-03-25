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
from typing import List, Tuple

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
    def __init__(self):
        self._transport = None
        self._protocol = None

    def __del__(self):
        """
        Destructor to ensure transport is closed when the object is garbage collected.
        This prevents resource leaks by closing the transport.
        """
        if self._transport and not self._transport.is_closing():
            try:
                self._transport.close()
            except Exception as e:
                png_logger.error(f"Error in destructor of AsyncUDPTransport: {e}")

    async def _create_transport(self, destination: Tuple[str, int]) -> None:
        """
        Create a UDP transport to a specific destination if not already created.
        :param destination: A tuple (IP, Port) specifying the destination.
        """
        if self._transport is None or self._transport.is_closing():
            try:
                loop = asyncio.get_running_loop()
                self._transport, self._protocol = await loop.create_datagram_endpoint(
                    asyncio.DatagramProtocol,
                    remote_addr=destination
                )
            except OSError as e:
                png_logger.error(f"Error creating transport to {destination}: {e}")
                raise

    async def send(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Send data to the specified destination.
        :param data: Bytes to send
        :param destination: Destination (IP, Port)
        """
        await self._create_transport(destination)
        try:
            self._transport.sendto(data)
        except Exception as e:
            png_logger.error(f"Error sending packet to {destination}: {e}")

class AsyncUDPForwarder:
    def __init__(self, forward_addresses: List[Tuple[str, int]]):
        """
        Initializes the AsyncUDPForwarder instance with forwarding destinations.
        :param forward_addresses: A list of tuples, where each tuple consists of an IP address
                                  (str) and a port number (int) to forward packets to.
        """
        self.m_forward_addresses = forward_addresses
        self._transport = AsyncUDPTransport()

    async def forward(self, data: bytes) -> None:
        """
        Asynchronously forwards the given data to all the configured destinations.
        :param data: The data (bytes) to forward, which is the received UDP packet.
        """
        for destination in self.m_forward_addresses:
            await self._forwardPacket(data, destination)

    async def _forwardPacket(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Asynchronously forwards the received UDP packet to the specified destination.
        :param data: The data (bytes) to forward, which is the received UDP packet.
        :param destination: A tuple (IP, Port) specifying where the packet should be forwarded.
        """
        try:
            await self._transport.send(data, destination)
        except Exception as e:
            png_logger.error(f"Error forwarding packet to {destination}: {e}")
