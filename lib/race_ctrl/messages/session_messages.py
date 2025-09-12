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
from .base import RaceCtrlMsgBase, MessageType

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SessionStartRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.SESSION_START,
            involved_drivers=[],
            lap_number=lap_number)

class SessionEndRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.SESSION_END,
            involved_drivers=[],
            lap_number=lap_number)

class DrsEnabledRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.DRS_ENABLED,
            involved_drivers=[],
            lap_number=lap_number)

class DrsDisabledRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, reason: str, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.DRS_DISABLED,
            involved_drivers=[],
            lap_number=lap_number)
        self.reason: str = reason

    def toJSON(self, _driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        return {
            **super().toJSON(_driver_info_dict),
            "reason": self.reason
        }

class ChequeredFlagRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.CHEQUERED_FLAG,
            involved_drivers=[],
            lap_number=lap_number)

class StartLightsRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, num_lights: int, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.START_LIGHTS,
            involved_drivers=[],
            lap_number=lap_number)
        self.num_lights: int = num_lights

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        return {
            **super().toJSON(driver_info_dict),
            "num-lights": self.num_lights
        }

class LightsOutRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.LIGHTS_OUT,
            involved_drivers=[],
            lap_number=lap_number)

class RedFlagRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.RED_FLAG,
            involved_drivers=[],
            lap_number=lap_number)

class SafetyCarRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, sc_type: str, event_type: str, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.SAFETY_CAR,
            involved_drivers=[],
            lap_number=lap_number)
        self.sc_type: str = sc_type
        self.event_type: str = event_type

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        return {
            **super().toJSON(driver_info_dict),
            "sc-type": self.sc_type,
            "event-type": self.event_type
        }

class RaceWinnerRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, winner_index: int, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.RACE_WINNER,
            involved_drivers=[winner_index],
            lap_number=lap_number)

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        ret = {
            **super().toJSON(driver_info_dict)
        }

        if driver_info := driver_info_dict.get(self.involved_drivers[0]):
            ret["driver-info"] = driver_info
        return ret
