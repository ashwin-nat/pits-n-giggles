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

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MessageType(Enum):
    """Enumeration of possible race control message types."""
    SESSION_START = auto()
    SESSION_END = auto()
    FASTEST_LAP = auto()
    RETIREMENT = auto()
    DRS_ENABLED = auto()
    DRS_DISABLED = auto()
    CHEQUERED_FLAG = auto()
    RACE_WINNER = auto()
    PENALTY = auto()
    SPEED_TRAP = auto()
    START_LIGHTS = auto()
    LIGHTS_OUT = auto()
    DRIVE_THROUGH_SERVED = auto()
    STOP_GO_SERVED = auto()
    RED_FLAG = auto()
    OVERTAKE = auto()
    SAFETY_CAR = auto()
    COLLISION = auto()

    def __str__(self) -> str:
        return self.name

@dataclass
class RaceCtrlMsgBase:
    """
    Base class for all race control messages.

    Attributes:
        _id (int): Unique identifier of the message.
        timestamp (float): Time at which the message was issued (seconds).
        message_type (MessageType): Type of race control message.
        involved_drivers (List[int]): List of driver indices involved in the message.
    """
    timestamp: float
    message_type: MessageType
    involved_drivers: List[int] = field(default_factory=list)
    lap_number: Optional[int] = None
    _id: Optional[int] = None

    def toJSON(self, _driver_info_dict: Optional[Dict[int, dict]] = None) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        return {
            "id": self._id,
            "lap-number": self.lap_number,
            "timestamp": self.timestamp,
            "message-type": str(self.message_type),
            "involved-drivers": list(self.involved_drivers),
        }
