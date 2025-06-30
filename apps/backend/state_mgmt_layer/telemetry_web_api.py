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
from typing import Any, Dict, List, Optional, Union

import lib.race_analyzer as RaceAnalyzer
import apps.backend.state_mgmt_layer.telemetry_state as TelState
from lib.f1_types import (CarStatusData, F1Utils, LapHistoryData,
                          VisualTyreCompound)
from lib.tyre_wear_extrapolator import TyreWearPerLap
from apps.backend.state_mgmt_layer.data_per_driver import DataPerDriver, TyreSetInfo
from apps.backend.state_mgmt_layer.overtakes import GetOvertakesStatus

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_logger: logging.Logger = None
_session_state_ref: TelState.SessionState = None

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

def initApiLayer(logger: logging.Logger) -> None:
    """Initialise the API layer by fetching the session state from the data store.
    """
    global _session_state_ref, _logger
    _session_state_ref = TelState.getSessionStateRef()
    _logger = logger
    assert _session_state_ref is not None

# ------------------------- API - CLASSES ------------------------------------------------------------------------------

class RaceInfoUpdate:
    """This class will prepare the live race telemetry info response. Use toJSON() method to get the JSON rsp
    """
    def __init__(self) -> None:
        """Initialse the member variables by fetching necessary data from the data store

        """

        self.m_session_info = _session_state_ref.m_session_info
        track_length = self.m_session_info.m_packet_session.m_trackLength if self.m_session_info.m_packet_session else None
        self.m_driver_list_rsp = DriversListRsp(self.m_session_info.m_is_spectating, track_length,
                                                (str(self.m_session_info.m_session_type) == "Time Trial"))
        self.m_curr_lap = self.m_driver_list_rsp.getCurrentLap()
        if self.m_session_info.m_weather_forecast_samples is None:
            self.m_session_info.m_weather_forecast_samples = []

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON update for the current race

        Returns:
            Dict[str, Any]: JSON response.
        """

        final_json = {
            # First, global fields
            "live-data" : True,
            "f1-game-year" : _getValueOrDefaultValue(self.m_session_info.m_game_year, None),
            "packet-format" : _getValueOrDefaultValue(self.m_session_info.m_packet_format, None),
            "circuit": str(self.m_session_info.m_track) if self.m_session_info.m_track is not None else "---",
            "track-temperature": _getValueOrDefaultValue(self.m_session_info.m_track_temp, default_value=0),
            "air-temperature": _getValueOrDefaultValue(self.m_session_info.m_air_temp, default_value=0),
            "event-type": _getValueOrDefaultValue(str(self.m_session_info.m_session_type)),
            "session-time-left" : _getValueOrDefaultValue(self.m_session_info.m_packet_session.m_sessionTimeLeft \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "total-laps": _getValueOrDefaultValue(self.m_session_info.m_total_laps, default_value=None),
            "current-lap": _getValueOrDefaultValue(self.m_curr_lap, default_value=None),
            "safety-car-status": str(_getValueOrDefaultValue(self.m_session_info.m_safety_car_status, default_value="")),
            "pit-speed-limit": _getValueOrDefaultValue(self.m_session_info.m_pit_speed_limit, default_value=0),
            "weather-forecast-samples": [
                {
                    "time-offset": str(sample.m_timeOffset),
                    "weather": str(sample.m_weather),
                    "rain-probability": str(sample.m_rainPercentage)
                } for sample in self.m_session_info.m_weather_forecast_samples
            ],
            "race-ended" : self.m_session_info.session_ended,
            "is-spectating" : _getValueOrDefaultValue(self.m_session_info.m_is_spectating, False),
            "session-type"  : str(self.m_session_info.m_session_type) \
                if self.m_session_info.m_session_type is not None else "---",
            "session-duration-so-far" : _getValueOrDefaultValue(
                (self.m_session_info.m_packet_session.m_sessionDuration - self.m_session_info.m_packet_session.m_sessionTimeLeft) \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "num-sc" : _getValueOrDefaultValue(self.m_session_info.m_packet_session.m_numSafetyCarPeriods \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "num-vsc" : _getValueOrDefaultValue(self.m_session_info.m_packet_session.m_numVirtualSafetyCarPeriods \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "num-red-flags" : _getValueOrDefaultValue(self.m_session_info.m_packet_session.m_numRedFlagPeriods \
                                                          if self.m_session_info.m_packet_session else None, 0),
            "player-pit-window" : _getValueOrDefaultValue(self.m_driver_list_rsp.m_next_pit_stop_window, None),
            "spectator-car-index" : _getValueOrDefaultValue(self.m_session_info.m_spectator_car_index, None),
        }

        if str(self.m_session_info.m_session_type) == "Time Trial":
            final_json["tt-data"] = self.m_driver_list_rsp.toJSON()
        else:
            final_json["table-entries"] = self.m_driver_list_rsp.toJSON()

        final_json["fastest-lap-overall"] = _getValueOrDefaultValue(
            self.m_driver_list_rsp.m_fastest_lap, default_value=0)
        final_json["fastest-lap-overall-driver"] = _getValueOrDefaultValue(
            self.m_driver_list_rsp.m_fastest_lap_driver)
        final_json["fastest-lap-overall-tyre"] = str(self.m_driver_list_rsp.m_fastest_lap_tyre) \
            if self.m_driver_list_rsp.m_fastest_lap_tyre else None
        return final_json

class OverallRaceStatsRsp:
    """
    Overall race stats response class.
    """

    def __init__(self):
        """Get the overall race stats and prepare the rsp fields
        """

        self.m_rsp = _session_state_ref.getRaceInfo()
        self._checkUpdateRecords()
        # Remove the classification-data key as it is not used by the frontend
        self.m_rsp.pop('classification-data', None)

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
                _logger.debug('Failed to get fastest times JSON')
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
            _, overtake_records = _session_state_ref.getOvertakeJSON()
            self.m_rsp["overtakes"] = self.m_rsp["overtakes"] | overtake_records

        self.m_rsp["custom-markers"] = _session_state_ref.m_custom_markers_history.getJSONList()
        if _session_state_ref.isPositionHistorySupported():
            drivers_list_rsp = DriversListRsp(
                                    is_spectator_mode=True,
                                    is_tt_mode=str(_session_state_ref.m_session_info.m_session_type) == "Time Trial")
            self.m_rsp["position-history"] = drivers_list_rsp.getPositionHistoryJSON()
            if _session_state_ref.m_session_info.m_packet_format == 2023:
                self.m_rsp["tyre-stint-history"] = drivers_list_rsp.getTyreStintHistoryJSON()
            else:
                self.m_rsp["tyre-stint-history-v2"] = drivers_list_rsp.getTyreStintHistoryJSONv2()

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

        self.m_rsp = _session_state_ref.getDriverInfoJsonByIndex(index)
        assert self.m_rsp
        status, overtakes_info = _session_state_ref.getOvertakeJSON(self.m_rsp["driver-name"])
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

        self.m_track_temp               = _session_state_ref.m_session_info.m_track_temp
        self.m_air_temp                 = _session_state_ref.m_session_info.m_air_temp
        self.m_weather_forecast_samples = _session_state_ref.m_session_info.m_weather_forecast_samples
        if self.m_weather_forecast_samples is None:
            self.m_weather_forecast_samples = []
        self.m_circuit                  = _session_state_ref.m_session_info.m_track
        self.m_total_laps               = _session_state_ref.m_session_info.m_total_laps
        self.m_game_year                = _session_state_ref.m_session_info.m_game_year
        self.m_packet_format            = _session_state_ref.m_session_info.m_packet_format
        self.m_session_type               = _session_state_ref.m_session_info.m_session_type
        self.m_pit_speed_limit          = _session_state_ref.m_session_info.m_pit_speed_limit

        self.m_next_pit_window          = _session_state_ref.m_ideal_pit_stop_window
        self.m_fastest_lap_ms           = \
            _session_state_ref.m_driver_data[_session_state_ref.m_fastest_index].m_lap_info.m_best_lap_ms if \
                _session_state_ref.m_fastest_index is not None else None
        self.m_fastest_s1_ms            = _session_state_ref.m_fastest_s1_ms
        self.m_fastest_s2_ms            = _session_state_ref.m_fastest_s2_ms
        self.m_fastest_s3_ms            = _session_state_ref.m_fastest_s3_ms
        player_index = _session_state_ref.m_session_info.m_spectator_car_index \
                        if _session_state_ref.m_session_info.m_is_spectating \
                        else _session_state_ref.m_player_index
        player_data = (
            _session_state_ref.m_driver_data[player_index]
            if player_index is not None and 0 <= player_index < len(_session_state_ref.m_driver_data)
            else None
        )
        player_position = player_data.m_driver_info.position if player_data else None
        prev_data = _session_state_ref.getDriverInfoByPosition(player_position - 1) if player_position else None
        next_data = _session_state_ref.getDriverInfoByPosition(player_position + 1) if player_position else None

        self.__initCarTelemetry(player_data)
        self.__initLapTimes(player_data)
        self.__initTyreWear(player_data)
        self.__initPenalties(player_data)
        self.__initGForce(player_data)
        self.__initPaceComparison(player_data, prev_data, next_data)

    def __initCarTelemetry(self, player_data: Optional[DataPerDriver]) -> None:
        """Prepares the car telemetry data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        if player_data and player_data.m_packet_copies.m_packet_car_telemetry:
            self.m_throttle = player_data.m_packet_copies.m_packet_car_telemetry.m_throttle
            self.m_brake    = player_data.m_packet_copies.m_packet_car_telemetry.m_brake
            self.m_steering = player_data.m_packet_copies.m_packet_car_telemetry.m_steer
        else:
            self.m_throttle = 0
            self.m_brake    = 0
            self.m_steering = 0

    def __initLapTimes(self, player_data: Optional[DataPerDriver]) -> None:
        """Prepares the player's lap history data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        self.m_curr_lap: Optional[int] = player_data.m_lap_info.m_current_lap if player_data else None
        self.m_lap_time_history: LapTimeHistory = LapTimeHistory(
            player_data, self.m_fastest_lap_ms, self.m_fastest_s1_ms, self.m_fastest_s2_ms, self.m_fastest_s3_ms)
        self.m_speed_trap_record: Optional[float] = player_data.m_packet_copies.m_packet_lap_data.m_speedTrapFastestSpeed \
            if player_data and player_data.m_packet_copies.m_packet_lap_data else None

    def __initTyreWear(self, player_data: Optional[DataPerDriver]) -> None:
        """Prepares the player's tyre wear data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        if player_data and player_data.m_packet_copies.m_packet_car_damage:
            self.m_tyre_wear = TyreWearPerLap(
                fl_tyre_wear=player_data.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                fr_tyre_wear=player_data.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                rl_tyre_wear=player_data.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                rr_tyre_wear=player_data.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
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

    def __initPenalties(self, player_data: Optional[DataPerDriver]) -> None:
        """Prepares the player's penalties data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        if player_data and player_data.m_packet_copies.m_packet_lap_data:
            self.m_penalties = player_data.m_packet_copies.m_packet_lap_data.m_penalties
            self.m_total_warnings = player_data.m_packet_copies.m_packet_lap_data.m_totalWarnings
            self.m_corner_cutting_warnings = player_data.m_packet_copies.m_packet_lap_data.m_cornerCuttingWarnings
            self.m_num_dt = player_data.m_packet_copies.m_packet_lap_data.m_numUnservedDriveThroughPens
            self.m_num_sg = player_data.m_packet_copies.m_packet_lap_data.m_numUnservedStopGoPens
            self.m_num_collisions = len(player_data.m_collision_records)
        else:
            self.m_penalties = 0
            self.m_total_warnings = 0
            self.m_corner_cutting_warnings = 0
            self.m_num_dt = 0
            self.m_num_sg = 0
            self.m_num_collisions = 0

    def __initGForce(self, player_data: Optional[DataPerDriver]) -> None:
        """Prepares the player's g-force data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        if player_data and player_data.m_packet_copies.m_packet_motion:
            self.m_g_force_lat = player_data.m_packet_copies.m_packet_motion.m_gForceLateral
            self.m_g_force_vert = player_data.m_packet_copies.m_packet_motion.m_gForceVertical
            self.m_g_force_long = player_data.m_packet_copies.m_packet_motion.m_gForceLongitudinal
        else:
            self.m_g_force_lat = 0
            self.m_g_force_vert = 0
            self.m_g_force_long = 0

    def __initPaceComparison(self,
                             player_data: DataPerDriver,
                             prev_data: Optional[DataPerDriver],
                             next_data: Optional[DataPerDriver]) -> None:
        """Prepares the player's pace comparison data.

        Args:
            player_data (TelData.DataPerDriver): The player's DataPerDriver object
            prev_data (Optional[TelData.DataPerDriver]): The previous driver's DataPerDriver object (may be None)
            next_data (Optional[TelData.DataPerDriver]): The next driver's DataPerDriver object (may be None)
        """
        self.m_pace_comp_json = {
            "player" : {
                "name" : None,
                "lap-ms" : None,
                "sector-1-ms" : None,
                "sector-2-ms" : None,
                "sector-3-ms" : None,
                "ers" : {
                    "ers-percent": None,
                    "ers-mode" : None,
                    "ers-harvested-by-mguk-this-lap" : None,
                    "ers-deployed-this-lap" : None,
                },
            },
            "prev" : {
                "name" : None,
                "lap-ms" : None,
                "sector-1-ms" : None,
                "sector-2-ms" : None,
                "sector-3-ms" : None,
                "ers" : {
                    "ers-percent": None,
                    "ers-mode" : None,
                    "ers-harvested-by-mguk-this-lap" : None,
                    "ers-deployed-this-lap" : None,
                },
            },
            "next" : {
                "name" : None,
                "lap-ms" : None,
                "sector-1-ms" : None,
                "sector-2-ms" : None,
                "sector-3-ms" : None,
                "ers" : {
                    "ers-percent": None,
                    "ers-mode" : None,
                    "ers-harvested-by-mguk-this-lap" : None,
                    "ers-deployed-this-lap" : None,
                },
            }
        }
        if not player_data:
            return

        self.__populatePaceCompDataForDriver(self.m_pace_comp_json["player"], player_data)
        self.__populatePaceCompDataForDriver(self.m_pace_comp_json["prev"], prev_data)
        self.__populatePaceCompDataForDriver(self.m_pace_comp_json["next"], next_data)

    def __populatePaceCompDataForDriver(self,
                                        json_dict: Dict[str, any],
                                        driver_obj: Optional[DataPerDriver]) -> None:
        """Populates the player's pace comparison data.

        Args:
            json_dict (Dict[str, any]): The JSON dict to populate
            driver_obj (Optional[TelData.DataPerDriver]): The driver's DataPerDriver object (may be None)
        """

        if not driver_obj:
            return
        json_dict["name"] = driver_obj.m_driver_info.name
        json_dict["lap-ms"] = driver_obj.m_lap_info.m_last_lap_ms
        last_lap_obj = driver_obj.m_packet_copies.m_packet_session_history.getLastLapData() if driver_obj.m_packet_copies.m_packet_session_history else None
        if last_lap_obj:
            json_dict["sector-1-ms"] = last_lap_obj.m_sector1TimeInMS
            json_dict["sector-2-ms"] = last_lap_obj.m_sector2TimeInMS
            json_dict["sector-3-ms"] = last_lap_obj.m_sector3TimeInMS
        json_dict["ers"] = {
            "ers-percent" : _getValueOrDefaultValue(driver_obj.m_car_info.m_ers_perc),
            "ers-mode" : _getValueOrDefaultValue(str(driver_obj.m_packet_copies.m_packet_car_status.m_ersDeployMode)
                                            if driver_obj.m_packet_copies.m_packet_car_status else None),
            "ers-harvested-by-mguk-this-lap" : (((driver_obj.m_packet_copies.m_packet_car_status.m_ersHarvestedThisLapMGUK
                                            if driver_obj.m_packet_copies.m_packet_car_status else 0.0) /
                                                CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0),
            "ers-deployed-this-lap" : ((driver_obj.m_packet_copies.m_packet_car_status.m_ersDeployedThisLap
                                    if driver_obj.m_packet_copies.m_packet_car_status else 0.0) /
                                        CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0
        }

    def toJSON(self, stream_overlay_start_sample_data: Optional[bool] = False) -> Dict[str, Any]:
        """Dump this object into JSON

        Args:
            stream_overlay_start_sample_data (Optional[bool], optional): Whether to include the start sample data

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return {
            "f1-game-year" : self.m_game_year,
            "event-type" : str(self.m_session_type),
            "show-sample-data-at-start": stream_overlay_start_sample_data,
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
                "circuit" : str(self.m_circuit),
                "track-temperature": self.m_track_temp,
                "air-temperature": self.m_air_temp,
                "pit-speed-limit": self.m_pit_speed_limit,
            },
            "g-force": {
                "lat": self.m_g_force_lat,
                "vert": self.m_g_force_vert,
                "long": self.m_g_force_long
            },
            "pace-comparison" : self.m_pace_comp_json,
        }

# ------------------------- HELPER - CLASSES ---------------------------------------------------------------------------

class DriversListRsp:
    """
    Drivers list response class.
    """

    def __init__(self, is_spectator_mode: bool, track_length: Optional[int] = None, is_tt_mode: bool = False):
        """Get the drivers list and prepare the rsp fields

        Args:
            is_spectator_mode (bool): Whether the player is in spectator mode
            track_length (Optional[int], optional): The track length. Defaults to None.
            is_tt_mode (bool, optional): Whether the player is in time trial mode
        """

        self.m_is_spectator_mode : bool = is_spectator_mode
        self.m_track_length : int = track_length
        self.m_json_rsp : Union[List[Dict[str, Any]], Dict[str, Any]] = [] # In TT mode dict, else list
        self.m_fastest_lap : Optional[int] = None
        self.m_fastest_lap_driver: Optional[str] = None
        self.m_fastest_lap_tyre: Optional[VisualTyreCompound] = None
        self.m_next_pit_stop_window: Optional[int] = None
        self.m_fastest_s1_ms: Optional[int] = None
        self.m_fastest_s2_ms: Optional[int] = None
        self.m_fastest_s3_ms: Optional[int] = None
        self.m_is_tt_mode : bool = is_tt_mode
        if self.m_is_tt_mode:
            self.__initTTDict()
        else:
            self.__initDriverList()

    def toJSON(self) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Get the drivers list JSON

        Returns:
            Union[List[Dict[str, Any]], Dict[str, Any]]: The JSON dump
        """
        return self.m_json_rsp

    def getCurrentLap(self) -> Optional[int]:
        """Get current lap.

        Returns:
            Optional[int]: The lap number. None if no race is ongoing
        """

        if len(self.m_json_rsp) == 0:
            return None

        if self.m_is_tt_mode:
            return self.m_json_rsp["current-lap"]

        if self.m_is_spectator_mode:
            return self.m_json_rsp[0]["lap-info"]["current-lap"]
        return next((driver_data["lap-info"]["current-lap"] for driver_data in self.m_json_rsp \
                     if driver_data["driver-info"]["is-player"]), None)

    def getPositionHistoryJSON(self) -> List[Dict[str, Any]]:
        """Get position history.

        Returns:
            List[Dict[str, Any]]: The position history JSON
        """

        if not self.m_json_rsp:
            return []

        # Use original list since this request comes only once in a bluemoon
        return [data_per_driver.getPositionHistoryJSON() \
                for data_per_driver in _session_state_ref.m_driver_data \
                    if data_per_driver and data_per_driver.is_valid]

    def getTyreStintHistoryJSON(self) -> List[Dict[str, Any]]:
        """Get tyre stint history.

        Returns:
            List[Dict[str, Any]]: The tyre stint history JSON
        """

        if not self.m_json_rsp:
            return []

        ret = [data_per_driver.getTyreStintHistoryJSON() \
                for data_per_driver in _session_state_ref.m_driver_data \
                if data_per_driver and data_per_driver.is_valid]
        return sorted(ret, key=lambda x: x["position"])

    def getTyreStintHistoryJSONv2(self) -> List[Dict[str, Any]]:
        """Get tyre stint history.

        Returns:
            List[Dict[str, Any]]: The tyre stint history JSON
        """

        if not self.m_json_rsp:
            return []

        ret = [data_per_driver.getTyreStintHistoryJSONv2() \
                for data_per_driver in _session_state_ref.m_driver_data \
                if data_per_driver and data_per_driver.is_valid]
        return sorted(ret, key=lambda x: x["position"])

    def getBestSectorTimes(self) -> List[Optional[int]]:
        """Get best sector times.

        Returns:
            List[Optional[int]]: The best sector times. Can be None
        """
        return [self.m_fastest_s1_ms, self.m_fastest_s2_ms, self.m_fastest_s3_ms]

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
        return drs_activated or drs_available or (drs_distance > 0)

    def __initDriverList(self) -> None:
        """Initialise the fields
        """

        # Player index can never be none, since the player always an index, even if a spectator (for Lobby packet)
        if not _session_state_ref.is_data_available:
            return

        # Update the list data
        self.m_next_pit_stop_window = _session_state_ref.m_ideal_pit_stop_window
        if _session_state_ref.m_fastest_index is not None:
            self.m_fastest_lap = _session_state_ref.m_driver_data[
                                    _session_state_ref.m_fastest_index].m_lap_info.m_best_lap_ms
            self.m_fastest_lap_driver = _session_state_ref.m_driver_data[
                                        _session_state_ref.m_fastest_index].m_driver_info.name
            self.m_fastest_lap_tyre = _session_state_ref.m_driver_data[
                                        _session_state_ref.m_fastest_index].m_lap_info.m_best_lap_tyre

        self.m_fastest_s1_ms = _session_state_ref.m_fastest_s1_ms
        self.m_fastest_s2_ms = _session_state_ref.m_fastest_s2_ms
        self.m_fastest_s3_ms = _session_state_ref.m_fastest_s3_ms

        # for each driver:
        for index, driver_data in enumerate(_session_state_ref.m_driver_data):
            if (index, driver_data) == (None, None):
                return
            if not driver_data.is_valid:
                continue
            if not 1 <= driver_data.m_driver_info.position <= _session_state_ref.m_num_active_cars:
                continue
            self.m_json_rsp.append(self._getDriverJSON(index,driver_data))
        self.m_json_rsp.sort(key=lambda obj: obj["driver-info"]["position"])


    def __initTTDict(self) -> None:
        """Initialise the fields
        """

        # Player index can never be none, since the player always an index, even if a spectator (for Lobby packet)
        player_index = _session_state_ref.m_player_index
        if (player_index is None) or (_session_state_ref.m_num_active_cars is None):
            return

        # Player object must be found in TT mode
        player_obj = _session_state_ref.m_driver_data[player_index]
        if not player_obj:
            _logger.debug("Player not found in TT mode")
            return

        # Init the TT packet copy
        self.m_time_trial_packet = _session_state_ref.m_time_trial_packet

        # Insert top speed into the lap-history-data records
        if player_obj.m_packet_copies.m_packet_session_history:
            session_history = player_obj.m_packet_copies.m_packet_session_history.toJSON()
            for index, lap_data in enumerate(session_history["lap-history-data"]):
                lap_data["top-speed-kmph"] = player_obj.m_per_lap_snapshots[index + 1].m_top_speed_kmph \
                    if (index + 1) in player_obj.m_per_lap_snapshots else None
        else:
            session_history = None

        self.m_fastest_lap = player_obj.m_lap_info.m_best_lap_ms
        self.m_fastest_lap_driver = player_obj.m_driver_info.name
        self.m_fastest_lap_tyre = player_obj.m_lap_info.m_best_lap_tyre
        self.m_json_rsp = {
            "current-lap" : player_obj.m_lap_info.m_current_lap,
            "session-history": session_history,
            "tt-data": self.m_time_trial_packet.toJSON() if self.m_time_trial_packet else None,
            "tt-setups" : self._getTTSetupJSON(),
        }

    def _getTTSetupJSON(self) -> Dict[str, Any]:
        """Get the TT setup JSON data.

        Returns:
            Dict[str, Any]: TT setup JSON data.
        """
        if not self.m_time_trial_packet:
            return {
                "personal-best-setup": None,
                "player-session-best-setup": None,
                "rival-session-best-setup": None
            }

        personal_best_setup: Optional[dict[str, Any]] = None
        session_best_setup: Optional[dict[str, Any]] = None
        rival_setup: Optional[dict[str, Any]] = None

        personal_best_idx = self.m_time_trial_packet.m_personalBestDataSet.m_carIdx
        session_best_idx = self.m_time_trial_packet.m_playerSessionBestDataSet.m_carIdx
        rival_idx = self.m_time_trial_packet.m_rivalSessionBestDataSet.m_carIdx

        # Since game doesn't do this, possible bug
        if self.m_time_trial_packet.m_playerSessionBestDataSet.m_lapTimeInMS == self.m_time_trial_packet.m_personalBestDataSet.m_lapTimeInMS:
            personal_best_idx = session_best_idx

        if (driver := self._safeGetDriver(personal_best_idx)) and driver.m_packet_copies.m_packet_car_setup:
            personal_best_setup = driver.m_packet_copies.m_packet_car_setup.toJSON()

        if (driver := self._safeGetDriver(session_best_idx)) and driver.m_packet_copies.m_packet_car_setup:
            session_best_setup = driver.m_packet_copies.m_packet_car_setup.toJSON()

        if (driver := self._safeGetDriver(rival_idx)) and driver.m_packet_copies.m_packet_car_setup:
            rival_setup = driver.m_packet_copies.m_packet_car_setup.toJSON()

        return {
            "personal-best-setup": personal_best_setup,
            "player-session-best-setup": session_best_setup,
            "rival-session-best-setup": rival_setup,
        }

    def _safeGetDriver(self, index: int) -> Optional[DataPerDriver]:
        """Safely get a non-None DataPerDriver from m_driver_data by index."""
        if 0 <= index < len(_session_state_ref.m_driver_data):
            driver = _session_state_ref.m_driver_data[index]
            if driver is not None:
                return driver
        return None

    def _getDriverJSON(self, index: int, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Get the driver JSON data.

        Args:
            index (int): Index of the driver.
            driver_data (DataPerDriver): Driver data.

        Returns:
            Dict[str, Any]: Driver JSON data.
        """
        return {
            "driver-info": self._getDriverInfoJSON(index, driver_data),
            "delta-info": self._getDeltaInfoJSON(driver_data),
            "ers-info": self._getERSInfoJSON(driver_data),
            "lap-info": self._getLapInfoJSON(driver_data),
            "warns-pens-info": self._getWarningsPenaltiesJSON(driver_data),
            "tyre-info": self._getTyreInfoJSON(driver_data),
            "damage-info": self._getDamageInfoJSON(driver_data),
            "fuel-info": driver_data.getFuelStatsJSON(),
        }

    def _getDriverInfoJSON(self, index: int, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Extract driver information section for JSON response.

        Args:
            index (int): Index of the driver.
            driver_data (DataPerDriver): Driver data.

        Returns:
            Dict[str, Any]: Driver information section for JSON response.
        """
        telemetry_restrictions = str(driver_data.m_driver_info.telemetry_restrictions) \
            if driver_data.m_driver_info.telemetry_restrictions is not None else "N/A"

        return {
            "position": _getValueOrDefaultValue(driver_data.m_driver_info.position),
            "grid-position": _getValueOrDefaultValue(driver_data.m_driver_info.grid_position),
            "name": _getValueOrDefaultValue(driver_data.m_driver_info.name),
            "team": _getValueOrDefaultValue(driver_data.m_driver_info.team),
            "is-fastest": _getValueOrDefaultValue(index == _session_state_ref.m_fastest_index),
            "is-player": _getValueOrDefaultValue(driver_data.m_driver_info.is_player),
            "dnf-status": _getValueOrDefaultValue(driver_data.m_driver_info.m_dnf_status_code),
            "index": _getValueOrDefaultValue(index),
            "telemetry-setting": telemetry_restrictions, # Already NULL checked
            "is-pitting": _getValueOrDefaultValue(driver_data.m_lap_info.m_is_pitting, default_value=False),
            "drs": self.__getDRSValue(driver_data.m_car_info.m_drs_activated,
                                    driver_data.m_car_info.m_drs_allowed,
                                    driver_data.m_car_info.m_drs_distance),
            "drs-activated": _getValueOrDefaultValue(driver_data.m_car_info.m_drs_activated, default_value=False),
            "drs-allowed": _getValueOrDefaultValue(driver_data.m_car_info.m_drs_allowed, default_value=False),
            "drs-distance": _getValueOrDefaultValue(driver_data.m_car_info.m_drs_distance, default_value=0),
        }

    def _getDeltaInfoJSON(self, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Extract delta information section for JSON response."""
        return {
            "delta": driver_data.m_lap_info.m_delta_to_car_in_front,
            "delta-to-car-in-front": driver_data.m_lap_info.m_delta_to_car_in_front,
            "delta-to-leader": driver_data.m_lap_info.m_delta_to_leader,
        }

    def _getERSInfoJSON(self, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Extract ERS information section for JSON response."""
        ers_perc = f"{F1Utils.floatToStr(driver_data.m_car_info.m_ers_perc)}%" \
            if driver_data.m_car_info.m_ers_perc is not None else "0.00%"

        car_status = driver_data.m_packet_copies.m_packet_car_status
        ers_mode = str(car_status.m_ersDeployMode) if car_status else None

        return {
            "ers-percent": _getValueOrDefaultValue(ers_perc),
            "ers-percent-float": _getValueOrDefaultValue(driver_data.m_car_info.m_ers_perc),
            "ers-mode": _getValueOrDefaultValue(ers_mode),
            "ers-harvested-by-mguk-this-lap": self._calculateERSPercentage(car_status.m_ersHarvestedThisLapMGUK \
                                                                           if car_status else 0.0),
            "ers-deployed-this-lap": self._calculateERSPercentage(car_status.m_ersDeployedThisLap \
                                                                  if car_status else 0.0),
        }

    def _calculateERSPercentage(self, value: float) -> float:
        """Calculate ERS percentage from raw value."""
        return (value / CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0

    def _getLapInfoJSON(self, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Extract lap information section for JSON response."""
        lap_progress = self._calculateLapProgress(driver_data)

        return {
            "current-lap": driver_data.m_lap_info.m_current_lap,
            "last-lap": self._getLapDetailsSubsection(driver_data, for_best_lap=False),
            "best-lap": self._getLapDetailsSubsection(driver_data, for_best_lap=True),
            "lap-progress": lap_progress,
            "speed-trap-record-kmph": self._getSpeedTrapRecord(driver_data),
            "top-speed-kmph": driver_data.m_lap_info.m_top_speed_kmph_this_lap,
        }

    def _calculateLapProgress(self, driver_data: DataPerDriver) -> Optional[float]:
        """Calculate lap progress percentage."""
        lap_data = driver_data.m_packet_copies.m_packet_lap_data
        if not lap_data or not self.m_track_length:
            return None

        return (lap_data.m_lapDistance / self.m_track_length) * 100.0

    def _getSpeedTrapRecord(self, driver_data: DataPerDriver) -> Optional[float]:
        """Get speed trap record if available."""
        lap_data = driver_data.m_packet_copies.m_packet_lap_data
        return lap_data.m_speedTrapFastestSpeed if lap_data else None

    def _getLapDetailsSubsection(self, driver_data: DataPerDriver, for_best_lap: bool) -> Dict[str, Any]:
        """Create lap details subsection for last or best lap."""
        if for_best_lap:
            lap_obj = driver_data.m_lap_info.m_best_lap_obj
            lap_time_ms = driver_data.m_lap_info.m_best_lap_ms
        else:
            lap_obj = driver_data.m_lap_info.m_last_lap_obj
            lap_time_ms = driver_data.m_lap_info.m_last_lap_ms

        sector_status = driver_data.getSectorStatus(
            self.m_fastest_s1_ms, self.m_fastest_s2_ms, self.m_fastest_s3_ms,
            for_best_lap=for_best_lap
        )

        # Extract sector times, handling None case
        s1_time = lap_obj.m_sector1TimeInMS if lap_obj else None
        s2_time = lap_obj.m_sector2TimeInMS if lap_obj else None
        s3_time = lap_obj.m_sector3TimeInMS if lap_obj else None

        return {
            "lap-time-ms": lap_time_ms,
            "lap-time-ms-player": 0,
            "s1-time-ms-player": 0,
            "s2-time-ms-player": 0,
            "s3-time-ms-player": 0,
            "sector-status": sector_status,
            "s1-time-ms": s1_time,
            "s2-time-ms": s2_time,
            "s3-time-ms": s3_time,
        }

    def _getWarningsPenaltiesJSON(self, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Extract warnings and penalties section for JSON response."""
        if not (lap_data := driver_data.m_packet_copies.m_packet_lap_data):
            return {
                "corner-cutting-warnings": None,
                "time-penalties": None,
                "num-dt": None,
                "num-sg": None,
            }

        return {
            "corner-cutting-warnings": _getValueOrDefaultValue(lap_data.m_cornerCuttingWarnings),
            "time-penalties": _getValueOrDefaultValue(lap_data.m_penalties),
            "num-dt": _getValueOrDefaultValue(lap_data.m_numUnservedDriveThroughPens),
            "num-sg": _getValueOrDefaultValue(lap_data.m_numUnservedStopGoPens),
        }

    def _getTyreInfoJSON(self, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Extract tyre information section for JSON response."""
        return {
            "wear-prediction": driver_data.getFullTyreWearPredictions(self.m_next_pit_stop_window),
            "current-wear": driver_data.getCurrentTyreWearJSON(),
            "tyre-age": _getValueOrDefaultValue(driver_data.m_tyre_info.tyre_age),
            "tyre-life-remaining": _getValueOrDefaultValue(driver_data.m_tyre_info.tyre_life_remaining_laps),
            "visual-tyre-compound": str(_getValueOrDefaultValue(driver_data.m_tyre_info.tyre_vis_compound, default_value="")),
            "actual-tyre-compound": str(_getValueOrDefaultValue(driver_data.m_tyre_info.tyre_act_compound, default_value="")),
            "num-pitstops": _getValueOrDefaultValue(driver_data.m_driver_info.m_num_pitstops),
        }

    def _getDamageInfoJSON(self, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Extract damage information section for JSON response."""
        return {
            "fl-wing-damage": driver_data.m_car_info.m_fl_wing_damage,
            "fr-wing-damage": driver_data.m_car_info.m_fr_wing_damage,
            "rear-wing-damage": driver_data.m_car_info.m_rear_wing_damage,
        }

class LapTimeInfo:
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

class LapTimeHistory:
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
