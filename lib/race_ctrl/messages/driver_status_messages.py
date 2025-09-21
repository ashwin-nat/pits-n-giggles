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

from typing import Any, Dict, Optional, Union

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

    def toJSON(self, driver_info_dict = None) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = super().toJSON(driver_info_dict)
        if driver_info_dict and (driver_info := driver_info_dict.get(self.involved_drivers[0])):
            ret["driver-info"] = driver_info
        return ret

class CarDamageRaceControlMessage(RaceCtrlMsgBase):
    def __init__(self,
                 timestamp: float,
                 driver_index: int,
                 lap_number: int,
                 damaged_part: str,
                 old_value: Union[int, float],
                 new_value: Union[int, float]) -> None:
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
        self.m_old_value: Union[int, float] = old_value
        self.m_new_value: Union[int, float] = new_value

    def toJSON(self, driver_info_dict = None) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = super().toJSON(driver_info_dict)
        ret["damaged-part"] = self.m_damaged_part
        ret["old-value"] = self.m_old_value
        ret["new-value"] = self.m_new_value
        if driver_info_dict and (driver_info := driver_info_dict.get(self.involved_drivers[0])):
            ret["driver-info"] = driver_info
        return ret

class WingChangeRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self, timestamp: float, driver_index: int, lap_number: Optional[int] = None) -> None:
        """Driver pitting message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            driver_index (int): Index of the driver.
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.WING_CHANGE,
            involved_drivers=[driver_index],
            lap_number=lap_number)

    def toJSON(self, driver_info_dict = None) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = super().toJSON(driver_info_dict)
        if driver_info_dict and (driver_info := driver_info_dict.get(self.involved_drivers[0])):
            ret["driver-info"] = driver_info
        return ret

class TyreChangeRaceControlMessage(RaceCtrlMsgBase):
    def __init__(self,
                 timestamp: float,
                 driver_index: int,
                 lap_number: Optional[int],
                 old_tyre_compound: str,
                 old_tyre_index: int,
                 new_tyre_compound: str,
                 new_tyre_index: int) -> None:
        """Driver pitting message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            driver_index (int): Index of the driver.
            lap_number (Optional[int]): Lap number
            old_tyre_compound (str): Old tyre compound
            old_tyre_index (int): Old tyre index
            new_tyre_compound (str): New tyre compound
            new_tyre_index (int): New tyre index
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.TYRE_CHANGE,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.old_tyre_compound: str = old_tyre_compound
        self.old_tyre_index: int = old_tyre_index
        self.new_tyre_compound: str = new_tyre_compound
        self.new_tyre_index: int = new_tyre_index

    def toJSON(self, driver_info_dict = None) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = {
            **super().toJSON(driver_info_dict),
            "old-tyre-compound": self.old_tyre_compound,
            "old-tyre-index": self.old_tyre_index,
            "new-tyre-compound": self.new_tyre_compound,
            "new-tyre-index": self.new_tyre_index
        }

        if driver_info_dict and (driver_info := driver_info_dict.get(self.involved_drivers[0])):
            ret["driver-info"] = driver_info
        return ret
