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

from dataclasses import dataclass
from typing import Any, Dict, Optional

# ------------------------- CLASS DEFINITIONS --------------------------------------------------------------------------

@dataclass(slots=True)
class TyreWearPerLap:
    """Class representing the tyre wear percentage per lap.

    Attributes:
        fl_tyre_wear (float): Front left tyre wear percentage.
        fr_tyre_wear (float): Front right tyre wear percentage.
        rl_tyre_wear (float): Rear left tyre wear percentage.
        rr_tyre_wear (float): Rear right tyre wear percentage.
        lap_number (Optional[int]): Lap number.
        is_racing_lap (bool): Whether it's a racing lap or not.
        desc (Optional[str]): Description of the lap (e.g., pit stop, VSC).
    """
    fl_tyre_wear: float
    fr_tyre_wear: float
    rl_tyre_wear: float
    rr_tyre_wear: float
    lap_number: Optional[int] = None
    is_racing_lap: bool = True
    desc: Optional[str] = None

    @property
    def m_average(self) -> float:
        """
        Return the average tyre wear by calculating the sum of all tyre wears and dividing by 4.
        """
        return (self.fl_tyre_wear + self.fr_tyre_wear + self.rl_tyre_wear + self.rr_tyre_wear) / 4.0

    def __lt__(self, other: "TyreWearPerLap") -> bool:
        """
        Compare tyre wear objects by average tyre wear.

        Enables usage with max(), min(), sorted(), etc.
        """
        if not isinstance(other, TyreWearPerLap):
            return NotImplemented
        return self.m_average < other.m_average

    def toJSON(self) -> Dict[str, Any]:
        """
        Return a dictionary representing the object in JSON format.

        Returns:
            Dict[str, Any]: The JSON representation of the object.
        """

        return {
            "lap-number": self.lap_number,
            "front-left-wear": self.fl_tyre_wear,
            "front-right-wear": self.fr_tyre_wear,
            "rear-left-wear": self.rl_tyre_wear,
            "rear-right-wear": self.rr_tyre_wear,
            "average" : self.m_average,
            "desc" : self.desc
        }