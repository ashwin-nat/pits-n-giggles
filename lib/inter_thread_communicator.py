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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import queue
import threading
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# ------------------------- CLASS DEFINITIONS --------------------------------------------------------------------------

@dataclass(frozen=True)
class ITCMessage:
    class MessageType(Enum):
        CUSTOM_MARKER = 1
        # Add more message types as needed

    m_message_type: "ITCMessage.MessageType"
    m_message: Any

class InterThreadCommunicator:
    _instance: Optional["InterThreadCommunicator"] = None
    queues: Dict[str, queue.Queue]

    def __new__(cls, *args, **kwargs) -> "InterThreadCommunicator":
        """
        Singleton pattern to ensure only one instance is created.

        Returns:
            InterThreadCommunicator: Object of this class
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Construct the InterThreadCommunicator object."""
        # Initialize only once to avoid resetting the queues dictionary on subsequent instantiations
        if not hasattr(self, "queues"):
            self.queues = {}
            self._lock = threading.Lock()  # Lock to protect access to the queues

    def _get_queue(self, queue_name: str) -> queue.Queue:
        """Get the specified named queue. If it doesn't exist, create it.

        Args:
            queue_name (str): Name of the queue

        Returns:
            queue.Queue: The queue object
        """
        # Get or create a queue by name
        with self._lock:
            if queue_name not in self.queues:
                self.queues[queue_name] = queue.Queue()
            return self.queues[queue_name]

    def send(self, queue_name: str, message: ITCMessage) -> None:
        """Send the given message to the specified queue

        Args:
            queue_name (str): Name of the queue
            message (ITCMessage): The message to be sent
        """
        q = self._get_queue(queue_name)
        q.put(message)

    def receive(self, queue_name: str, timeout_sec: int = 0) -> Optional[ITCMessage]:
        """Receives a message from the specified queue. If no message is available,
            waits up to `timeout_sec` seconds if specified. Returns None if no message is received within the timeout.

        Args:
            queue_name (str): Name of the queue
            timeout_sec (int, optional): The maximum number of seconds to wait for a message. Defaults to 0.

        Returns:
            Optional[ITCMessage]: The received message or None
        """

        q = self._get_queue(queue_name)

        try:
            return q.get(timeout=timeout_sec) if timeout_sec > 0 else q.get_nowait()
        except queue.Empty:
            return None

