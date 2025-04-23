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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from dataclasses import dataclass
from typing import Optional

from lib.f1_types import SafetyCarType, TelemetrySetting
from ..png_logger import getLogger

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

png_logger = getLogger()

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass(slots=True)
class DriverInfo:
    """
    Class that models the information stored per race driver.

    Attributes:
        name (Optional[str]): The name of the driver.
        position (Optional[int]): The current position of the driver in the race.
        team (Optional[str]): The team to which the driver belongs.
        is_player (Optional[bool]): Indicates whether the driver is the player.
        telemetry_restrictions (Optional[TelemetrySetting]): Telemetry settings indicating the level of data available for the driver.
        driver_number (Optional[int]): The race number of the driver.
        m_num_pitstops (Optional[int]): The number of pitstops made by the driver.
        m_dnf_status_code (Optional[str]): Status code indicating if the driver did not finish the race.
        m_curr_lap_sc_status (Optional[SafetyCarType]): The current lap's safety car status.
    """
    name: Optional[str] = None
    position: Optional[int] = None
    team: Optional[str] = None
    is_player: Optional[bool] = None
    telemetry_restrictions: Optional[TelemetrySetting] = None
    driver_number: Optional[int] = None
    m_num_pitstops: Optional[int] = None
    m_dnf_status_code: Optional[str] = None
    m_curr_lap_max_sc_status: Optional[SafetyCarType] = None
