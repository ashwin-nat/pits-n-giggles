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

import asyncio
import contextvars
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

# ------------------------- CLASS DEFINITIONS --------------------------------------------------------------------------

class TyreDeltaMessage:
    class TyreType(Enum):
        SLICK = 1
        WET = 2
        INTER = 3

        @staticmethod
        def isValid(tyre_type: Any) -> bool:
            """Check if the given tyre type ID is valid

            Args:
                tyre_type (int or TyreType): The tyre type to be validated

            Returns:
                bool: True if valid, else False
            """

            if isinstance(tyre_type, TyreDeltaMessage.TyreType):
                return True  # It's already an instance of F1PacketType
            return any(tyre_type == member.value for member in TyreDeltaMessage.TyreType)

        def __repr__(self) -> str:
            """Return a string representation of the TyreDeltaMessage object."""
            return {
                TyreDeltaMessage.TyreType.SLICK: "Slick",
                TyreDeltaMessage.TyreType.WET: "Wet",
                TyreDeltaMessage.TyreType.INTER: "Intermediate"
            }.get(self, "")

        def __str__(self) -> str:
            """Return a string representation of the TyreDeltaMessage object."""
            return self.__repr__()

    def __init__(self, curr_tyre_type: TyreType, other_tyre_type: TyreType, delta: float) -> None:
        """Initialize the TyreDeltaMessage object.

        Args:
            curr_tyre_type (TyreType): The current tyre type
            other_tyre_type (TyreType): The other tyre type
            delta (float): The tyre delta
        """
        self.m_curr_tyre_type = curr_tyre_type
        self.m_other_tyre_type = other_tyre_type
        self.m_delta = delta

    def __repr__(self) -> str:
        """Return a string representation of the TyreDeltaMessage object."""

        return f"TyreDeltaMessage(curr_tyre_type={str(self.m_curr_tyre_type)}, " \
                f"other_tyre_type={str(self.m_other_tyre_type)}, delta={self.m_delta})"

    def __str__(self) -> str:
        """Return a string representation of the TyreDeltaMessage object."""
        return self.__repr__()

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON representation of this object.

        Returns:
            Dict[str, Any]: The JSON representation of this object.
        """
        return {
            "curr-tyre-type": str(self.m_curr_tyre_type),
            "other-tyre-type": str(self.m_other_tyre_type),
            "tyre-delta": self.m_delta
        }

class TyreDeltaNotificationMessageCollection:
    def __init__(self, tyre_delta_messages: list[TyreDeltaMessage]) -> None:
        """Initialize the TyreDeltaNotificationMessageCollection object.

        Args:
            tyre_delta_messages (list[TyreDeltaMessage]): The list of tyre delta messages
        """
        self.m_tyre_delta_messages = tyre_delta_messages

    def __repr__(self) -> str:
        """Return a string representation of the TyreDeltaNotificationMessageCollection object."""
        return f"TyreDeltaNotificationMessageCollection(tyre_delta_messages={self.m_tyre_delta_messages})"

    def __str__(self) -> str:
        """Return a string representation of the TyreDeltaNotificationMessageCollection object."""
        return self.__repr__()

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON representation of this object.

        Returns:
            Dict[str, Any]: The JSON representation of this object.
        """
        return {
            "curr-tyre-type" : str(self.m_tyre_delta_messages[0].m_curr_tyre_type),
            "tyre-delta-messages": [message.toJSON() for message in self.m_tyre_delta_messages]
        }

class FinalClassificationNotification:
    def __init__(self, player_position: int) -> None:
        """Initialize the FinalClassificationNotification object.

        Args:
            player_position (int): The player's position in the final classification
        """
        self.m_player_position = player_position

    def __repr__(self) -> str:
        """Return a string representation of the FinalClassificationNotification object."""
        return f"FinalClassificationNotification(player_position={self.m_player_position})"

    def __str__(self) -> str:
        """Return a string representation of the FinalClassificationNotification object."""
        return self.__repr__()

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON representation of this object.

        Returns:
            Dict[str, Any]: The JSON representation of this object.
        """
        return {
            "player-position": self.m_player_position
        }

@dataclass(frozen=True)
class ITCMessage:
    class MessageType(str, Enum):
        CUSTOM_MARKER                      = "custom-marker"
        TYRE_DELTA_NOTIFICATION            = "tyre-delta"
        TYRE_DELTA_NOTIFICATION_V2         = "tyre-delta-v2"
        UDP_PACKET_FORWARD                 = "udp-packet-forward"
        FINAL_CLASSIFICATION_NOTIFICATION  = "final-classification-notification"

        def __str__(self) -> str:
            return self.value

        def __repr__(self) -> str:
            return self.value
    m_message_type: "ITCMessage.MessageType"
    m_message: Any

    def __repr__(self) -> str:
        """Return a string representation of the ITCMessage object."""
        return f"ITCMessage(message_type={self.m_message_type}, message={str(self.m_message)})"

    def __str__(self) -> str:
        """Return a string representation of the ITCMessage object."""
        return self.__repr__()

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON representation of this object.

        Returns:
            Dict[str, Any]: The JSON representation of this object.
        """
        return {
            "message-type": str(self.m_message_type),
            "message": self.m_message.toJSON()
        }

class AsyncInterTaskCommunicator:
    """Singleton Class for asynchronous inter-task communication"""
    _instance: Optional["AsyncInterTaskCommunicator"] = None
    _last_used_queue = contextvars.ContextVar("last_used_queue", default=None)
    _unblock_receivers_obj = object()

    def __new__(cls, *args: Any, **kwargs: Any) -> "AsyncInterTaskCommunicator":
        """
        Singleton pattern to ensure only one instance is created.
        Returns:
            AsyncInterThreadCommunicator: Object of this class
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, queue_size: int = 0):
        """Construct the AsyncInterThreadCommunicator object."""
        if not hasattr(self, '_initialized'):
            self.queues: Dict[str, asyncio.Queue] = {}
            self._lock = asyncio.Lock()
            self._queue_size = queue_size
            self._initialized = True

    async def send(self, queue_name: str, message: Any) -> None:
        """Send a message to the specified queue. The last used queue is cached at a task level.

        Args:
            queue_name (str): The name of the queue to send the message to.
            message (Any): The message to send.
        """
        q = await self._get_queue(queue_name)
        await q.put(message)

    async def receive(self, queue_name: str, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Asynchronously retrieves an item from the specified queue.

        Behavior depends on the `timeout` parameter:
          - If `timeout` is None, waits indefinitely until an item is available.
          - If `timeout` > 0, waits up to `timeout` seconds for an item.
          - If `timeout` == 0, attempts to retrieve immediately; returns `None` if the queue is empty.

        NOTE: If any task calls shutdown

        Args:
            queue_name (str): The name of the queue to retrieve the item from.
            timeout (Optional[float]): Maximum time in seconds to wait for an item.

        Returns:
            Optional[Any]: The item retrieved from the queue, or None if the operation timed out.
        """
        q = await self._get_queue(queue_name)
        try:
            item = await (asyncio.wait_for(q.get(), timeout) if timeout is not None else q.get())
            return None if item is self._unblock_receivers_obj else item
        except asyncio.TimeoutError:
            return None

    async def unblock_receivers(self) -> None:
        """Unblocks any tasks waiting for messages on all queues."""
        async with self._lock:
            for q in self.queues.values():
                await q.put(self._unblock_receivers_obj)

    async def _get_queue(self, queue_name: str) -> asyncio.Queue:
        """
        Get the queue associated with the given name, using contextvars
        for caching the last accessed queue.
        """
        cached = self._last_used_queue.get()
        if cached and cached[0] == queue_name:
            return cached[1]

        async with self._lock:
            if queue_name not in self.queues:
                self.queues[queue_name] = asyncio.Queue(maxsize=self._queue_size)

            queue = self.queues[queue_name]
            self._last_used_queue.set((queue_name, queue))
            return queue
