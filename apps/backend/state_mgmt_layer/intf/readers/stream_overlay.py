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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import Any, Dict, List, Optional

from apps.backend.state_mgmt_layer.data_per_driver import DataPerDriver
from apps.backend.state_mgmt_layer.session_state import SessionState
from lib.f1_types import CarStatusData

from ..base import BaseAPI
from .helpers import LapTimeHistory

# ------------------------- API - CLASSES ------------------------------------------------------------------------------

class StreamOverlayData(BaseAPI):
    """
    Player telemetry overlay update class.
    """

    def __init__(self, session_state: SessionState) -> None:
        """Initialse the member variables by fetching necessary data from the data store

        Args:
            session_state (SessionState): Handle to the session state data structure
        """

        self.m_track_temp               = session_state.m_session_info.m_track_temp
        self.m_air_temp                 = session_state.m_session_info.m_air_temp
        self.m_weather_forecast_samples = session_state.m_session_info.m_weather_forecast_samples
        if self.m_weather_forecast_samples is None:
            self.m_weather_forecast_samples = []
        self.m_circuit                  = session_state.m_session_info.m_track
        self.m_total_laps               = session_state.m_session_info.m_total_laps
        self.m_game_year                = session_state.m_session_info.m_game_year
        self.m_packet_format            = session_state.m_session_info.m_packet_format
        self.m_formula_type             = session_state.m_session_info.m_formula
        self.m_session_type             = session_state.m_session_info.m_session_type
        self.m_pit_speed_limit          = session_state.m_session_info.m_pit_speed_limit

        self.m_next_pit_window          = session_state.m_ideal_pit_stop_window
        self.m_fastest_lap_ms           = \
            session_state.m_driver_data[session_state.m_fastest_index].m_lap_info.m_best_lap_ms if \
                session_state.m_fastest_index is not None else None
        self.m_fastest_s1_ms            = session_state.m_fastest_s1_ms
        self.m_fastest_s2_ms            = session_state.m_fastest_s2_ms
        self.m_fastest_s3_ms            = session_state.m_fastest_s3_ms
        player_index = session_state.m_session_info.m_spectator_car_index \
                        if session_state.m_session_info.m_is_spectating \
                        else session_state.m_player_index
        player_data = (
            session_state.m_driver_data[player_index]
            if player_index is not None and 0 <= player_index < len(session_state.m_driver_data)
            else None
        )
        player_position = player_data.m_driver_info.position if player_data else None
        prev_data = session_state.getDriverInfoByPosition(player_position - 1) if player_position else None
        next_data = session_state.getDriverInfoByPosition(player_position + 1) if player_position else None

        self.__initCarTelemetry(player_data)
        self.__initLapTimes(player_data)
        self.__initTyreSets(player_data)
        self.__initPenalties(player_data)
        self.__initGForce(player_data)
        self.__initPaceComparison(player_data, prev_data, next_data)
        self.__initMotion(session_state.m_driver_data)

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

    def __initTyreSets(self, player_data: Optional[DataPerDriver]) -> None:
        """Prepares the player's tyre sets data.

        Args:
            player_data (Optional[TelData.DataPerDriver]): The player's DataPerDriver object
        """

        if player_data:
            self.m_tyre_sets_pkt = player_data.m_packet_copies.m_packet_tyre_sets
        else:
            self.m_tyre_sets_pkt = None

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

    def __initMotion(self, drivers_data: List[DataPerDriver]) -> None:
        """Prepares and updates the motion/position data of all cars"""
        self.m_motion_json = [
            {
                "name": driver.m_driver_info.name,
                "team": str(driver.m_driver_info.team),
                "track-position": driver.m_driver_info.position,
                "index": driver.m_index,
                "motion": (
                    driver.m_packet_copies.m_packet_motion.toJSON()
                        if driver.m_packet_copies.m_packet_motion
                        else None
                ),
                "ers" : {
                    "ers-percent" : self._getValueOrDefaultValue(driver.m_car_info.m_ers_perc),
                    "ers-mode" : self._getValueOrDefaultValue(str(driver.m_packet_copies.m_packet_car_status.m_ersDeployMode)
                                                    if driver.m_packet_copies.m_packet_car_status else None),
                    "ers-harvested-by-mguk-this-lap" : (((driver.m_packet_copies.m_packet_car_status.m_ersHarvestedThisLapMGUK
                                                    if driver.m_packet_copies.m_packet_car_status else 0.0) /
                                                        CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0),
                    "ers-deployed-this-lap" : ((driver.m_packet_copies.m_packet_car_status.m_ersDeployedThisLap
                                            if driver.m_packet_copies.m_packet_car_status else 0.0) /
                                                CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0
                }
            }
            for driver in drivers_data
            if driver and driver.is_valid
        ]

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
            "ers-percent" : self._getValueOrDefaultValue(driver_obj.m_car_info.m_ers_perc),
            "ers-mode" : self._getValueOrDefaultValue(str(driver_obj.m_packet_copies.m_packet_car_status.m_ersDeployMode)
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
            "f1-packet-format" : self.m_packet_format,
            "event-type" : str(self.m_session_type),
            "formula-type" : str(self.m_formula_type),
            "show-sample-data-at-start": stream_overlay_start_sample_data,
            "circuit-enum-name" : self.m_circuit.name if self.m_circuit else None,
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
            "tyre-sets" : self.m_tyre_sets_pkt.toJSON() if self.m_tyre_sets_pkt else None,
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
            "motion" : self.m_motion_json,
        }
