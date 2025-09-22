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

from lib.f1_types import (LapData, LapHistoryData, ResultStatus,
                          VisualTyreCompound)

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass(slots=True)
class LapInfo:
    """
    Class that models lap-related information for a race driver.

    Attributes:
        m_best_lap_ms (Optional[int]): The best lap time in milliseconds.
        m_best_lap_obj (Optional[LapHistoryData]): Object containing details about the best lap.
        m_best_lap_tyre (Optional[VisualTyreCompound]): Visual representation of the tyre compound used during the best lap.
        m_pb_s1_ms (Optional[int]): Personal best sector 1 time in milliseconds.
        m_pb_s2_ms (Optional[int]): Personal best sector 2 time in milliseconds.
        m_pb_s3_ms (Optional[int]): Personal best sector 3 time in milliseconds.
        m_last_lap_ms (Optional[int]): The time taken for the last lap in milliseconds.
        m_last_lap_obj (Optional[LapHistoryData]): Object containing details about the last lap.
        m_current_lap (Optional[int]): The current lap number the driver is on.
        m_delta_to_car_in_front (Optional[int]): Time difference to the car in front in milliseconds.
        m_delta_to_leader (Optional[int]): Time difference to the race leader in milliseconds.
        m_top_speed_kmph_this_lap (Optional[int]): The top speed achieved during the current lap in km/h.
        m_speed_trap_record (Optional[float]): The speed trap record for the driver in km/h.
        m_is_pitting (Optional[bool]): Indicates whether the driver is currently in the pit lane.
        m_total_race_time (Optional[float]): Total race time in seconds.
        m_result_status  (Optional[ResultStatus]): The result status of the driver.
    """
    m_best_lap_ms: Optional[int] = None
    m_best_lap_obj: Optional[LapHistoryData] = None
    m_best_lap_tyre: Optional[VisualTyreCompound] = None
    m_pb_s1_ms: Optional[int] = None
    m_pb_s2_ms: Optional[int] = None
    m_pb_s3_ms: Optional[int] = None
    m_last_lap_ms: Optional[int] = None
    m_last_lap_obj: Optional[LapHistoryData] = None
    m_current_lap: Optional[int] = None
    m_delta_to_car_in_front: Optional[int] = None
    m_delta_to_leader: Optional[int] = None
    m_top_speed_kmph_this_lap: Optional[int] = None
    m_speed_trap_record: Optional[float] = None
    m_is_pitting: Optional[bool] = None
    m_total_race_time: Optional[float] = None
    m_result_status: Optional[ResultStatus] = None
    m_curr_lap_s1_ms: Optional[int] = None
    m_curr_lap_s2_ms: Optional[int] = None
    m_curr_lap_s3_ms: Optional[int] = None
    m_curr_lap_ms: Optional[int] = None
    m_curr_sector: Optional[LapData.Sector] = None
    m_curr_lap_invalid: Optional[bool] = None
    m_curr_status: Optional[LapData.DriverStatus] = None

    def processLapDataUpdate(self, lap_data: LapData) -> None:
        """Update the lap information based on the provided lap data object"""
        self.m_delta_to_car_in_front = lap_data.m_deltaToCarInFrontInMS
        self.m_delta_to_leader = (
            lap_data.m_deltaToRaceLeaderInMS +
            (lap_data.m_deltaToRaceLeaderMinutes * 60000)
        )

        self.m_curr_lap_ms = lap_data.m_currentLapTimeInMS
        self.m_curr_lap_invalid = lap_data.m_currentLapInvalid
        self.m_curr_status = lap_data.m_driverStatus
        self.m_curr_sector = lap_data.m_sector
        self.m_curr_lap_s1_ms = lap_data.s1TimeMS
        self.m_curr_lap_s2_ms = lap_data.s2TimeMS
        self.m_curr_lap_s3_ms = lap_data.s3TimeMS
