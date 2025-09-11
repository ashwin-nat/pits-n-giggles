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
from typing import Dict, List, Set

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MessageType(Enum):
    """Enumeration of possible race control message types."""
    FLAG = auto()
    PENALTY = auto()
    NOTE = auto()
    OTHER = auto()

@dataclass(frozen=True)
class RaceControlMessage:
    """
    Base class for all race control messages.

    Attributes:
        timestamp (float): Time at which the message was issued (seconds).
        message_type (MessageType): Type of race control message.
        involved_drivers (Set[int]): Set of driver indices involved in the message.
    """
    timestamp: float
    message_type: MessageType
    involved_drivers: Set[int] = field(default_factory=set)
