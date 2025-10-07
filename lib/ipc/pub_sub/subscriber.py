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

from typing import Any, Callable, Dict, Optional
import logging

import zmq

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SubscriberSync:
    """
    Synchronous ZeroMQ Subscriber for inter-process communication.
    Subscribes to messages from a specified port and processes them with a callback.
    """

    def __init__(self, port: int = 4768, logger: Optional[logging.Logger] = None) -> None:
        """
        Initializes the SubscriberSync.

        Args:
            port (int): The port number to connect to.
            logger (Optional[logging.Logger]): An optional logger object.
        """
        self._port: int = port
        self._context: zmq.Context = zmq.Context()
        self._socket: zmq.Socket = self._context.socket(zmq.SUB)
        self._socket.connect(f"tcp://localhost:{self._port}")
        self._socket.setsockopt_string(zmq.SUBSCRIBE, "") # Subscribe to all messages
        self._running: bool = False
        self._logger = logger

    def run(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Starts the subscriber, continuously receiving messages and
        calling the provided callback function with the received data.

        Args:
            callback (Callable[[Dict[str, Any]], None]): The function to call with received data.
        """
        if self._logger:
            self._logger.info(f"Subscriber connected to port {self._port}")
        self._running = True
        while self._running:
            try:
                message: str = self._socket.recv_string(flags=zmq.NOBLOCK)
                # Assuming the message is a string representation of a dictionary
                data: Dict[str, Any] = eval(message) # This is generally unsafe, use json.loads if actual JSON
                callback(data)
            except zmq.Again:
                # No message received yet, continue
                pass
            except Exception as e:
                if self._running and self._logger: # Only log error if not intentionally closing
                    self._logger.error(f"Subscriber error: {e}")
                break

    def close(self) -> None:
        """
        Closes the subscriber socket and terminates the ZeroMQ context.
        """
        self._running = False
        self._socket.close()
        self._context.term()
        if self._logger:
            self._logger.info("Subscriber closed.")
