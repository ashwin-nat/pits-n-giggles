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
        :return: None
        """
        for destination in self.m_forward_addresses:
            self._forwardPacket(data, destination)

    def _forwardPacket(self, data: bytes, destination: Tuple[str, int]) -> None:
        """
        Forwards the received UDP packet to the specified destination.

        :param data: The data (bytes) to forward, which is the received UDP packet.
        :param destination: A tuple (IP, Port) specifying where the packet should be forwarded.
        :return: None
        """
        forward_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            forward_socket.sendto(data, destination)
        except Exception as e:
            png_logger.error(f"Error forwarding packet to {destination}: {e}")
        finally:
            forward_socket.close()