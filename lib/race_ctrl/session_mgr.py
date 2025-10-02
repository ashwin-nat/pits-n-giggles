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

from typing import Dict, List, Optional

from .driver_mgr import DriverRaceControlManager
from .messages import RaceCtrlMsgBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SessionRaceControlManager:
    """
    Manager for all race control messages in a session.

    Attributes:
        messages (List[RaceControlMessage]): All messages in this session.
        drivers (Dict[int, DriverRaceControlManager]): Per-driver managers.
    """

    def __init__(self) -> None:
        self.messages: List[RaceCtrlMsgBase] = []
        self.drivers: Dict[int, DriverRaceControlManager] = {}

    def register_driver(self, driver_index: int, driver_mgr: DriverRaceControlManager) -> None:
        """Register a driver manager with this session."""
        self.drivers[driver_index] = driver_mgr
        driver_mgr.register_session_manager(self)

    def add_message(self, message: RaceCtrlMsgBase, is_propagated: bool = False) -> int:
        """
        Add a race control message to the session and relevant drivers.

        Args:
            message (RaceCtrlMsgBase): The message to add.
            is_propagated (bool): Whether the message is propagated from the driver to the session. If true, the message
                                  will not be added to the driver manager (given that the message came from the driver).

        Returns:
            int: The message ID (its index in the session list).
        """
        message._id = len(self.messages)
        self.messages.append(message)
        if is_propagated:
            return message._id

        for driver_idx in message.involved_drivers:
            if driver_mgr := self.drivers.get(driver_idx):
                driver_mgr.add_message(message, propagate=False)

        return message._id

    def clear(self) -> None:
        """Clear all session and driver messages. All registered drivers are automatically un-registered"""
        self.messages.clear()
        for driver_mgr in self.drivers.values():
            driver_mgr.clear()
        self.drivers.clear()

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = None) -> List[dict]:
        """Export all session messages as JSON-ready dicts with implicit IDs.

        Args:
            driver_info_dict (Optional[Dict[int, dict]]): Optional driver info dict.
            If specified, the driver info will be added to the message JSON. The dict must be a mapping of index against
            driver info JSON, which contains the following keys: `name`, `team`, `driver-number`.
        """
        return [msg.toJSON(driver_info_dict) for msg in self.messages]
