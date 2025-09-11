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

from typing import Dict, List

from .driver_mgr import DriverRaceControlManager
from .messages import RaceControlMessage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SessionRaceControlManager:
    """
    Manager for all race control messages in a session.

    Attributes:
        messages (List[RaceControlMessage]): All messages in this session.
        drivers (Dict[int, DriverRaceControlManager]): Per-driver managers.
    """

    def __init__(self) -> None:
        self.messages: List[RaceControlMessage] = []
        self.drivers: Dict[int, DriverRaceControlManager] = {}

    def register_driver(self, driver_index: int, driver_mgr: DriverRaceControlManager) -> None:
        """Register a driver manager with this session."""
        self.drivers[driver_index] = driver_mgr

    def add_message(self, message: RaceControlMessage) -> int:
        """
        Add a race control message to the session and relevant drivers.

        Returns:
            int: The message ID (its index in the session list).
        """
        self.messages.append(message)
        msg_id = len(self.messages) - 1

        for driver_idx in message.involved_drivers:
            driver_mgr = self.drivers.get(driver_idx)
            if driver_mgr:
                driver_mgr.add_message(message)

        return msg_id

    def clear(self) -> None:
        """Clear all session and driver messages. All registered drivers are automatically un-registered"""
        self.messages.clear()
        for driver_mgr in self.drivers.values():
            driver_mgr.clear()
        self.drivers.clear()

    def to_json(self) -> List[dict]:
        """Export all session messages as JSON-ready dicts with implicit IDs."""
        return [
            {
                "id": idx,
                "timestamp": msg.timestamp,
                "message_type": msg.message_type.name,
                "involved_drivers": list(msg.involved_drivers),
            }
            for idx, msg in enumerate(self.messages)
        ]
