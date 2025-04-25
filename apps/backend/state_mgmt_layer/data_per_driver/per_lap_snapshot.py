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

from typing import Any, Dict

from apps.lib.f1_types import (CarDamageData, CarStatusData, PacketTyreSetsData,
                          SafetyCarType)
from apps.backend.common.png_logger import getLogger

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

png_logger = getLogger()

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class PerLapSnapshotEntry:
    """
    Class that captures one lap's snapshot data

    Attributes:
        m_car_damage_packet (CarDamageData): The Car damage packet
        m_car_status_packet (CarStatusData): The Car Status packet
        m_track_position (int): The lap's track position
        m_tyre_sets_packet (Optional[PacketTyreSetsData]): The Tyre Sets packet
        m_max_sc_status (PacketSessionData.SafetyCarStatus): The lap's maximum safety car status value
        m_top_speed_kmph (float): The lap's top speed in kmph
    """

    def __init__(self,
        car_damage : CarDamageData,
        car_status : CarStatusData,
        max_sc_status  : SafetyCarType,
        tyre_sets  : PacketTyreSetsData,
        track_position: int,
        top_speed_kmph: float = 0.0):
        """Init the snapshot entry object

        Args:
            car_damage (CarDamageData): The Car damage packet
            car_status (CarStatusData): The Car Status packet
            max_sc_status (PacketSessionData.SafetyCarStatus): The lap's maximum safety car status value
            tyre_sets (PacketTyreSetsData): The Tyre Sets packet
            track_position (int): The lap's track position
            top_speed_kmph (float): The lap's top speed in kmph
        """

        self.m_car_damage_packet: CarDamageData = car_damage
        self.m_car_status_packet: CarStatusData = car_status
        self.m_max_sc_status: SafetyCarType = max_sc_status
        self.m_tyre_sets_packet: PacketTyreSetsData = tyre_sets
        self.m_track_position: int = track_position
        self.m_top_speed_kmph: float = top_speed_kmph

    def toJSON(self, lap_number : int) -> Dict[str, Any]:
        """Dump this object into JSON

        Args:
            lap_number (int): The lap number corresponding to this history item

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return {
            "lap-number" : lap_number,
            "car-damage-data" : self.m_car_damage_packet.toJSON() if self.m_car_damage_packet else None,
            "car-status-data" : self.m_car_status_packet.toJSON() if self.m_car_status_packet else None,
            "max-safety-car-status" : str(self.m_max_sc_status) if self.m_max_sc_status else None,
            "tyre-sets-data" : self.m_tyre_sets_packet.toJSON() if self.m_tyre_sets_packet else None,
            "track-position" : self.m_track_position or None,
            "top-speed-kmph" : self.m_top_speed_kmph,
        }
