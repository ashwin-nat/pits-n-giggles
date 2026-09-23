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

"""SessionState.getTyreDeltaNotificationMessages()'s output type.

A standalone sibling of session_state.py (not under intf/readers/) because those readers
import SessionState directly - putting this there and importing it back into session_state.py
would be circular. telemetry_layer consumes it via apps.backend.state_mgmt_layer's re-export.
"""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from enum import Enum
from typing import Any, Dict

# ------------------------- CLASS DEFINITIONS --------------------------------------------------------------------------

class TyreDeltaMessage:
    class TyreType(Enum):
        SLICK = 1
        WET = 2
        INTER = 3

        def __repr__(self) -> str:
            return {
                TyreDeltaMessage.TyreType.SLICK: "Slick",
                TyreDeltaMessage.TyreType.WET: "Wet",
                TyreDeltaMessage.TyreType.INTER: "Intermediate"
            }.get(self, "")

        def __str__(self) -> str:
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
        return f"TyreDeltaMessage(curr_tyre_type={str(self.m_curr_tyre_type)}, " \
                f"other_tyre_type={str(self.m_other_tyre_type)}, delta={self.m_delta})"

    def __str__(self) -> str:
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
