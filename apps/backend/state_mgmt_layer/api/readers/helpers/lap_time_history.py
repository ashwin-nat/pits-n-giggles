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

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from apps.backend.state_mgmt_layer import SessionState
import lib.race_analyzer as RaceAnalyzer
from apps.backend.state_mgmt_layer.data_per_driver import (DataPerDriver,
                                                           TyreSetInfo)
from apps.backend.state_mgmt_layer.overtakes import GetOvertakesStatus
from lib.f1_types import (CarStatusData, F1Utils, LapHistoryData,
                          VisualTyreCompound)
from lib.save_to_disk import save_json_to_file
from lib.tyre_wear_extrapolator import TyreWearPerLap
from ...base import BaseAPI

# ------------------------- CLASSES ------------------------------------------------------------------------------------

class LapTimeHistory(BaseAPI):
    """Class representing lap time history data along with tyre set used

    Attributes:
        m_personal_fastest_lap_number (int): Fastest lap number.
        m_personal_fastest_s1_lap_number (int): Fastest sector 1 lap number.
        m_personal_fastest_s2_lap_number (int): Fastest sector 2 lap number.
        m_personal_fastest_s3_lap_number (int): Fastest sector 3 lap number.
        m_global_fastest_lap_ms (int): Fastest lap time of all drivers
        m_global_fastest_s1_ms (int) : Fastest S1 time of all drivers
        m_global_fastest_s2_ms (int) : Fastest S2 time of all drivers
        m_global_fastest_s3_ms (int) : Fastest S3 time of all drivers
        m_lap_time_history_data (List[LapTimeInfo]): List of LapTimeInfo objects representing lap time history data.
    """

    def __init__(self,
                 driver_data: Optional[DataPerDriver] = None,
                 global_fastest_lap_ms: Optional[int] = None,
                 global_fastest_s1_ms: Optional[int] = None,
                 global_fastest_s2_ms: Optional[int] = None,
                 global_fastest_s3_ms: Optional[int] = None,) -> None:
        """
        Initializes LapTimeHistory with an optional DataPerDriver object.

        Args:
            driver_data (Optional[TelData.DataPerDriver], optional): An instance of DataPerDriver. Defaults to None.
        """

        if driver_data is None:
            self.m_personal_fastest_lap_number: int = None

        self.m_global_fastest_lap_ms: Optional[int]  = global_fastest_lap_ms
        self.m_global_fastest_s1_ms: Optional[int]   = global_fastest_s1_ms
        self.m_global_fastest_s2_ms: Optional[int]   = global_fastest_s2_ms
        self.m_global_fastest_s3_ms: Optional[int]   = global_fastest_s3_ms

        if driver_data is None or driver_data.m_packet_copies.m_packet_session_history is None:
            self.m_personal_fastest_lap_number: int = None
            self.m_personal_fastest_s1_lap_number: int = None
            self.m_personal_fastest_s2_lap_number: int = None
            self.m_personal_fastest_s3_lap_number: int = None
            self.m_lap_time_history_data: List[LapHistoryData] = []
            return

        self.m_personal_fastest_lap_number: int      = driver_data.m_packet_copies.m_packet_session_history.m_bestLapTimeLapNum
        self.m_personal_fastest_s1_lap_number: int   = driver_data.m_packet_copies.m_packet_session_history.m_bestSector1LapNum
        self.m_personal_fastest_s2_lap_number: int   = driver_data.m_packet_copies.m_packet_session_history.m_bestSector2LapNum
        self.m_personal_fastest_s3_lap_number: int   = driver_data.m_packet_copies.m_packet_session_history.m_bestSector3LapNum
        self.m_lap_time_history_data: List[LapHistoryData] = []

        for index, lap_info in enumerate(driver_data.m_packet_copies.m_packet_session_history.m_lapHistoryData):
            lap_number = index + 1
            top_speed_kmph = driver_data.m_per_lap_snapshots[lap_number].m_top_speed_kmph \
                if lap_number in driver_data.m_per_lap_snapshots else None
            self.m_lap_time_history_data.append(LapTimeInfo(
                lap_history_data=lap_info,
                tyre_set_info=driver_data.getTyreSetInfoAtLap(lap_num=lap_number),
                top_speed_kmph=top_speed_kmph,
                lap_number=lap_number))

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the LapTimeHistory instance to a JSON-compatible dictionary with kebab-case keys.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the LapTimeHistory instance.
        """
        return {
            "fastest-lap-number": self.m_personal_fastest_lap_number,
            "fastest-s1-lap-number": self.m_personal_fastest_s1_lap_number,
            "fastest-s2-lap-number": self.m_personal_fastest_s2_lap_number,
            "fastest-s3-lap-number": self.m_personal_fastest_s3_lap_number,
            "global-fastest-lap-ms": self.m_global_fastest_lap_ms,
            "global-fastest-s1-ms" : self.m_global_fastest_s1_ms,
            "global-fastest-s2-ms" : self.m_global_fastest_s2_ms,
            "global-fastest-s3-ms" : self.m_global_fastest_s3_ms,
            "lap-time-history-data": [lap_time_info.toJSON() for lap_time_info in self.m_lap_time_history_data]
        }

class LapTimeInfo(BaseAPI):
    """Lap time info per lap. Contains Lap info breakdown and tyre set used

    Attributes:
        m_lapTimeInMS (int): Lap time in milliseconds.
        m_sector1TimeInMS (int): Sector 1 time in milliseconds.
        m_sector1TimeMinutes (int): Sector 1 whole minute part.
        m_sector2TimeInMS (int): Sector 2 time in milliseconds.
        m_sector2TimeMinutes (int): Sector 2 whole minute part.
        m_sector3TimeInMS (int): Sector 3 time in milliseconds.
        m_sector3TimeMinutes (int): Sector 3 whole minute part.
        m_lapValidBitFlags (int): Bit flags representing lap and sector validity.
        m_top_speed_kmph (int): Top speed this lap
        m_tyre_set_info (TyreSetInfo): The tyre set used.
    """
    def __init__(self,
                 lap_history_data: LapHistoryData,
                 tyre_set_info: TyreSetInfo,
                 top_speed_kmph: int,
                 lap_number: int) -> None:
        """
        Initializes LapTimeInfo with an existing LapHistoryData object, tyre set info and lap number.

        Args:
            lap_history_data (LapHistoryData): An instance of LapHistoryData.
            tyre_set_info (TyreSetInfo): The tyre set info for this lap
            lap_number (int): The lap number for this lap
        """

        # Initialize the base class attributes by copying from the existing LapHistoryData instance
        self.m_lapTimeInMS          = lap_history_data.m_lapTimeInMS
        self.m_sector1TimeInMS      = lap_history_data.m_sector1TimeInMS
        self.m_sector1TimeMinutes   = lap_history_data.m_sector1TimeMinutes
        self.m_sector2TimeInMS      = lap_history_data.m_sector2TimeInMS
        self.m_sector2TimeMinutes   = lap_history_data.m_sector2TimeMinutes
        self.m_sector3TimeInMS      = lap_history_data.m_sector3TimeInMS
        self.m_sector3TimeMinutes   = lap_history_data.m_sector3TimeMinutes
        self.m_lapValidBitFlags     = lap_history_data.m_lapValidBitFlags
        self.m_top_speed_kmph       = top_speed_kmph

        # Initialize the additional attributes
        self.m_tyre_set_info = tyre_set_info
        self.m_lap_number = lap_number

    def __str__(self) -> str:
        """
        Returns a string representation of LapTimeInfo.

        Returns:
            str: String representation of LapTimeInfo.
        """
        base_str = super().__str__()
        return f"{base_str}, Tyre Set Info: {str(self.m_tyre_set_info)}, Lap Number: {str(self.m_lap_number)}"

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the LapTimeInfo instance to a JSON-compatible dictionary with kebab-case keys.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the LapTimeInfo instance.
        """
        return {
            "lap-time-in-ms": self.m_lapTimeInMS,
            "lap-time-str": F1Utils.millisecondsToMinutesSecondsMilliseconds(self.m_lapTimeInMS),
            "sector-1-time-in-ms": self.m_sector1TimeInMS,
            "sector-1-time-minutes": self.m_sector1TimeMinutes,
            "sector-1-time-str" : F1Utils.getLapTimeStrSplit(self.m_sector1TimeMinutes, self.m_sector1TimeInMS),
            "sector-2-time-in-ms": self.m_sector2TimeInMS,
            "sector-2-time-minutes": self.m_sector2TimeMinutes,
            "sector-2-time-str": F1Utils.getLapTimeStrSplit(self.m_sector2TimeMinutes, self.m_sector2TimeInMS),
            "sector-3-time-in-ms": self.m_sector3TimeInMS,
            "sector-3-time-minutes": self.m_sector3TimeMinutes,
            "sector-3-time-str": F1Utils.getLapTimeStrSplit(self.m_sector3TimeMinutes, self.m_sector3TimeInMS),
            "lap-valid-bit-flags": self.m_lapValidBitFlags,
            "tyre-set-info" : self.m_tyre_set_info.toJSON() if self.m_tyre_set_info else None,
            "top-speed-kmph" : self.m_top_speed_kmph,
            "lap-number": self.m_lap_number,
        }
