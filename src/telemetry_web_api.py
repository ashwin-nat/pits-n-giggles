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

from src.png_logger import getLogger
from typing import Dict, Any, Optional, List
from lib.f1_types import F1Utils, LapHistoryData, CarStatusData, VisualTyreCompound
import lib.race_analyzer as RaceAnalyzer
from lib.tyre_wear_extrapolator import TyreWearPerLap
import src.telemetry_data as TelData
from src.telemetry_handler import getOvertakeJSON, GetOvertakesStatus
from src.data_per_driver import TyreSetInfo

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

png_logger = getLogger()

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

class RaceInfoUpdate:
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
            "live-data" : True,
            "f1-game-year" : _getValueOrDefaultValue(self.m_globals.m_game_year, None),
            "circuit": _getValueOrDefaultValue(self.m_globals.m_circuit),
            "track-temperature": _getValueOrDefaultValue(self.m_globals.m_track_temp, default_value=0),
            "air-temperature": _getValueOrDefaultValue(self.m_globals.m_air_temp, default_value=0),
            "event-type": _getValueOrDefaultValue(self.m_globals.m_event_type),
            "session-time-left" : _getValueOrDefaultValue(self.m_globals.m_packet_session.m_sessionTimeLeft \
                                                          if self.m_globals.m_packet_session else None, 0),
            "total-laps": _getValueOrDefaultValue(self.m_globals.m_total_laps, default_value=None),
            "current-lap": _getValueOrDefaultValue(self.m_curr_lap, default_value=None),
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
            "session-type"  : _getValueOrDefaultValue(self.m_globals.m_event_type),
            "session-duration-so-far" : _getValueOrDefaultValue(
                (self.m_globals.m_packet_session.m_sessionDuration - self.m_globals.m_packet_session.m_sessionTimeLeft) \
                                                          if self.m_globals.m_packet_session else None, 0),
            "num-sc" : _getValueOrDefaultValue(self.m_globals.m_packet_session.m_numSafetyCarPeriods \
                                                          if self.m_globals.m_packet_session else None, 0),
            "num-vsc" : _getValueOrDefaultValue(self.m_globals.m_packet_session.m_numVirtualSafetyCarPeriods \
                                                          if self.m_globals.m_packet_session else None, 0),
            "num-red-flags" : _getValueOrDefaultValue(self.m_globals.m_packet_session.m_numRedFlagPeriods \
                                                          if self.m_globals.m_packet_session else None, 0),
            "player-pit-window" : _getValueOrDefaultValue(self.m_driver_list_rsp.m_next_pit_stop_window, None),
        }

        if self.m_globals.m_event_type == "Time Trial":
            final_json["tt-data"] = self.m_driver_list_rsp.getTtTableJSON()
        else:
            final_json["table-entries"] = self.m_driver_list_rsp.toRaceTableJSON(self.m_globals.m_event_type)
            self._updatePlayerLapTimes(final_json["table-entries"])

        final_json["fastest-lap-overall"] = _getValueOrDefaultValue(
            self.m_driver_list_rsp.m_fastest_lap, default_value=0)
        final_json["fastest-lap-overall-driver"] = _getValueOrDefaultValue(
            self.m_driver_list_rsp.m_fastest_lap_driver)
        final_json["fastest-lap-overall-tyre"] = str(self.m_driver_list_rsp.m_fastest_lap_tyre) \
            if self.m_driver_list_rsp.m_fastest_lap_tyre else None
        return final_json

    def _updatePlayerLapTimes(self,table_entries_json: List[Dict[str, Any]]) -> None:
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
            player_last_lap = player_entry["lap-info"]["last-lap"]
            player_best_lap = player_entry["lap-info"]["best-lap"]
            for table_entry in table_entries_json:
                # Update last lap time for player in every object
                if table_entry["driver-info"]["index"] != player_entry["driver-info"]["index"]:
                    # Current entry is NOT the player entry
                    table_entry["lap-info"]["last-lap"]["lap-time-ms-player"] = player_last_lap["lap-time-ms"]
                    table_entry["lap-info"]["last-lap"]["s1-time-ms-player"] = player_last_lap["s1-time-ms"]
                    table_entry["lap-info"]["last-lap"]["s2-time-ms-player"] = player_last_lap["s2-time-ms"]
                    table_entry["lap-info"]["last-lap"]["s3-time-ms-player"] = player_last_lap["s3-time-ms"]

                    table_entry["lap-info"]["best-lap"]["lap-time-ms-player"] = player_best_lap["lap-time-ms"]
                    table_entry["lap-info"]["best-lap"]["s1-time-ms-player"] = player_best_lap["s1-time-ms"]
                    table_entry["lap-info"]["best-lap"]["s2-time-ms-player"] = player_best_lap["s2-time-ms"]
                    table_entry["lap-info"]["best-lap"]["s3-time-ms-player"] = player_best_lap["s3-time-ms"]
                else:
                    # Current entry is the player entry
                    table_entry["lap-info"]["last-lap"]["lap-time-ms-player"] = table_entry["lap-info"]["last-lap"]["lap-time-ms"]
                    table_entry["lap-info"]["last-lap"]["s1-time-ms-player"] = table_entry["lap-info"]["last-lap"]["s1-time-ms"]
                    table_entry["lap-info"]["last-lap"]["s2-time-ms-player"] = table_entry["lap-info"]["last-lap"]["s2-time-ms"]
                    table_entry["lap-info"]["last-lap"]["s3-time-ms-player"] = table_entry["lap-info"]["last-lap"]["s3-time-ms"]

                    table_entry["lap-info"]["best-lap"]["lap-time-ms-player"] = table_entry["lap-info"]["best-lap"]["lap-time-ms"]
                    table_entry["lap-info"]["best-lap"]["s1-time-ms-player"] = table_entry["lap-info"]["best-lap"]["s1-time-ms"]
                    table_entry["lap-info"]["best-lap"]["s2-time-ms-player"] = table_entry["lap-info"]["best-lap"]["s2-time-ms"]
                    table_entry["lap-info"]["best-lap"]["s3-time-ms-player"] = table_entry["lap-info"]["best-lap"]["s3-time-ms"]

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
                png_logger.debug('Failed to get fastest times JSON')
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
            drivers_list_rsp = DriversListRsp(is_spectator_mode=True)
            self.m_rsp["position-history"] = drivers_list_rsp.getPositionHistoryJSON()
            self.m_rsp["tyre-stint-history"] = drivers_list_rsp.getTyreStintHistoryJSON()

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
            self.m_event_type               = TelData._globals.m_event_type
            self.m_pit_speed_limit          = TelData._globals.m_pit_speed_limit

        with TelData._driver_data_lock.gen_rlock():
            self.m_next_pit_window          = TelData._driver_data.m_ideal_pit_stop_window
            self.m_fastest_lap_ms           = \
                TelData._driver_data.m_driver_data[TelData._driver_data.m_fastest_index].m_lap_info.m_best_lap_ms if \
                    TelData._driver_data.m_fastest_index is not None else None
            self.m_fastest_s1_ms            = TelData._driver_data.m_fastest_s1_ms
            self.m_fastest_s2_ms            = TelData._driver_data.m_fastest_s2_ms
            self.m_fastest_s3_ms            = TelData._driver_data.m_fastest_s3_ms
            player_index = TelData._globals.m_spectator_car_index if TelData._globals.m_is_spectating \
                            else TelData._driver_data.m_player_index
            player_data = TelData._driver_data.m_driver_data[player_index] \
                            if player_index in TelData._driver_data.m_driver_data else None
            player_position = player_data.m_driver_info.position if player_data else None
            prev_data = TelData._driver_data.getDriverInfoByPosition(player_position - 1) if player_position else None
            next_data = TelData._driver_data.getDriverInfoByPosition(player_position + 1) if player_position else None

        self.__initCarTelemetry(player_data)
        self.__initLapTimes(player_data)
        self.__initTyreWear(player_data)
        self.__initPenalties(player_data)
        self.__initGForce(player_data)
        self.__initPaceComparison(player_data, prev_data, next_data)

    def __initCarTelemetry(self, player_data: Optional[TelData.DataPerDriver]) -> None:
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

    def __initLapTimes(self, player_data: Optional[TelData.DataPerDriver]) -> None:
        """Prepares the player's lap history data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        self.m_curr_lap: Optional[int] = player_data.m_current_lap if player_data else None
        self.m_lap_time_history: LapTimeHistory = LapTimeHistory(
            player_data, self.m_fastest_lap_ms, self.m_fastest_s1_ms, self.m_fastest_s2_ms, self.m_fastest_s3_ms)
        self.m_speed_trap_record: Optional[float] = player_data.m_packet_copies.m_packet_lap_data.m_speedTrapFastestSpeed \
            if player_data and player_data.m_packet_copies.m_packet_lap_data else None

    def __initTyreWear(self, player_data: Optional[TelData.DataPerDriver]) -> None:
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

    def __initPenalties(self, player_data: Optional[TelData.DataPerDriver]) -> None:
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

    def __initGForce(self, player_data: Optional[TelData.DataPerDriver]) -> None:
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
                             player_data: TelData.DataPerDriver,
                             prev_data: Optional[TelData.DataPerDriver],
                             next_data: Optional[TelData.DataPerDriver]) -> None:
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
                                        driver_obj: Optional[TelData.DataPerDriver]) -> None:
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
            "event-type" : self.m_event_type,
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
                "circuit" : self.m_circuit,
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
        self.m_fastest_lap_tyre: Optional[VisualTyreCompound] = None
        self.m_next_pit_stop_window: Optional[int] = None
        self.m_fastest_s1_ms: Optional[int] = None
        self.m_fastest_s2_ms: Optional[int] = None
        self.m_fastest_s3_ms: Optional[int] = None
        self.__initDriverList()
        self.__updateDriverList()

    def toRaceTableJSON(self, session_type: str) -> Dict[str, Any]:
        """Get the race table JSON

        Args:
            session_type (SessionType23 | SessionType24): The session type

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return  [
            {
                "driver-info" : {
                    "position": _getValueOrDefaultValue(data_per_driver.m_driver_info.position),
                    "name": _getValueOrDefaultValue(data_per_driver.m_driver_info.name),
                    "team": _getValueOrDefaultValue(data_per_driver.m_driver_info.team),
                    "is-fastest": _getValueOrDefaultValue(data_per_driver.m_is_fastest),
                    "is-player": _getValueOrDefaultValue(data_per_driver.m_driver_info.is_player),
                    "dnf-status" : _getValueOrDefaultValue(data_per_driver.m_driver_info.m_dnf_status_code),
                    "index" : _getValueOrDefaultValue(data_per_driver.m_index),
                    "telemetry-setting" : data_per_driver.m_driver_info.telemetry_restrictions, # Already NULL checked
                    "drs": self.__getDRSValue(data_per_driver.m_car_info.m_drs_activated, data_per_driver.m_car_info.m_drs_allowed,
                                        data_per_driver.m_car_info.m_drs_distance),
                },
                "delta-info" : {
                    "delta": data_per_driver.m_delta_to_car_in_front,
                    "delta-to-car-in-front": data_per_driver.m_delta_to_car_in_front,
                    "delta-to-leader": data_per_driver.m_delta_to_leader,
                },
                "ers-info" : {
                    "ers-percent": _getValueOrDefaultValue(data_per_driver.m_car_info.m_ers_perc),
                    "ers-mode" : _getValueOrDefaultValue(str(data_per_driver.m_packet_copies.m_packet_car_status.m_ersDeployMode)
                                                        if data_per_driver.m_packet_copies.m_packet_car_status else None),
                    "ers-harvested-by-mguk-this-lap" : (((data_per_driver.m_packet_copies.m_packet_car_status.m_ersHarvestedThisLapMGUK
                                                        if data_per_driver.m_packet_copies.m_packet_car_status else 0.0) /
                                                            CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0),
                    "ers-deployed-this-lap" : ((data_per_driver.m_packet_copies.m_packet_car_status.m_ersDeployedThisLap
                                                if data_per_driver.m_packet_copies.m_packet_car_status else 0.0) /
                                                    CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0,
                },
                "lap-info" : {
                    "current-lap" : data_per_driver.m_current_lap,
                    "last-lap" : {
                        "lap-time-ms" : data_per_driver.m_lap_info.m_last_lap_ms,
                        "lap-time-ms-player" : 0,
                        "s1-time-ms-player" : 0,
                        "s2-time-ms-player" : 0,
                        "s3-time-ms-player" : 0,
                        "sector-status" : data_per_driver.getSectorStatus(
                            self.m_fastest_s1_ms, self.m_fastest_s2_ms, self.m_fastest_s3_ms, for_best_lap=False,
                            session_type_str=session_type),
                        "s1-time-ms" : data_per_driver.m_lap_info.m_last_lap_obj.m_sector1TimeInMS \
                            if data_per_driver.m_lap_info.m_last_lap_obj else None,
                        "s2-time-ms" : data_per_driver.m_lap_info.m_last_lap_obj.m_sector2TimeInMS \
                            if data_per_driver.m_lap_info.m_last_lap_obj else None,
                        "s3-time-ms" : data_per_driver.m_lap_info.m_last_lap_obj.m_sector3TimeInMS \
                            if data_per_driver.m_lap_info.m_last_lap_obj else None,
                    },
                    "best-lap" : {
                        "lap-time-ms" : data_per_driver.m_lap_info.m_best_lap_ms,
                        "lap-time-ms-player" : 0,
                        "s1-time-ms-player" : 0,
                        "s2-time-ms-player" : 0,
                        "s3-time-ms-player" : 0,
                        "sector-status" : data_per_driver.getSectorStatus(
                            self.m_fastest_s1_ms, self.m_fastest_s2_ms, self.m_fastest_s3_ms, for_best_lap=True,
                            session_type_str=session_type),
                        "s1-time-ms" : data_per_driver.m_lap_info.m_best_lap_obj.m_sector1TimeInMS \
                            if data_per_driver.m_lap_info.m_best_lap_obj else None,
                        "s2-time-ms" : data_per_driver.m_lap_info.m_best_lap_obj.m_sector2TimeInMS \
                            if data_per_driver.m_lap_info.m_best_lap_obj else None,
                        "s3-time-ms" : data_per_driver.m_lap_info.m_best_lap_obj.m_sector3TimeInMS \
                            if data_per_driver.m_lap_info.m_best_lap_obj else None,
                    },
                    "lap-progress" : data_per_driver.m_lap_progress, # NULL is supported
                    "speed-trap-record-kmph" : data_per_driver.m_packet_copies.m_packet_lap_data.m_speedTrapFastestSpeed if \
                        data_per_driver.m_packet_copies.m_packet_lap_data else None, # NULL is supported
                    "top-speed-kmph" : data_per_driver.m_top_speed_kmph_this_lap,
                },
                "warns-pens-info" : {
                    "corner-cutting-warnings" : _getValueOrDefaultValue(data_per_driver.m_corner_cutting_warnings),
                    "time-penalties" : _getValueOrDefaultValue(data_per_driver.m_time_penalties),
                    "num-dt" : _getValueOrDefaultValue(data_per_driver.m_num_dt),
                    "num-sg" : _getValueOrDefaultValue(data_per_driver.m_num_sg),
                },
                "tyre-info" : {
                    "wear-prediction" : data_per_driver.getFullTyreWearPredictions(self.m_next_pit_stop_window),
                    "current-wear" : data_per_driver.getCurrentTyreWearJSON(),
                    "tyre-age": _getValueOrDefaultValue(data_per_driver.m_tyre_info.tyre_age),
                    "tyre-life-remaining" : _getValueOrDefaultValue(
                        data_per_driver.m_tyre_info.tyre_life_remaining_laps),
                    "visual-tyre-compound": str(_getValueOrDefaultValue(
                        data_per_driver.m_tyre_info.tyre_vis_compound, default_value="")),
                    "actual-tyre-compound": str(_getValueOrDefaultValue(
                        data_per_driver.m_tyre_info.tyre_act_compound, default_value="")),
                    "num-pitstops": _getValueOrDefaultValue(data_per_driver.m_driver_info.m_num_pitstops),
                },
                "damage-info" : {
                    "fl-wing-damage" : data_per_driver.m_car_info.m_fl_wing_damage, # NULL is supported
                    "fr-wing-damage" : data_per_driver.m_car_info.m_fr_wing_damage, # NULL is supported
                    "rear-wing-damage" : data_per_driver.m_car_info.m_rear_wing_damage, # NULL is supported
                },

                "fuel-info" : data_per_driver.getFuelStatsJSON(),
            } for data_per_driver in self.m_final_list
        ]

    def getTtTableJSON(self) -> Dict[str, Any]:
        """Get the Time Trial table JSON.

        Returns:
            Dict[str, Any]: The JSON dump.
        """

        # Player object must be found in TT mode
        player_obj = next(
            (driver for driver in self.m_final_list if driver.m_driver_info.is_player),
            None
        )

        if not player_obj:
            png_logger.debug("Player not found in TT mode")
            return None

        # Insert top speed into the lap-history-data records
        if player_obj.m_packet_copies.m_packet_session_history:
            session_history = player_obj.m_packet_copies.m_packet_session_history.toJSON()
            for index, lap_data in enumerate(session_history["lap-history-data"]):
                lap_data["top-speed-kmph"] = player_obj.m_per_lap_snapshots[index + 1].m_top_speed_kmph \
                    if (index + 1) in player_obj.m_per_lap_snapshots else None
        else:
            session_history = None
        return {
            "session-history": session_history,
            "tt-data": self.m_time_trial_packet.toJSON() if self.m_time_trial_packet else None,
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
        return next((driver_data.m_current_lap for driver_data in self.m_final_list if driver_data.m_driver_info.is_player), None)

    def getPositionHistoryJSON(self) -> List[Dict[str, Any]]:
        """Get position history.

        Returns:
            List[Dict[str, Any]]: The position history JSON
        """

        if not self.m_final_list:
            return []

        return [data_per_driver.getPositionHistoryJSON() for data_per_driver in self.m_final_list]

    def getTyreStintHistoryJSON(self) -> List[Dict[str, Any]]:
        """Get tyre stint history.

        Returns:
            List[Dict[str, Any]]: The tyre stint history JSON
        """

        if not self.m_final_list:
            return []

        return [data_per_driver.getTyreStintHistoryJSON() for data_per_driver in self.m_final_list]

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

        with TelData._driver_data_lock.gen_rlock():
            # Do the bare mimnimum within this block so that we can unlock the mutex ASAP
            # Player index can never be none, since the player always an index, even if a spectator (for Lobby packet)
            if (TelData._driver_data.m_player_index is None) or (TelData._driver_data.m_num_active_cars is None):
                return

            # Update the list data
            self.m_next_pit_stop_window = TelData._driver_data.m_ideal_pit_stop_window
            if TelData._driver_data.m_fastest_index is not None:
                self.m_fastest_lap = TelData._driver_data.m_driver_data[
                                        TelData._driver_data.m_fastest_index].m_lap_info.m_best_lap_ms
                self.m_fastest_lap_driver = TelData._driver_data.m_driver_data[
                                            TelData._driver_data.m_fastest_index].m_driver_info.name
                self.m_fastest_lap_tyre = TelData._driver_data.m_driver_data[
                                            TelData._driver_data.m_fastest_index].m_lap_info.m_best_lap_tyre
            positions = list(range(1, TelData._driver_data.m_num_active_cars + 1))
            for position in positions:
                index, temp_data = TelData._driver_data.getIndexByTrackPosition(position)
                if (index, temp_data) == (None, None):
                    return

                temp_data.m_index = index
                temp_data.m_is_fastest = (index == TelData._driver_data.m_fastest_index)

                # Add this prepped record into the final list
                self.m_final_list.append(temp_data)
            self.m_fastest_s1_ms = TelData._driver_data.m_fastest_s1_ms
            self.m_fastest_s2_ms = TelData._driver_data.m_fastest_s2_ms
            self.m_fastest_s3_ms = TelData._driver_data.m_fastest_s3_ms
            self.m_time_trial_packet = TelData._driver_data.m_time_trial_packet

    def __updateDriverList(self) -> None:
        """Add extra fields to each DataPerDriver object
        """

        for driver_data in self.m_final_list:
            if driver_data.m_car_info.m_ers_perc is not None:
                driver_data.m_car_info.m_ers_perc = f"{F1Utils.floatToStr(driver_data.m_car_info.m_ers_perc)}%"
            if driver_data.m_driver_info.telemetry_restrictions is not None:
                driver_data.m_driver_info.telemetry_restrictions = str(driver_data.m_driver_info.telemetry_restrictions)
            else:
                driver_data.m_driver_info.telemetry_restrictions = "N/A"
            if driver_data.m_packet_copies.m_packet_lap_data:
                driver_data.m_corner_cutting_warnings = driver_data.m_packet_copies.m_packet_lap_data.m_cornerCuttingWarnings
                driver_data.m_time_penalties = driver_data.m_packet_copies.m_packet_lap_data.m_penalties
                driver_data.m_num_dt = driver_data.m_packet_copies.m_packet_lap_data.m_numUnservedDriveThroughPens
                driver_data.m_num_sg = driver_data.m_packet_copies.m_packet_lap_data.m_numUnservedStopGoPens
                if self.m_track_length:
                    driver_data.m_lap_progress = (driver_data.m_packet_copies.m_packet_lap_data.m_lapDistance /
                                                            self.m_track_length) * 100.0
                else:
                    driver_data.m_lap_progress = None
            else:
                driver_data.m_lap_progress = None
                driver_data.m_corner_cutting_warnings = None
                driver_data.m_time_penalties = None
                driver_data.m_num_dt = None
                driver_data.m_num_sg = None

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
        m_tyre_set_info (TyreSetInfo): The tyre set used.
    """
    def __init__(self,
                 lap_history_data: LapHistoryData,
                 tyre_set_info: TyreSetInfo,
                 lap_number: int) -> None:
        """
        Initializes LapTimeInfo with an existing LapHistoryData object, tyre set info and lap number.

        Args:
            lap_history_data (LapHistoryData): An instance of LapHistoryData.
            tyre_set_info (TyreSetInfo): The tyre set info for this lap
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
                 driver_data: Optional[TelData.DataPerDriver] = None,
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
