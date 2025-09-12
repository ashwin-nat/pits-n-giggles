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

class PenaltyRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self, timestamp: float, penalty_type: str, infringement_type: str, vehicle_index: int,
                 other_vehicle_index: int, time: int, places_gained: int, lap_number: Optional[int] = None) -> None:
        """Penalty message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            penalty_type (str): Penalty type.
            infringement_type (str): Infringement type.
            vehicle_index (int): Index of the vehicle.
            other_vehicle_index (int): Index of the other vehicle.
            time (int): Penalty time in seconds.
            places_gained (int): Number of places gained.
        """
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
        """Export the message as a JSON-ready dict."""
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

class DtPenServedRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self, timestamp: float, driver_index: int, lap_number: Optional[int] = None) -> None:
        """Drive through served message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            driver_index (int): Index of the driver.
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.DRIVE_THROUGH_SERVED,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.driver_index: int = driver_index

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = {
            **super().toJSON(driver_info_dict),
            "driver-index": self.driver_index
        }

        if driver_info := driver_info_dict.get(self.driver_index):
            ret["driver-info"] = driver_info
        return ret

class SgPenServedRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self, timestamp: float, driver_index: int, stop_time: float, lap_number: Optional[int] = None) -> None:
        """Stop go served message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            driver_index (int): Index of the driver.
            stop_time (float): Stop time in seconds.
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.STOP_GO_SERVED,
            involved_drivers=[driver_index],
            lap_number=lap_number)
        self.driver_index: int = driver_index
        self.stop_time: float = stop_time

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = {
            **super().toJSON(driver_info_dict),
            "driver-index": self.driver_index,
            "stop-time": self.stop_time
        }

        if driver_info := driver_info_dict.get(self.driver_index):
            ret["driver-info"] = driver_info
        return ret

class CollisionRaceCtrlMsg(RaceCtrlMsgBase):
    def __init__(self, timestamp: float, involved_drivers: List[int], lap_number: Optional[int] = None) -> None:
        """Collision message

        Args:
            timestamp (float): Time at which the message was issued (seconds).
            involved_drivers (List[int]): List of involved drivers indices.
        """
        super().__init__(
            timestamp=timestamp,
            message_type=MessageType.COLLISION,
            involved_drivers=involved_drivers,
            lap_number=lap_number)

    def toJSON(self, driver_info_dict: Optional[Dict[int, dict]] = {}) -> Dict[str, Any]:
        """Export the message as a JSON-ready dict."""
        ret = {
            **super().toJSON(driver_info_dict),
            "involved-drivers": self.involved_drivers
        }

        if driver_1_info := driver_info_dict.get(self.involved_drivers[0]):
            ret["driver-1-info"] = driver_1_info
        if driver_2_info := driver_info_dict.get(self.involved_drivers[1]):
            ret["driver-2-info"] = driver_2_info
        return ret
