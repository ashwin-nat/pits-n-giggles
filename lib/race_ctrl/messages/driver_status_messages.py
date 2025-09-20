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

from typing import Any, Dict, Optional
from .base import MessageType, RaceCtrlMsgBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class DriverPittingRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self, timestamp: float, driver_index: int, lap_number: Optional[int] = None) -> None:
        """Driver pitting message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            driver_index (int): Index of the driver.
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.PITTING,
            involved_drivers=[driver_index],
            lap_number=lap_number)

    def toJSON(self, driver_info_dict = None):
        """Export the message as a JSON-ready dict."""
        ret = super().toJSON(driver_info_dict)
        if driver_info_dict and (driver_info := driver_info_dict.get(self.involved_drivers[0])):
            ret["driver-info"] = driver_info
        return ret

class CarDamageRaceCtrlMerssage(RaceCtrlMsgBase):
    def __init__(self,
                 timestamp: float,
                 driver_index: int,
                 lap_number: int,
                 damaged_part: str,
                 old_value: int | float,
                 new_value: int | float) -> None:
        """Driver pitting message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            driver_index (int): Index of the driver.
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.CAR_DAMAGE,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.m_damaged_part: str = damaged_part
        self.m_old_value: int | float = old_value
        self.m_new_value: int | float = new_value

    def toJSON(self, driver_info_dict = None):
        """Export the message as a JSON-ready dict."""
        ret = super().toJSON(driver_info_dict)
        ret["damaged-part"] = self.m_damaged_part
        ret["old-value"] = self.m_old_value
        ret["new-value"] = self.m_new_value
        if driver_info_dict and (driver_info := driver_info_dict.get(self.involved_drivers[0])):
            ret["driver-info"] = driver_info
        return ret