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
import struct

class UDPListener():
    """This class represents a UDP client.

    Attributes:
    - m_buffer_size - The buffer size being used
    - m_port - The UDP port that this client is bound to
    - m_bind_ip - The IP address this UDP client is bound to
    - m_socket - The socket object handle associated with this client

    Methods:
    - getNextMessage()
    """

    def __init__(self, port: int, bind_ip:str, buffer_size:int=16384) -> None:
        """Construct a UDPListener object

        Args:
            port (int): The port number to initialise this client to
            bind_ip (str): The IP address this client must be bound to (default is '127.0.0.1')
            buffer_size (int, optional): The buffer size to be specified. Defaults to 16 kb.
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
        message, _ = self.m_socket.recvfrom(self.m_buffer_size)
        return message

class TCPListener():
    """This class represents a TCP server.

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
            bind_ip (str): The IP address this server must be bound to (default is '127.0.0.1')
            buffer_size (int, optional): The buffer size to be specified. Defaults to 16 kb.
        """
        self.m_buffer_size = buffer_size
        self.m_port = port
        self.m_bind_ip = bind_ip
        self.m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.m_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.m_socket.bind((self.m_bind_ip, self.m_port))
        self.m_socket.listen(1)  # Set the maximum number of queued connections
        self.m_connection = None

    def getNextMessage(self) -> bytes:
        """
        Waits until the next message arrives on the current connection
        or establishes a new connection, then returns it.

        Returns:
        bytes: The raw bytes that were received.
        """
        while True:
            if self.m_connection is None:
                self.m_connection, _ = self.m_socket.accept()

            try:
                # Read the message length (assumed to be a 4-byte integer)
                message_length_bytes = self.m_connection.recv(4)
                if not message_length_bytes:
                    # Connection closed by the client
                    self.m_connection.close()
                    self.m_connection = None
                    continue  # Continue listening for the next connection

                message_length = struct.unpack('!I', message_length_bytes)[0]

                # Read the actual message based on the length
                message = self.m_connection.recv(message_length)
                if not message:
                    # Connection closed by the client
                    self.m_connection.close()
                    self.m_connection = None
                    continue  # Continue listening for the next connection

                return message

            except socket.error:
                # Handle socket errors, e.g., if the client abruptly disconnects
                self.m_connection.close()
                self.m_connection = None
                continue  # Continue listening for the next connection