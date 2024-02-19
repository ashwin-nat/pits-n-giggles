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

import socket


class UDPListener(object):
    """This class represents a UDP client.

    Attributes:
    - m_buffer_size - The buffer size being used
    - m_port - The UDP port that this client is bound to
    - m_bind_ip - The IP address this UDP client is bound to
    - m_socket - The socket object handle associated with this client

    Methods:
    - getNextMessage()
    """

    def __init__(self, port: int, bind_ip:str, buffer_size:int=1500) -> None:
        """Construct a UDPListener object

        Args:
            port (int): The port number to initialise this client to
            bind_ip (str): The IP address this client must be bound to
            buffer_size (int, optional): The buffer size to be specified. Defaults to 1500.
        """
        self.m_buffer_size = buffer_size
        self.m_port = port
        self.m_bind_ip = bind_ip
        self.m_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.m_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.m_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.m_socket.bind((self.m_bind_ip, self.m_port))

    def getNextMessage(self) -> bytes:
        """Waits until the next message arrives, then returns it.

        Returns:
            bytes: The raw bytes that were received
        """
        message, src = self.m_socket.recvfrom(self.m_buffer_size)
        return message