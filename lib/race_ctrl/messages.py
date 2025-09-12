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

    def toJSON(self, _driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        return {
            "id": self._id,
            "lap_number": self.lap_number,
            "timestamp": self.timestamp,
            "message_type": str(self.message_type),
            "involved_drivers": list(self.involved_drivers),
        }

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

class FastestLapRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, driver_index: int, lap_time_ms: int, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.FASTEST_LAP,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.lap_time_ms: int = lap_time_ms

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        ret = {
            **super().toJSON(driver_info_dict),
            "lap-time-ms": self.lap_time_ms
        }

        if driver_info := driver_info_dict.get(self.involved_drivers[0]):
            ret["driver-info"] = driver_info
        return ret

class RetirementRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, driver_index: int, reason: str, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.RETIREMENT,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.reason: str = reason

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        ret = {
            **super().toJSON(driver_info_dict),
            "reason": self.reason
        }

        if driver_info := driver_info_dict.get(self.involved_drivers[0]):
            ret["driver-info"] = driver_info
        return ret

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

class PenaltyRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, penalty_type: str, infringement_type: str, vehicle_index: int,
                 other_vehicle_index: int, time: int, places_gained: int, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.PENALTY,
            involved_drivers=[vehicle_index],
            lap_number=lap_number)
        self.penalty_type: str = penalty_type
        self.infringement_type: str = infringement_type
        self.vehicle_index: int = vehicle_index
        self.other_vehicle_index: int = other_vehicle_index
        if self.other_vehicle_index != 255:
            self.involved_drivers.append(self.other_vehicle_index)
        self.time: int = time
        self.places_gained: int = places_gained

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        ret = {
            **super().toJSON(driver_info_dict),
            "penalty-type": self.penalty_type,
            "infringement-type": self.infringement_type,
            "vehicle-index": self.vehicle_index,
            "other-vehicle-index": self.other_vehicle_index,
            "time": self.time,
            "places-gained": self.places_gained
        }

        if driver_info := driver_info_dict.get(self.vehicle_index):
            ret["driver-info"] = driver_info
        if other_driver_info := driver_info_dict.get(self.other_vehicle_index):
            ret["other-driver-info"] = other_driver_info
        return ret

class SpeedTrapRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, driver_index: int, speed: float, is_session_fastest: bool,
                 is_personal_fastest: bool, fastest_index: int, session_fastest: float,
                 lap_number: Optional[int] = None) -> None:
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

class DtPenServedRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, driver_index: int, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.DRIVE_THROUGH_SERVED,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.driver_index: int = driver_index

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        ret = {
            **super().toJSON(driver_info_dict),
            "driver-index": self.driver_index
        }

        if driver_info := driver_info_dict.get(self.driver_index):
            ret["driver-info"] = driver_info
        return ret

class SgPenServedRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, driver_index: int, stop_time: float, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.STOP_GO_SERVED,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.driver_index: int = driver_index
        self.stop_time: float = stop_time

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        ret = {
            **super().toJSON(driver_info_dict),
            "driver-index": self.driver_index,
            "stop-time": self.stop_time
        }

        if driver_info := driver_info_dict.get(self.driver_index):
            ret["driver-info"] = driver_info
        return ret

class RedFlagRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.RED_FLAG,
            involved_drivers=[],
            lap_number=lap_number)

class OvertakeRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, overtaker_index: int, overtaken_index: int, lap_number: Optional[int] = None) -> None:
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


class CollisionRaceCtrlMsg(RaceCtrlMsgBase):

    def __init__(self, timestamp: float, involved_drivers: List[int], lap_number: Optional[int] = None) -> None:
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.COLLISION,
            involved_drivers=involved_drivers,
            lap_number=lap_number)

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        ret = {
            **super().toJSON(driver_info_dict),
            "involved-drivers": self.involved_drivers
        }

        if driver_1_info := driver_info_dict.get(self.involved_drivers[0]):
            ret["driver-1-info"] = driver_1_info
        if driver_2_info := driver_info_dict.get(self.involved_drivers[1]):
            ret["driver-2-info"] = driver_2_info
        return ret
