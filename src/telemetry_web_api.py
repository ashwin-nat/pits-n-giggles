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

import logging
from typing import Dict, Any, Optional, List
from lib.f1_types import F1Utils
import lib.race_analyzer as RaceAnalyzer
import src.telemetry_data as TelData
from src.telemetry_handler import dumpPktCapToFile, getOvertakeJSON, GetOvertakesStatus, getCustomMarkersJSON

# ------------------------- UTILITIES ----------------------------------------------------------------------------------

def _getValueOrDefaultValue(
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

# ------------------------- API - CLASSES ------------------------------------------------------------------------------

class RaceInfoRsp:
    """This class will prepare the live race telemetry info response. Use toJSON() method to get the JSON rsp
    """
    def __init__(self) -> None:
        """Initialse the member variables by fetching necessary data from the data store

        """

        # self.m_driver_data, self.m_fastest_lap_overall = TelData.getDriverData(num_adjacent_cars)
        self.m_globals = TelData.getGlobals()
        track_length = self.m_globals.m_packet_session.m_trackLength if self.m_globals.m_packet_session else None
        self.m_driver_list_rsp = DriversListRsp(self.m_globals.m_is_spectating, track_length)
        self.m_curr_lap = self.m_driver_list_rsp.getCurrentLap()
        if self.m_globals.m_weather_forecast_samples is None:
            self.m_globals.m_weather_forecast_samples = []

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON response for the given num_adjacent_cars

        Returns:
            Dict[str, Any]: JSON response.
        """

        globals_json = {
            # First, global fields
            "circuit": _getValueOrDefaultValue(self.m_globals.m_circuit),
            "track-temperature": _getValueOrDefaultValue(self.m_globals.m_track_temp),
            "air-temperature": _getValueOrDefaultValue(self.m_globals.m_air_temp),
            "event-type": _getValueOrDefaultValue(self.m_globals.m_event_type),
            "total-laps": _getValueOrDefaultValue(self.m_globals.m_total_laps),
            "current-lap": _getValueOrDefaultValue(self.m_curr_lap),
            "safety-car-status": str(_getValueOrDefaultValue(self.m_globals.m_safety_car_status, default_value="")),
            "pit-speed-limit": _getValueOrDefaultValue(self.m_globals.m_pit_speed_limit),
            "weather-forecast-samples": [
                {
                    "time-offset": str(sample.m_timeOffset),
                    "weather": str(sample.m_weather),
                    "rain-probability": str(sample.m_rainPercentage)
                } for sample in self.m_globals.m_weather_forecast_samples
            ],
            "race-ended" : bool(self.m_globals.m_packet_final_classification),
            "is-spectating" : _getValueOrDefaultValue(self.m_globals.m_is_spectating, False),
        }

        driver_list_json = self.m_driver_list_rsp.toJSON()
        globals_json.update(driver_list_json)
        return globals_json

class SavePacketCaptureRsp:
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
            "is-success" : bool(self.m_file_name),
            "status-code" : str(self.m_status_code),
            "file-name" : _getValueOrDefaultValue(self.m_file_name, ""),
            "num-packets" : _getValueOrDefaultValue(self.m_num_packets, default_value=0),
            "num-bytes" : _getValueOrDefaultValue(self.m_num_bytes, default_value=0)
        }

class OverallRaceStatsRsp:
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
            self.m_rsp["records"]["tyre-stats"] = RaceAnalyzer.getTyreStintRecordsDict(self.m_rsp)

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

class DriverInfoRsp:
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

# ------------------------- HELPER - CLASSES ---------------------------------------------------------------------------

class DriversListRsp:
    """
    Drivers list response class.
    """

    def __init__(self, is_spectator_mode: bool, track_length: int):
        """Get the drivers list and prepare the rsp fields

        Args:
            is_spectator_mode (bool): Whether the player is in spectator mode
            track_length (int): The length of the track
        """

        self.m_is_spectator_mode : bool = is_spectator_mode
        self.m_track_length : int = track_length
        self.m_final_list : List[TelData.DataPerDriver] = []
        self.m_fastest_lap : Optional[str] = None
        self.__initDriverList()
        self.__updateDriverList()
        if len(self.m_final_list) > 0:
            self._recomputeDeltas()

    def toJSON(self) -> Dict[str, Any]:
        """Dump this object into JSON

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return {
            "table-entries": [
                {
                    "position": _getValueOrDefaultValue(data_per_driver.m_position),
                    "name": _getValueOrDefaultValue(data_per_driver.m_name),
                    "team": _getValueOrDefaultValue(data_per_driver.m_team),
                    "delta": self.__getDeltaPlusPenaltiesPlusPit(data_per_driver.m_delta_to_car_in_front,
                                                               data_per_driver.m_penalties,
                                                               data_per_driver.m_is_pitting,
                                                               data_per_driver.m_dnf_status_code),
                    "delta-to-leader": self.__getDeltaPlusPenaltiesPlusPit(
                                F1Utils.millisecondsToSecondsMilliseconds(data_per_driver.m_delta_to_leader),
                                                               data_per_driver.m_penalties,
                                                               data_per_driver.m_is_pitting,
                                                               data_per_driver.m_dnf_status_code),
                    "ers": _getValueOrDefaultValue(data_per_driver.m_ers_perc),
                    "best": _getValueOrDefaultValue(data_per_driver.m_best_lap_str),
                    "best-lap-delta" : _getValueOrDefaultValue(data_per_driver.m_best_lap_delta),
                    "last": _getValueOrDefaultValue(data_per_driver.m_last_lap),
                    "last-lap-delta" : _getValueOrDefaultValue(data_per_driver.m_last_lap_delta),
                    "is-fastest": _getValueOrDefaultValue(data_per_driver.m_is_fastest),
                    "is-player": _getValueOrDefaultValue(data_per_driver.m_is_player),
                    "average-tyre-wear": _getValueOrDefaultValue(data_per_driver.m_tyre_wear),
                    "tyre-age": _getValueOrDefaultValue(data_per_driver.m_tyre_age),
                    "tyre-life-remaining" : _getValueOrDefaultValue(data_per_driver.m_tyre_life_remaining_laps),
                    "tyre-compound": _getValueOrDefaultValue(data_per_driver.m_tyre_compound_type),
                    "drs": self.__getDRSValue(data_per_driver.m_drs_activated, data_per_driver.m_drs_allowed,
                                            data_per_driver.m_drs_distance),
                    "num-pitstops": _getValueOrDefaultValue(data_per_driver.m_num_pitstops),
                    "dnf-status" : _getValueOrDefaultValue(data_per_driver.m_dnf_status_code),
                    "index" : _getValueOrDefaultValue(data_per_driver.m_index),
                    "telemetry-setting" : data_per_driver.m_telemetry_restrictions, # Already NULL checked
                    "lap-progress" : data_per_driver.m_lap_progress, # NULL is supported
                    "corner-cutting-warnings" : _getValueOrDefaultValue(data_per_driver.m_corner_cutting_warnings),
                    "time-penalties" : _getValueOrDefaultValue(data_per_driver.m_time_penalties),
                    "num-dt" : _getValueOrDefaultValue(data_per_driver.m_num_dt),
                    "num-sg" : _getValueOrDefaultValue(data_per_driver.m_num_sg),
                    "tyre-wear-prediction" : data_per_driver.getTyrePredictionsJSONList(
                        data_per_driver.m_ideal_pit_stop_window),
                    "fuel-load-kg" : _getValueOrDefaultValue(data_per_driver.m_fuel_load_kg),
                    "fuel-laps-remaining" : _getValueOrDefaultValue(data_per_driver.m_fuel_laps_remaining),
                    "fl-wing-damage" : data_per_driver.m_fl_wing_damage, # NULL is supported
                    "fr-wing-damage" : data_per_driver.m_fr_wing_damage, # NULL is supported
                    "rear-wing-damage" : data_per_driver.m_rear_wing_damage, # NULL is supported
                } for data_per_driver in self.m_final_list
            ],
            "fastest-lap-overall" : _getValueOrDefaultValue(self.m_fastest_lap)
        }

    def getCurrentLap(self) -> Optional[int]:
        """Get current lap.

        Returns:
            Optional[int]: The lap number. None if no race is ongoing
        """

        if len(self.m_final_list) == 0:
            return None

        if self.m_is_spectator_mode:
            return self.m_final_list[0].m_current_lap
        return next((driver_data.m_current_lap for driver_data in self.m_final_list if driver_data.m_is_player), None)

    def __getDeltaPlusPenaltiesPlusPit(self,
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
        if is_pitting:
            return "PIT " + penalties
        if delta is not None:
            return delta + " " + penalties
        return "---"

    def __getDRSValue(self,
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

        if (drs_activated is None) or (drs_available is None) or (drs_distance is None):
            return False
        return bool(drs_activated or drs_available or (drs_distance > 0))

    def __initDriverList(self) -> None:
        """Initialise the fields
        """

        with TelData._driver_data_lock:
            # Do the bare mimnimum within this block so that we can unlock the mutex ASAP
            if (TelData._driver_data.m_player_index is None) or (TelData._driver_data.m_num_active_cars is None):
                return

            # Update the list data
            if TelData._driver_data.m_fastest_index is not None:
                self.m_fastest_lap = TelData._driver_data.m_driver_data[
                                        TelData._driver_data.m_fastest_index].m_best_lap_str
            positions = list(range(1, TelData._driver_data.m_num_active_cars + 1))
            for position in positions:
                index, temp_data = TelData._driver_data.getIndexByTrackPosition(position)
                if (index, temp_data) == (None, None):
                    return

                temp_data.m_index = index
                temp_data.m_is_fastest = (index == TelData._driver_data.m_fastest_index)
                if temp_data.m_is_player:
                    temp_data.m_ideal_pit_stop_window = TelData._driver_data.m_ideal_pit_stop_window
                else:
                    temp_data.m_ideal_pit_stop_window = None

                # Add this prepped record into the final list
                self.m_final_list.append(temp_data)

    def __updateDriverList(self) -> None:
        """Add extra fields to each DataPerDriver object
        """

        for driver_data in self.m_final_list:
            if driver_data.m_ers_perc is not None:
                driver_data.m_ers_perc = F1Utils.floatToStr(driver_data.m_ers_perc) + "%"
            if driver_data.m_tyre_wear is not None:
                driver_data.m_tyre_wear = F1Utils.floatToStr(driver_data.m_tyre_wear) + "%"
            if driver_data.m_telemetry_restrictions is not None:
                driver_data.m_telemetry_restrictions = str(driver_data.m_telemetry_restrictions)
            else:
                driver_data.m_telemetry_restrictions = "N/A"
            if driver_data.m_packet_lap_data:
                driver_data.m_corner_cutting_warnings = driver_data.m_packet_lap_data.m_cornerCuttingWarnings
                driver_data.m_time_penalties = driver_data.m_packet_lap_data.m_penalties
                driver_data.m_num_dt = driver_data.m_packet_lap_data.m_numUnservedDriveThroughPens
                driver_data.m_num_sg = driver_data.m_packet_lap_data.m_numUnservedStopGoPens
                if self.m_track_length:
                    driver_data.m_lap_progress = (driver_data.m_packet_lap_data.m_lapDistance /
                                                            self.m_track_length) * 100.0
                else:
                    driver_data.m_lap_progress = None
            else:
                driver_data.m_lap_progress = None
                driver_data.m_corner_cutting_warnings = None
                driver_data.m_time_penalties = None
                driver_data.m_num_dt = None
                driver_data.m_num_sg = None

    def _recomputeDeltas(self):
        """Recompute the deltas for the list of driver data relative to the player
        """

        # pylint: disable=too-many-branches
        self.m_final_list[0].m_delta_to_car_in_front = "---"
        if self.m_is_spectator_mode:
            # just convert the deltas to str
            for data in self.m_final_list:
                if data.m_delta_to_car_in_front is not None and isinstance(data.m_delta_to_car_in_front, int):
                    data.m_delta_to_car_in_front = self._millisecondsToSecondsStr(data.m_delta_to_car_in_front)
                else:
                    data.m_delta_to_car_in_front = "---"
                data.m_last_lap_delta = "---"
                data.m_best_lap_delta = "---"
        else:
            # recompute the deltas if not spectator mode
            player_index = next((index for index, item in enumerate(self.m_final_list) if item.m_is_player), None)
            if self.m_final_list[player_index].m_last_lap == "---":
                player_last_lap_ms = None
            else:
                player_last_lap_ms = F1Utils.timeStrToMilliseconds(self.m_final_list[player_index].m_last_lap)
            fastest_lap_ms = self.m_final_list[player_index].m_best_lap_ms

            # case 1: player is in the absolute front of this pack
            if player_index == 0:
                self.m_final_list[0].m_delta_to_car_in_front = "---"
                delta_so_far = 0
                for data in self.m_final_list[1:]:
                    delta_so_far += data.m_delta_to_car_in_front
                    data.m_delta_to_car_in_front = self._millisecondsToSecondsStr(delta_so_far)

            # case 2: player is in the back of the pack
            # Iterate from back to front using reversed need to look at previous car's data for distance ahead
            elif player_index == len(self.m_final_list) - 1:
                delta_so_far = 0
                one_car_behind_index = len(self.m_final_list)-1
                one_car_behind_delta = self.m_final_list[one_car_behind_index].m_delta_to_car_in_front
                for data in reversed(self.m_final_list[:len(self.m_final_list)-1]):
                    delta_so_far -= one_car_behind_delta
                    one_car_behind_delta = data.m_delta_to_car_in_front
                    data.m_delta_to_car_in_front = self._millisecondsToSecondsStr(delta_so_far)
                self.m_final_list[len(self.m_final_list)-1].m_delta_to_car_in_front = "---"

            # case 3: player is somewhere in the middle of the pack
            else:

                # First, set the deltas for the cars ahead
                delta_so_far = 0
                one_car_behind_index = player_index
                one_car_behind_delta = self.m_final_list[one_car_behind_index].m_delta_to_car_in_front
                for data in reversed(self.m_final_list[:player_index]):
                    delta_so_far -= one_car_behind_delta
                    one_car_behind_delta = data.m_delta_to_car_in_front
                    data.m_delta_to_car_in_front = self._millisecondsToSecondsStr(delta_so_far)

                # Finally, set the deltas for the cars ahead
                delta_so_far = 0
                for data in self.m_final_list[player_index+1:]:
                    delta_so_far += data.m_delta_to_car_in_front
                    data.m_delta_to_car_in_front = self._millisecondsToSecondsStr(delta_so_far)

                # finally set the delta for the player
                self.m_final_list[player_index].m_delta_to_car_in_front = "---"

            # Update the race leader's delta to car in front
            if self.m_final_list[0].m_position == 1:
                self.m_final_list[0].m_delta_to_car_in_front = "---"

            # Set the last lap delta and best lap delta
            for data in self.m_final_list:
                if data.m_is_player:
                    data.m_last_lap_delta = data.m_last_lap
                    data.m_best_lap_delta = data.m_best_lap_str
                else:
                    if player_last_lap_ms is not None and data.m_last_lap != "---" and data.m_last_lap is not None:
                        data.m_last_lap_delta = self._millisecondsToSecondsStr(
                            F1Utils.timeStrToMilliseconds(data.m_last_lap) - player_last_lap_ms)
                    else:
                        data.m_last_lap_delta = "---"

                    if fastest_lap_ms is not None and data.m_best_lap_ms != 0 and data.m_best_lap_ms is not None:
                        data.m_best_lap_delta = self._millisecondsToSecondsStr(data.m_best_lap_ms - fastest_lap_ms)
                    else:
                        data.m_best_lap_delta = "---"

    def _millisecondsToSecondsStr(self, ms: float) -> str:
        """
        Convert milliseconds to a formatted string representing seconds.

        Args:
            ms (float): Time duration in milliseconds.

        Returns:
            str: Formatted string representing the time duration in seconds.
        """
        sign = "+" if ms >= 0 else ""
        seconds = ms / 1000
        return f"{sign}{seconds:.3f}"
