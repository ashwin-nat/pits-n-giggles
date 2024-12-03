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
from typing import Dict, Any, Optional, List
from lib.f1_types import F1Utils, LapHistoryData, CarStatusData
import lib.race_analyzer as RaceAnalyzer
from lib.tyre_wear_extrapolator import TyreWearPerLap
import src.telemetry_data as TelData
from src.telemetry_handler import dumpPktCapToFile, getOvertakeJSON, GetOvertakesStatus

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

        self.m_globals = TelData.getGlobals()
        track_length = self.m_globals.m_packet_session.m_trackLength if self.m_globals.m_packet_session else None
        self.m_driver_list_rsp = DriversListRsp(self.m_globals.m_is_spectating, track_length)
        self.m_curr_lap = self.m_driver_list_rsp.getCurrentLap()
        if self.m_globals.m_weather_forecast_samples is None:
            self.m_globals.m_weather_forecast_samples = []

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON update for the current race

        Returns:
            Dict[str, Any]: JSON response.
        """

        final_json = {
            # First, global fields
            "f1-game-year" : _getValueOrDefaultValue(self.m_globals.m_game_year, None),
            "circuit": _getValueOrDefaultValue(self.m_globals.m_circuit),
            "track-temperature": _getValueOrDefaultValue(self.m_globals.m_track_temp, default_value=0),
            "air-temperature": _getValueOrDefaultValue(self.m_globals.m_air_temp, default_value=0),
            "event-type": _getValueOrDefaultValue(self.m_globals.m_event_type),
            "session-time-left" : _getValueOrDefaultValue(self.m_globals.m_packet_session.m_sessionTimeLeft \
                                                          if self.m_globals.m_packet_session else None, 0),
            "total-laps": _getValueOrDefaultValue(self.m_globals.m_total_laps),
            "current-lap": _getValueOrDefaultValue(self.m_curr_lap),
            "safety-car-status": str(_getValueOrDefaultValue(self.m_globals.m_safety_car_status, default_value="")),
            "pit-speed-limit": _getValueOrDefaultValue(self.m_globals.m_pit_speed_limit, default_value=0),
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

        final_json["table-entries"] = self.m_driver_list_rsp.toJSON()
        final_json["fastest-lap-overall"] = _getValueOrDefaultValue(
            self.m_driver_list_rsp.m_fastest_lap, default_value=0)
        final_json["fastest-lap-overall-driver"] = _getValueOrDefaultValue(
            self.m_driver_list_rsp.m_fastest_lap_driver)
        self._updatePlayerLapTimes(final_json["table-entries"])
        return final_json

    def _updatePlayerLapTimes(self,
                              table_entries_json: List[Dict[str, Any]]) -> None:
        """Update the lap-info key's contents

        Args:
            table_entries_json (List[Dict[str, Any]]): The "table-entries" list
        """

        player_entry = next(
            (
                table_entry
                for table_entry in table_entries_json
                if table_entry["driver-info"]["is-player"]
            ),
            None,
        )

        # Supporting only single player entry, split screen unsupported. player_entry should've been found by now
        if player_entry:
            for table_entry in table_entries_json:
                # Update last lap time for player in every object
                if table_entry["driver-info"]["index"] != player_entry["driver-info"]["index"]:
                    # TODO: deprecate
                    # Fill the player time fields from the identified player_entry object
                    table_entry["lap-info"]["last-lap-ms-player"] = player_entry["lap-info-new"]["last-lap"]["lap-time-ms"]
                    table_entry["lap-info"]["best-lap-ms-player"] = player_entry["lap-info-new"]["best-lap"]["lap-time-ms"]
                    table_entry["lap-info-new"]["last-lap"]["lap-time-ms-player"] = player_entry["lap-info-new"]["last-lap"]["lap-time-ms"]
                    table_entry["lap-info-new"]["best-lap"]["lap-time-ms-player"] = player_entry["lap-info-new"]["best-lap"]["lap-time-ms"]
                else:
                    table_entry["lap-info"]["last-lap-ms-player"] = table_entry["lap-info-new"]["last-lap"]["lap-time-ms"]
                    table_entry["lap-info"]["best-lap-ms-player"] = table_entry["lap-info-new"]["best-lap"]["lap-time-ms"]
                    table_entry["lap-info-new"]["last-lap"]["lap-time-ms-player"] = table_entry["lap-info-new"]["last-lap"]["lap-time-ms"]
                    table_entry["lap-info-new"]["best-lap"]["lap-time-ms-player"] = table_entry["lap-info-new"]["best-lap"]["lap-time-ms"]


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

        self.m_rsp["custom-markers"] = TelData.getCustomMarkersJSON()
        if TelData.isPositionHistorySupported():
            self.m_rsp["position-history"] = DriversListRsp(is_spectator_mode=True).getPositionHistoryJSON()

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

class PlayerTelemetryOverlayUpdate:
    """
    Player telemetry overlay update class.
    """

    def __init__(self):
        """Get the player telemetry data and prep the fields
        """

        with TelData._globals_lock.gen_rlock():
            self.m_track_temp               = TelData._globals.m_track_temp
            self.m_air_temp                 = TelData._globals.m_air_temp
            self.m_weather_forecast_samples = TelData._globals.m_weather_forecast_samples
            if self.m_weather_forecast_samples is None:
                self.m_weather_forecast_samples = []
            self.m_circuit                  = TelData._globals.m_circuit
            self.m_total_laps               = TelData._globals.m_total_laps
            self.m_game_year                = TelData._globals.m_game_year

        with TelData._driver_data_lock.gen_rlock():
            self.m_next_pit_window          = TelData._driver_data.m_ideal_pit_stop_window
            player_data = TelData._driver_data.m_driver_data[TelData._driver_data.m_player_index] \
                if TelData._driver_data.m_player_index in TelData._driver_data.m_driver_data else None

        self.__initCarTelemetry(player_data)
        self.__initLapTimes(player_data)
        self.__initTyreWear(player_data)
        self.__initPenalties(player_data)
        self.__initGForce(player_data)

    def __initCarTelemetry(self, player_data: Optional[TelData.DataPerDriver]) -> None:
        """Prepares the car telemetry data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        if player_data and player_data.m_packet_car_telemetry:
            self.m_throttle = player_data.m_packet_car_telemetry.m_throttle
            self.m_brake    = player_data.m_packet_car_telemetry.m_brake
            self.m_steering = player_data.m_packet_car_telemetry.m_steer
        else:
            self.m_throttle = 0
            self.m_brake    = 0
            self.m_steering = 0

    def __initLapTimes(self, player_data: Optional[TelData.DataPerDriver]) -> None:
        """Prepares the player's lap history data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        self.m_curr_lap: Optional[int] = player_data.m_current_lap if player_data else None
        self.m_lap_time_history: LapTimeHistory = LapTimeHistory(player_data)
        self.m_speed_trap_record: Optional[float] = player_data.m_packet_lap_data.m_speedTrapFastestSpeed \
            if player_data and player_data.m_packet_lap_data else None

    def __initTyreWear(self, player_data: Optional[TelData.DataPerDriver]) -> None:
        """Prepares the player's tyre wear data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        if player_data and player_data.m_packet_car_damage:
            self.m_tyre_wear = TyreWearPerLap(
                fl_tyre_wear=player_data.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                fr_tyre_wear=player_data.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                rl_tyre_wear=player_data.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                rr_tyre_wear=player_data.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                lap_number=self.m_curr_lap,
                is_racing_lap=True,
                desc="Curr tyre wear"
            )
            self.m_tyre_wear_predictions = player_data.getTyrePredictionsJSONList(self.m_next_pit_window)
        else:
            self.m_tyre_wear = TyreWearPerLap(
                fl_tyre_wear=0,
                fr_tyre_wear=0,
                rl_tyre_wear=0,
                rr_tyre_wear=0,
                lap_number=0,
                is_racing_lap=True,
                desc="No data"
            )
            self.m_tyre_wear_predictions = []

    def __initPenalties(self, player_data: Optional[TelData.DataPerDriver]) -> None:
        """Prepares the player's penalties data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        if player_data and player_data.m_packet_lap_data:
            self.m_penalties = player_data.m_packet_lap_data.m_penalties
            self.m_total_warnings = player_data.m_packet_lap_data.m_totalWarnings
            self.m_corner_cutting_warnings = player_data.m_packet_lap_data.m_cornerCuttingWarnings
            self.m_num_dt = player_data.m_packet_lap_data.m_numUnservedDriveThroughPens
            self.m_num_sg = player_data.m_packet_lap_data.m_numUnservedStopGoPens
            self.m_num_collisions = len(player_data.m_collision_records)
        else:
            self.m_penalties = 0
            self.m_total_warnings = 0
            self.m_corner_cutting_warnings = 0
            self.m_num_dt = 0
            self.m_num_sg = 0
            self.m_num_collisions = 0

    def __initGForce(self, player_data: Optional[TelData.DataPerDriver]) -> None:
        """Prepares the player's g-force data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        if player_data and player_data.m_packet_motion:
            self.m_g_force_lat = player_data.m_packet_motion.m_gForceLateral
            self.m_g_force_vert = player_data.m_packet_motion.m_gForceVertical
            self.m_g_force_long = player_data.m_packet_motion.m_gForceLongitudinal
        else:
            self.m_g_force_lat = 0
            self.m_g_force_vert = 0
            self.m_g_force_long = 0

    def toJSON(self) -> Dict[str, Any]:
        """Dump this object into JSON

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return {
            "f1-game-year" : self.m_game_year,
            "circuit" : self.m_circuit,
            "track-temp": self.m_track_temp,
            "air-temp": self.m_air_temp,
            "weather-forecast-samples": [
                {
                    "time-offset": sample.m_timeOffset,
                    "weather": str(sample.m_weather),
                    "rain-probability": sample.m_rainPercentage
                } for sample in self.m_weather_forecast_samples
            ],
            "lap-time-history" : self.m_lap_time_history.toJSON(),
            "car-telemetry" : {
                # The UI expects 0 to 100
                "throttle": (self.m_throttle * 100),
                "brake": (self.m_brake * 100),
                "steering" : (self.m_steering * 100),
            },
            "tyre-wear" : {
                "current" : self.m_tyre_wear.toJSON(),
                "predictions" : self.m_tyre_wear_predictions,
                "pit-window" : self.m_next_pit_window
            },
            "penalties-and-stats" : {
                "time-penalties": self.m_penalties,
                "total-warnings": self.m_total_warnings,
                "corner-cutting-warnings": self.m_corner_cutting_warnings,
                "unserved-drive-through-pens": self.m_num_dt,
                "unserved-stop-go-pens": self.m_num_sg,
                "num-collisions" : self.m_num_collisions,
                "speed-trap-record": self.m_speed_trap_record,
            },
            "g-force": {
                "lat": self.m_g_force_lat,
                "vert": self.m_g_force_vert,
                "long": self.m_g_force_long
            }
        }

# ------------------------- HELPER - CLASSES ---------------------------------------------------------------------------

class DriversListRsp:
    """
    Drivers list response class.
    """

    def __init__(self, is_spectator_mode: bool, track_length: Optional[int] = None):
        """Get the drivers list and prepare the rsp fields

        Args:
            is_spectator_mode (bool): Whether the player is in spectator mode
            track_length (Optional[int], optional): The track length. Defaults to None.
        """

        self.m_is_spectator_mode : bool = is_spectator_mode
        self.m_track_length : int = track_length
        self.m_final_list : List[TelData.DataPerDriver] = []
        self.m_fastest_lap : Optional[int] = None
        self.m_fastest_lap_driver: Optional[str] = None
        self.m_next_pit_stop_window: Optional[int] = None
        self.__initDriverList()
        self.__updateDriverList()
        if self.m_final_list:
            self._recomputeDeltas()

    def toJSON(self) -> Dict[str, Any]:
        """Dump this object into JSON

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return [
            {
                "driver-info" : {
                    "position": _getValueOrDefaultValue(data_per_driver.m_position),
                    "name": _getValueOrDefaultValue(data_per_driver.m_name),
                    "team": _getValueOrDefaultValue(data_per_driver.m_team),
                    "is-fastest": _getValueOrDefaultValue(data_per_driver.m_is_fastest),
                    "is-player": _getValueOrDefaultValue(data_per_driver.m_is_player),
                    "dnf-status" : _getValueOrDefaultValue(data_per_driver.m_dnf_status_code),
                    "index" : _getValueOrDefaultValue(data_per_driver.m_index),
                    "telemetry-setting" : data_per_driver.m_telemetry_restrictions, # Already NULL checked
                    "drs": self.__getDRSValue(data_per_driver.m_drs_activated, data_per_driver.m_drs_allowed,
                                        data_per_driver.m_drs_distance),
                },
                "delta-info" : {
                    "delta": self.__getDeltaPlusPenaltiesPlusPit(data_per_driver.m_delta_to_car_in_front,
                                                            data_per_driver.m_penalties,
                                                            data_per_driver.m_is_pitting,
                                                            data_per_driver.m_dnf_status_code),
                    "delta-to-leader": self.__getDeltaPlusPenaltiesPlusPit(
                                F1Utils.millisecondsToSecondsMilliseconds(data_per_driver.m_delta_to_leader),
                                                            data_per_driver.m_penalties,
                                                            data_per_driver.m_is_pitting,
                                                            data_per_driver.m_dnf_status_code),
                },
                "ers-info" : {
                    "ers-percent": _getValueOrDefaultValue(data_per_driver.m_ers_perc),
                    "ers-mode" : _getValueOrDefaultValue(str(data_per_driver.m_packet_car_status.m_ersDeployMode)
                                                        if data_per_driver.m_packet_car_status else None),
                    "ers-harvested-by-mguk-this-lap" : (((data_per_driver.m_packet_car_status.m_ersHarvestedThisLapMGUK
                                                        if data_per_driver.m_packet_car_status else 0.0) /
                                                            CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0),
                    "ers-deployed-this-lap" : ((data_per_driver.m_packet_car_status.m_ersDeployedThisLap
                                                if data_per_driver.m_packet_car_status else 0.0) /
                                                    CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0,
                },
                "lap-info" : {
                    "last-lap-ms" : data_per_driver.m_last_lap_ms,
                    "best-lap-ms" : data_per_driver.m_best_lap_ms,
                    "last-lap-ms-player" : 0,
                    "best-lap-ms-player" : 0,
                    "lap-progress" : data_per_driver.m_lap_progress, # NULL is supported
                    "speed-trap-record-kmph" : data_per_driver.m_packet_lap_data.m_speedTrapFastestSpeed if \
                        data_per_driver.m_packet_lap_data else None, # NULL is supported
                },
                "lap-info-new" : {
                    "last-lap" : {
                        "lap-time-ms" : data_per_driver.m_last_lap_ms,
                        "lap-time-ms-player" : 0,
                        "sector-status" : [
                            0,
                            1,
                            2,
                        ]
                    },
                    "best-lap" : {
                        "lap-time-ms" : data_per_driver.m_best_lap_ms,
                        "lap-time-ms-player" : 0,
                        "sector-status" : [
                            0,
                            1,
                            2,
                        ]
                    },
                    "lap-progress" : data_per_driver.m_lap_progress, # NULL is supported
                    "speed-trap-record-kmph" : data_per_driver.m_packet_lap_data.m_speedTrapFastestSpeed if \
                        data_per_driver.m_packet_lap_data else None, # NULL is supported
                },
                "warns-pens-info" : {
                    "corner-cutting-warnings" : _getValueOrDefaultValue(data_per_driver.m_corner_cutting_warnings),
                    "time-penalties" : _getValueOrDefaultValue(data_per_driver.m_time_penalties),
                    "num-dt" : _getValueOrDefaultValue(data_per_driver.m_num_dt),
                    "num-sg" : _getValueOrDefaultValue(data_per_driver.m_num_sg),
                },
                "tyre-info" : {
                    "wear-prediction" : data_per_driver.getTyrePredictionsJSONList(self.m_next_pit_stop_window),
                    "current-wear" : data_per_driver.getCurrentTyreWearJSON(),
                    "tyre-age": _getValueOrDefaultValue(data_per_driver.m_tyre_age),
                    "tyre-life-remaining" : _getValueOrDefaultValue(data_per_driver.m_tyre_life_remaining_laps),
                    "visual-tyre-compound": str(_getValueOrDefaultValue(data_per_driver.m_tyre_vis_compound,
                                                                        default_value="")),
                    "actual-tyre-compound": str(_getValueOrDefaultValue(data_per_driver.m_tyre_act_compound,
                                                                        default_value="")),
                    "num-pitstops": _getValueOrDefaultValue(data_per_driver.m_num_pitstops),
                },
                "damage-info" : {
                    "fl-wing-damage" : data_per_driver.m_fl_wing_damage, # NULL is supported
                    "fr-wing-damage" : data_per_driver.m_fr_wing_damage, # NULL is supported
                    "rear-wing-damage" : data_per_driver.m_rear_wing_damage, # NULL is supported
                },

                "fuel-info" : data_per_driver.getFuelStatsJSON(),
            } for data_per_driver in self.m_final_list
        ]

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

    def getPositionHistoryJSON(self) -> List[Dict[str, Any]]:
        """Get position history.

        Returns:
            List[Dict[str, Any]]: The position history JSON
        """

        if not self.m_final_list:
            return []

        return [data_per_driver.getPositionHistoryJSON() for data_per_driver in self.m_final_list]

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

        with TelData._driver_data_lock.gen_rlock():
            # Do the bare mimnimum within this block so that we can unlock the mutex ASAP
            if (TelData._driver_data.m_player_index is None) or (TelData._driver_data.m_num_active_cars is None):
                return

            # Update the list data
            self.m_next_pit_stop_window = TelData._driver_data.m_ideal_pit_stop_window
            if TelData._driver_data.m_fastest_index is not None:
                self.m_fastest_lap = TelData._driver_data.m_driver_data[
                                        TelData._driver_data.m_fastest_index].m_best_lap_ms
                self.m_fastest_lap_driver = TelData._driver_data.m_driver_data[
                                            TelData._driver_data.m_fastest_index].m_name
            positions = list(range(1, TelData._driver_data.m_num_active_cars + 1))
            for position in positions:
                index, temp_data = TelData._driver_data.getIndexByTrackPosition(position)
                if (index, temp_data) == (None, None):
                    return

                temp_data.m_index = index
                temp_data.m_is_fastest = (index == TelData._driver_data.m_fastest_index)

                # Add this prepped record into the final list
                self.m_final_list.append(temp_data)

    def __updateDriverList(self) -> None:
        """Add extra fields to each DataPerDriver object
        """

        for driver_data in self.m_final_list:
            if driver_data.m_ers_perc is not None:
                driver_data.m_ers_perc = F1Utils.floatToStr(driver_data.m_ers_perc) + "%"
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

        self.m_final_list[0].m_delta_to_car_in_front = "---"
        if self.m_is_spectator_mode:
            # just convert the deltas to str
            for data in self.m_final_list:
                if data.m_delta_to_car_in_front is not None and isinstance(data.m_delta_to_car_in_front, int):
                    data.m_delta_to_car_in_front = self._millisecondsToSecondsStr(data.m_delta_to_car_in_front)
                else:
                    data.m_delta_to_car_in_front = "---"
        else:
            # recompute the deltas if not spectator mode
            player_index = next((index for index, item in enumerate(self.m_final_list) if item.m_is_player), None)

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

class LapTimeInfo():
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
        m_tyre_set_info (TelData.DataPerDriver.TyreSetInfo): The tyre set used.
    """
    def __init__(self,
                 lap_history_data: LapHistoryData,
                 tyre_set_info: TelData.DataPerDriver.TyreSetInfo,
                 lap_number: int) -> None:
        """
        Initializes LapTimeInfo with an existing LapHistoryData object, tyre set info and lap number.

        Args:
            lap_history_data (LapHistoryData): An instance of LapHistoryData.
            tyre_set_info (TelData.DataPerDriver.TyreSetInfo): The tyre set info for this lap
            lap_number (int): The lap number for this lap
        """
        # Initialize the base class attributes by copying from the existing LapHistoryData instance
        self.m_lapTimeInMS = lap_history_data.m_lapTimeInMS
        self.m_sector1TimeInMS = lap_history_data.m_sector1TimeInMS
        self.m_sector1TimeMinutes = lap_history_data.m_sector1TimeMinutes
        self.m_sector2TimeInMS = lap_history_data.m_sector2TimeInMS
        self.m_sector2TimeMinutes = lap_history_data.m_sector2TimeMinutes
        self.m_sector3TimeInMS = lap_history_data.m_sector3TimeInMS
        self.m_sector3TimeMinutes = lap_history_data.m_sector3TimeMinutes
        self.m_lapValidBitFlags = lap_history_data.m_lapValidBitFlags

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
            "lap-number": self.m_lap_number
        }

class LapTimeHistory:
    """Class representing lap time history data along with tyre set used

    Attributes:
        m_fastest_lap_number (int): Fastest lap number.
        m_fastest_s1_lap_number (int): Fastest sector 1 lap number.
        m_fastest_s2_lap_number (int): Fastest sector 2 lap number.
        m_fastest_s3_lap_number (int): Fastest sector 3 lap number.
        m_lap_time_history_data (List[LapTimeInfo]): List of LapTimeInfo objects representing lap time history data.
    """

    def __init__(self, driver_data: Optional[TelData.DataPerDriver] = None) -> None:
        """
        Initializes LapTimeHistory with an optional DataPerDriver object.

        Args:
            driver_data (Optional[TelData.DataPerDriver], optional): An instance of DataPerDriver. Defaults to None.
        """

        if driver_data is None:
            self.m_fastest_lap_number: int = None

        if driver_data is None or driver_data.m_packet_session_history is None:
            self.m_fastest_lap_number: int = None
            self.m_fastest_s1_lap_number: int = None
            self.m_fastest_s2_lap_number: int = None
            self.m_fastest_s3_lap_number: int = None
            self.m_lap_time_history_data: List[LapHistoryData] = []
            return

        self.m_fastest_lap_number: int      = driver_data.m_packet_session_history.m_bestLapTimeLapNum
        self.m_fastest_s1_lap_number: int   = driver_data.m_packet_session_history.m_bestSector1LapNum
        self.m_fastest_s2_lap_number: int   = driver_data.m_packet_session_history.m_bestSector2LapNum
        self.m_fastest_s3_lap_number: int   = driver_data.m_packet_session_history.m_bestSector3LapNum
        self.m_lap_time_history_data: List[LapHistoryData] = []

        for index, lap_info in enumerate(driver_data.m_packet_session_history.m_lapHistoryData):
            lap_number = index + 1
            self.m_lap_time_history_data.append(LapTimeInfo(
                lap_history_data=lap_info,
                tyre_set_info=driver_data.getTyreSetInfoAtLap(lap_num=lap_number),
                lap_number=lap_number))

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the LapTimeHistory instance to a JSON-compatible dictionary with kebab-case keys.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the LapTimeHistory instance.
        """
        return {
            "fastest-lap-number": self.m_fastest_lap_number,
            "fastest-s1-lap-number": self.m_fastest_s1_lap_number,
            "fastest-s2-lap-number": self.m_fastest_s2_lap_number,
            "fastest-s3-lap-number": self.m_fastest_s3_lap_number,
            "lap-time-history-data": [lap_time_info.toJSON() for lap_time_info in self.m_lap_time_history_data]
        }
