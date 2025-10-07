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

from typing import Dict, Any
import asyncio
import zmq
import zmq.asyncio as zaio

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PublisherAsync:
    """
    Asynchronous ZeroMQ Publisher for inter-process communication.
    Publishes messages to a specified port.
    """

    def __init__(self, port: int = 4768):
        self.port = port
        self.context = zaio.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.num_subscribers_val = 0

    async def run(self) -> None:
        """
        Binds the publisher socket to the specified port.
        """
        self.socket.bind(f"tcp://*:{self.port}")
        print(f"Publisher listening on port {self.port}")

    async def close(self) -> None:
        """
        Closes the publisher socket and terminates the ZeroMQ context.
        """
        self.socket.close()
        self.context.term()
        print("Publisher closed.")

    @property
    def num_subscribers(self) -> int:
        """
        Returns the number of connected subscribers.
        Note: ZeroMQ PUB sockets do not directly expose the number of subscribers.
        This property is a placeholder and might require a custom mechanism
        if an accurate count is needed.
        """
        # In a real-world scenario, you might implement a custom heartbeat/registration
        # mechanism to track subscribers if an accurate count is critical.
        # For basic pub/sub, this is often not strictly necessary.
        return self.num_subscribers_val

    async def publish(self, data: Dict[str, Any]) -> None:
        """
        Publishes data to all connected subscribers.
        The data is sent as a JSON-encoded string.
        """
        message = str(data).encode('utf-8') # Simple string conversion for basic test
        await self.socket.send(message)
        # print(f"Published: {data}")
