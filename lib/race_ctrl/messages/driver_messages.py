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

from typing import Any, Dict, List, Optional
from .base import MessageType, RaceCtrlMsgBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class FastestLapRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self, timestamp: float, driver_index: int, lap_time_ms: int, lap_number: Optional[int] = None) -> None:
        """Fastest lap message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            driver_index (int): Index of the driver.
            lap_time_ms (int): Lap time in milliseconds
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.FASTEST_LAP,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.lap_time_ms: int = lap_time_ms

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = {
            **super().toJSON(driver_info_dict),
            "lap-time-ms": self.lap_time_ms
        }

        if driver_info := driver_info_dict.get(self.involved_drivers[0]):
            ret["driver-info"] = driver_info
        return ret

class RetirementRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self, timestamp: float, driver_index: int, reason: str, lap_number: Optional[int] = None) -> None:
        """Retirement message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            driver_index (int): Index of the driver.
            reason (str): Retirement reason.
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.RETIREMENT,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.reason: str = reason

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = {
            **super().toJSON(driver_info_dict),
            "reason": self.reason
        }

        if driver_info := driver_info_dict.get(self.involved_drivers[0]):
            ret["driver-info"] = driver_info
        return ret

class SpeedTrapRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self, timestamp: float, driver_index: int, speed: float, is_session_fastest: bool,
                 is_personal_fastest: bool, fastest_index: int, session_fastest: float,
                 lap_number: Optional[int] = None) -> None:
        """Speed trap message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            driver_index (int): Index of the driver.
            speed (float): Speed of the driver.
            is_session_fastest (bool): Whether the driver is the session fastest.
            is_personal_fastest (bool): Whether the driver is the personal fastest.
            fastest_index (int): Index of the fastest driver.
            session_fastest (float): Session fastest speed.
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.SPEED_TRAP,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.driver_index: int = driver_index
        self.speed: float = speed
        self.is_session_fastest: bool = is_session_fastest
        self.is_personal_fastest: bool = is_personal_fastest
        self.fastest_index: int = fastest_index
        self.session_fastest: float = session_fastest

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = {
            **super().toJSON(driver_info_dict),
            "driver-index": self.driver_index,
            "speed": self.speed,
            "is-session-fastest": self.is_session_fastest,
            "is-personal-fastest": self.is_personal_fastest,
            "fastest-index": self.fastest_index,
            "session-fastest": self.session_fastest
        }

        if driver_info := driver_info_dict.get(self.driver_index):
            ret["driver-info"] = driver_info
        if session_fastest_driver_info := driver_info_dict.get(self.fastest_index):
            ret["session-fastest-driver-info"] = session_fastest_driver_info
        return ret

class OvertakeRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self,
                 timestamp: float,
                 overtaker_index: int,
                 overtaken_index: int,
                 lap_number: Optional[int] = None) -> None:
        """Overtake message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            overtaker_index (int): Index of the overtaker.
            overtaken_index (int): Index of the overtaken.
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.OVERTAKE,
            involved_drivers=[overtaker_index, overtaken_index],
            lap_number=lap_number)

    @property
    def overtaker_index(self) -> int:
        return self.involved_drivers[0]

    @property
    def overtaken_index(self) -> int:
        return self.involved_drivers[1]

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = {
            **super().toJSON(driver_info_dict),
            "overtaker-index": self.overtaker_index,
            "overtaken-index": self.overtaken_index
        }

        if overtaker_info := driver_info_dict.get(self.involved_drivers[0]):
            ret["overtaker-info"] = overtaker_info
        if overtaken_info := driver_info_dict.get(self.involved_drivers[1]):
            ret["overtaken-info"] = overtaken_info
        return ret
