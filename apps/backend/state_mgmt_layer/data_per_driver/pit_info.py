# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

from dataclasses import dataclass
from typing import Any, Dict, Optional

from lib.f1_types import LapData

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass(slots=True)
class PitInfo:
    """
    Class that models the information stored per race driver.

    Attributes:
        name (Optional[str]): The name of the driver.
        position (Optional[int]): The current position of the driver in the race.
        grid_position (Optional[int]): The starting grid position of the driver.
        team (Optional[str]): The team to which the driver belongs.
        is_player (Optional[bool]): Indicates whether the driver is the player.
        telemetry_restrictions (Optional[TelemetrySetting]): Telemetry settings indicating the level of data available for the driver.
        driver_number (Optional[int]): The race number of the driver.
        m_num_pitstops (Optional[int]): The number of pitstops made by the driver.
        m_dnf_status_code (Optional[str]): Status code indicating if the driver did not finish the race.
        m_curr_lap_sc_status (Optional[SafetyCarType]): The current lap's safety car status.
    """
    m_pit_status: Optional[LapData.PitStatus] = None
    m_num_stops: Optional[int] = None
    m_pit_lane_timer_active: Optional[bool] = None
    m_pit_lane_timer_ms: Optional[int] = None
    m_pit_stop_timer_ms: Optional[int] = None
    m_pit_stop_should_serve_pen: Optional[bool] = None

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON representation of the PitInfo object."""
        return {
            "pit-status": str(self.m_pit_status),
            "num-stops": self.m_num_stops,
            "pit-lane-timer-active": self.m_pit_lane_timer_active,
            "pit-lane-timer-ms": self.m_pit_lane_timer_ms,
            "pit-stop-timer-ms": self.m_pit_stop_timer_ms,
            "pit-stop-should-serve-pen": self.m_pit_stop_should_serve_pen
        }
