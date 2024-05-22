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

import json
import logging
from typing import Dict, Any, Optional
from lib.f1_types import *
from lib.overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode, OvertakeRecord
import lib.race_analyzer as RaceAnalyzer
import src.telemetry_data as TelData
from src.telemetry_handler import dumpPktCapToFile, getOvertakeJSON, GetOvertakesStatus, getCustomMarkersJSON

# ------------------------- CLASSES --------------------------------------------

class TelemetryWebApiRspBase:
    """The base API response class. Contains common methods and fields
    """

    def __init__(self):
        """Dummy constructor. Should never be used directly
        """
        return

    def getValueOrDefaultValue(self,
            value: Optional[Any],
            default_value: str ='---') -> Optional[Any]:
        """
        Get value or default as string.

        Args:
            value: The value to check.
            default_value (str, optional): Default value if the input is None. Defaults to '---'.

        Returns:
            str: The value as is or default string if None.
        """
        return value if value is not None else default_value

class RaceInfoRsp(TelemetryWebApiRspBase):
    """This class will prepare the live race telemetry info response. Use toJSON() method to get the JSON rsp
    """
    def __init__(self, num_adjacent_cars: int) -> None:
        """Initialse the member variables by fetching necessary data from the data store

        Args:
            num_adjacent_cars (int): The number of cars adjacent to player to be included in the response
        """

        self.m_driver_data, self.m_fastest_lap_overall = TelData.getDriverData(num_adjacent_cars)
        (
            self.m_circuit,
            self.m_track_temp,
            self.m_event_type,
            self.m_total_laps,
            self.m_curr_lap,
            self.m_safety_car_status,
            self.m_weather_forecast_samples,
            self.m_pit_speed_limit,
            self.m_final_classification_received,
            self.m_is_spectator_mode,
            self.m_air_temp,
        ) = TelData.getGlobals()

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON response for the given num_adjacent_cars

        Returns:
            Dict[str, Any]: JSON response.
        """

        return {
            # First, global fields
            "circuit": self.getValueOrDefaultValue(self.m_circuit),
            "track-temperature": self.getValueOrDefaultValue(self.m_track_temp),
            "air-temperature": self.getValueOrDefaultValue(self.m_air_temp),
            "event-type": self.getValueOrDefaultValue(self.m_event_type),
            "total-laps": self.getValueOrDefaultValue(self.m_total_laps),
            "current-lap": self.getValueOrDefaultValue(self.m_curr_lap),
            "safety-car-status": str(self.getValueOrDefaultValue(self.m_safety_car_status, default_value="")),
            "fastest-lap-overall": self.m_fastest_lap_overall,
            "pit-speed-limit" : self.getValueOrDefaultValue(self.m_pit_speed_limit),
            "pit-speed-limit": self.getValueOrDefaultValue(self.m_pit_speed_limit),
            "weather-forecast-samples": [
                {
                    "time-offset": str(sample.m_timeOffset),
                    "weather": str(sample.m_weather),
                    "rain-probability": str(sample.m_rainPercentage)
                } for sample in self.m_weather_forecast_samples
            ],
            "race-ended" : self.getValueOrDefaultValue(self.m_final_classification_received, False),
            "is-spectating" : self.getValueOrDefaultValue(self.m_is_spectator_mode, False),

            # Now the driver data
            "table-entries": [
                {
                    "position": self.getValueOrDefaultValue(data_per_driver.m_position),
                    "name": self.getValueOrDefaultValue(data_per_driver.m_name),
                    "team": self.getValueOrDefaultValue(data_per_driver.m_team),
                    "delta": self.getDeltaPlusPenaltiesPlusPit(data_per_driver.m_delta_to_car_in_front,
                                                               data_per_driver.m_penalties,
                                                               data_per_driver.m_is_pitting,
                                                               data_per_driver.m_dnf_status_code),
                    "delta-to-leader": self.getDeltaPlusPenaltiesPlusPit(
                                F1Utils.millisecondsToSecondsMilliseconds(data_per_driver.m_delta_to_leader),
                                                               data_per_driver.m_penalties,
                                                               data_per_driver.m_is_pitting,
                                                               data_per_driver.m_dnf_status_code),
                    "ers": self.getValueOrDefaultValue(data_per_driver.m_ers_perc),
                    "best": self.getValueOrDefaultValue(data_per_driver.m_best_lap_str),
                    "best-lap-delta" : self.getValueOrDefaultValue(data_per_driver.m_best_lap_delta),
                    "last": self.getValueOrDefaultValue(data_per_driver.m_last_lap),
                    "last-lap-delta" : self.getValueOrDefaultValue(data_per_driver.m_last_lap_delta),
                    "is-fastest": self.getValueOrDefaultValue(data_per_driver.m_is_fastest),
                    "is-player": self.getValueOrDefaultValue(data_per_driver.m_is_player),
                    "average-tyre-wear": self.getValueOrDefaultValue(data_per_driver.m_tyre_wear),
                    "tyre-age": self.getValueOrDefaultValue(data_per_driver.m_tyre_age),
                    "tyre-life-remaining" : self.getValueOrDefaultValue(data_per_driver.m_tyre_life_remaining_laps),
                    "tyre-compound": self.getValueOrDefaultValue(data_per_driver.m_tyre_compound_type),
                    "drs": self.getDRSValue(data_per_driver.m_drs_activated, data_per_driver.m_drs_allowed,
                                            data_per_driver.m_drs_distance),
                    "num-pitstops": self.getValueOrDefaultValue(data_per_driver.m_num_pitstops),
                    "dnf-status" : self.getValueOrDefaultValue(data_per_driver.m_dnf_status_code),
                    "index" : self.getValueOrDefaultValue(data_per_driver.m_index),
                    "telemetry-setting" : data_per_driver.m_telemetry_restrictions, # Already NULL checked
                    "lap-progress" : data_per_driver.m_lap_progress, # NULL is supported
                    "corner-cutting-warnings" : self.getValueOrDefaultValue(data_per_driver.m_corner_cutting_warnings),
                    "time-penalties" : self.getValueOrDefaultValue(data_per_driver.m_time_penalties),
                    "num-dt" : self.getValueOrDefaultValue(data_per_driver.m_num_dt),
                    "num-sg" : self.getValueOrDefaultValue(data_per_driver.m_num_sg),
                    "tyre-wear-prediction" : data_per_driver.getTyrePredictionsJSONList(
                        data_per_driver.m_ideal_pit_stop_window),
                    "fuel-load-kg" : self.getValueOrDefaultValue(data_per_driver.m_fuel_load_kg),
                    "fuel-laps-remaining" : self.getValueOrDefaultValue(data_per_driver.m_fuel_laps_remaining),
                    "fl-wing-damage" : data_per_driver.m_fl_wing_damage, # NULL is supported
                    "fr-wing-damage" : data_per_driver.m_fr_wing_damage, # NULL is supported
                    "rear-wing-damage" : data_per_driver.m_rear_wing_damage, # NULL is supported
                } for data_per_driver in self.m_driver_data
            ]
        }

    def getDeltaPlusPenaltiesPlusPit(self,
            delta: str,
            penalties: str,
            is_pitting: bool,
            dnf_status_code: str):
        """
        Get delta plus penalties plus pit information.

        Args:
            delta (str): Delta information.
            penalties (str): Penalties information.
            is_pitting (bool): Whether the driver is pitting.
            dnf_status_code (str): The code indicating DNF status. Empty string if driver is still racing

        Returns:
            str: Delta plus penalties plus pit information.
        """

        if len(dnf_status_code) > 0:
            return dnf_status_code
        elif is_pitting:
            return "PIT " + penalties
        elif delta is not None:
            return delta + " " + penalties
        else:
            return "---"

    def getDRSValue(self,
            drs_activated: bool,
            drs_available: bool,
            drs_distance: int) -> bool:
        """
        Get DRS value.

        Args:
            drs_activated (bool): Whether DRS is activated.
            drs_available (bool): Whether DRS is available.
            drs_distance (int): Distance to DRS zone start.

        Returns:
            bool: True if DRS is activated or available or has non-zero distance, False otherwise.
        """

        return True if (drs_activated or drs_available or (drs_distance > 0)) else False

class SavePacketCaptureRsp(TelemetryWebApiRspBase):
    """
    Save packet capture response class.
    """

    def __init__(self):
        """Save the packet capture and prepare the rsp fields
        """

        (
            self.m_status_code,
            self.m_file_name,
            self.m_num_packets,
            self.m_num_bytes
        ) = dumpPktCapToFile(clear_db=True, reason='Received Request')

    def toJSON(self) -> Dict[str, Any]:
        """Dump this object into JSON

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return {
            "is-success" : (True if self.m_file_name else False),
            "status-code" : str(self.m_status_code),
            "file-name" : self.getValueOrDefaultValue(self.m_file_name, ""),
            "num-packets" : self.getValueOrDefaultValue(self.m_num_packets, default_value=0),
            "num-bytes" : self.getValueOrDefaultValue(self.m_num_bytes, default_value=0)
        }

class OverallRaceStatsRsp(TelemetryWebApiRspBase):
    """
    Overall race stats response class.
    """

    def __init__(self):
        """Get the overall race stats and prepare the rsp fields
        """

        self.m_rsp = TelData.getRaceInfo()
        self._checkUpdateRecords()

    def _checkUpdateRecords(self):
        """
        Checks the given JSON data for the presence of certain keys and updates the data if necessary.
        """
        if "records" not in self.m_rsp:
            self.m_rsp["records"] = {}

        if "fastest" not in self.m_rsp["records"]:
            try:
                self.m_rsp["records"]["fastest"] = RaceAnalyzer.getFastestTimesJson(self.m_rsp)
            except ValueError:
                logging.debug('Failed to get fastest times JSON')
                self.m_rsp["records"]["fastest"] = None

        if "tyre-stats" not in self.m_rsp["records"]:
            try:
                self.m_rsp["records"]["tyre-stats"] = RaceAnalyzer.getTyreStintRecordsDict(self.m_rsp)
            except:
                logging.debug('Failed to get tyre stats JSON')
                self.m_rsp["records"]["tyre-stats"] = None

        should_recompute_overtakes = False
        if "overtakes" not in self.m_rsp:
            self.m_rsp["overtakes"] = {
                "records" : []
            }
            should_recompute_overtakes = True

        expected_keys = [
            "number-of-overtakes",
            "number-of-times-overtaken",
            "most-heated-rivalries"
        ]
        for key in expected_keys:
            if key not in self.m_rsp["overtakes"]:
                should_recompute_overtakes = True

        if should_recompute_overtakes:
            _, overtake_records = getOvertakeJSON()
            self.m_rsp["overtakes"] = self.m_rsp["overtakes"] | overtake_records

        self.m_rsp["custom-markers"] = getCustomMarkersJSON()

    def toJSON(self) -> Dict[str, Any]:
        """Dump this object into JSON

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return self.m_rsp

class DriverInfoRsp(TelemetryWebApiRspBase):
    """
    Driver info response class.
    """

    def __init__(self, index: int):
        """Get the driver info and prepare the rsp fields

        Args:
            index (int): Index of the driver
        """

        self.m_rsp = TelData.getDriverInfoJsonByIndex(index)
        assert self.m_rsp
        status, overtakes_info = getOvertakeJSON(self.m_rsp["driver-name"])
        self.m_rsp["overtakes-status-code"] = str(status)
        self.m_rsp['overtakes'] = overtakes_info
        assert status != GetOvertakesStatus.INVALID_INDEX

    def toJSON(self) -> Dict[str, Any]:
        """Dump this object into JSON

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return self.m_rsp