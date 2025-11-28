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

from apps.backend.state_mgmt_layer.data_per_driver import DataPerDriver
from apps.backend.state_mgmt_layer.session_state import SessionState
from lib.f1_types import CarStatusData, F1Utils, VisualTyreCompound

from ...base import BaseAPI

# ------------------------- CLASSES ------------------------------------------------------------------------------------

class DriversListRsp(BaseAPI):
    """
    Drivers list response class.
    """

    def __init__(self,
                 logger: logging.Logger,
                 session_state: SessionState,
                 is_spectator_mode: bool,
                 track_length: Optional[int] = None,
                 is_tt_mode: bool = False
                 ):
        """Get the drivers list and prepare the rsp fields

        Args:
            logger (logging.Logger): Logger
            session_state_ref (TelState.SessionState): Reference to the session state
            is_spectator_mode (bool): Whether the player is in spectator mode
            track_length (Optional[int], optional): The track length. Defaults to None.
            is_tt_mode (bool, optional): Whether the player is in time trial mode
        """

        self.m_logger: logging.Logger = logger
        self.m_session_state: SessionState = session_state
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
                for data_per_driver in self.m_session_state.m_driver_data \
                    if data_per_driver and data_per_driver.is_valid]

    def getSpeedTrapRecordsJSON(self) -> List[Dict[str, Any]]:
        """Get speed trap records.

        Returns:
            List[Dict[str, Any]]: The speed trap records JSON
        """

        if not self.m_session_state.m_session_info or self.m_session_state.m_session_info.m_packet_format < 2024:
            return []
        if not self.m_json_rsp:
            return []

        # Use original list since this request comes only once in a bluemoon
        ret = [data_per_driver.getSpeedTrapRecordJSON() \
                for data_per_driver in self.m_session_state.m_driver_data \
                if data_per_driver and data_per_driver.is_valid]
        return sorted(ret, key=lambda x: x["speed-trap-record-kmph"], reverse=True)

    def getTyreStintHistoryJSON(self) -> List[Dict[str, Any]]:
        """Get tyre stint history.

        Returns:
            List[Dict[str, Any]]: The tyre stint history JSON
        """

        if not self.m_json_rsp:
            return []

        ret = [data_per_driver.getTyreStintHistoryJSON() \
                for data_per_driver in self.m_session_state.m_driver_data \
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
                for data_per_driver in self.m_session_state.m_driver_data \
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
        if not self.m_session_state.is_data_available:
            return

        # Update the list data
        self.m_next_pit_stop_window = self.m_session_state.m_ideal_pit_stop_window
        if self.m_session_state.m_fastest_index is not None:
            self.m_fastest_lap = self.m_session_state.m_driver_data[
                                    self.m_session_state.m_fastest_index].m_lap_info.m_best_lap_ms
            self.m_fastest_lap_driver = self.m_session_state.m_driver_data[
                                        self.m_session_state.m_fastest_index].m_driver_info.name
            self.m_fastest_lap_tyre = self.m_session_state.m_driver_data[
                                        self.m_session_state.m_fastest_index].m_lap_info.m_best_lap_tyre

        self.m_fastest_s1_ms = self.m_session_state.m_fastest_s1_ms
        self.m_fastest_s2_ms = self.m_session_state.m_fastest_s2_ms
        self.m_fastest_s3_ms = self.m_session_state.m_fastest_s3_ms

        # for each driver:
        for index, driver_data in enumerate(self.m_session_state.m_driver_data):
            if (index, driver_data) == (None, None):
                return
            if not driver_data.is_valid:
                continue
            if not 1 <= driver_data.m_driver_info.position <= self.m_session_state.m_num_active_cars:
                continue
            self.m_json_rsp.append(self._getDriverJSON(index,driver_data))

    def __initTTDict(self) -> None:
        """Initialise the fields
        """

        # Player index can never be none, since the player always an index, even if a spectator (for Lobby packet)
        player_index = self.m_session_state.m_player_index
        if (player_index is None) or (self.m_session_state.m_num_active_cars is None):
            return

        # Player object must be found in TT mode
        player_obj = self.m_session_state.m_driver_data[player_index]
        if not player_obj:
            self.m_logger.debug("Player not found in TT mode")
            return

        # Init the TT packet copy
        self.m_time_trial_packet = self.m_session_state.m_time_trial_packet
        self.m_irl_pole_lap = self.m_session_state.m_session_info.m_most_recent_pole_lap

        # Insert top speed into the lap-history-data records
        if player_obj.m_packet_copies.m_packet_session_history:
            session_history = player_obj.m_packet_copies.m_packet_session_history.toJSON()
            for index, lap_data in enumerate(session_history["lap-history-data"]):
                lap_data["top-speed-kmph"] = player_obj.m_per_lap_snapshots[index + 1].m_top_speed_kmph \
                    if (index + 1) in player_obj.m_per_lap_snapshots else None
        else:
            session_history = None

        if player_obj.m_lap_info.m_best_lap_ms:
            self.m_fastest_lap = player_obj.m_lap_info.m_best_lap_ms
            self.m_fastest_lap_tyre = VisualTyreCompound.SOFT # Always soft in TT
        elif self.m_time_trial_packet:
            self.m_fastest_lap = self.m_time_trial_packet.m_playerSessionBestDataSet.m_lapTimeInMS
            self.m_fastest_lap_tyre = VisualTyreCompound.SOFT
        else:
            self.m_fastest_lap = None
            self.m_fastest_lap_tyre = None
        self.m_fastest_lap_driver = player_obj.m_driver_info.name
        self.m_json_rsp = {
            "current-lap" : player_obj.m_lap_info.m_current_lap,
            "session-history": session_history,
            "tt-data": self.m_time_trial_packet.toJSON() if self.m_time_trial_packet else None,
            "tt-setups" : self._getTTSetupJSON(),
            "irl-pole-lap": self.m_irl_pole_lap.toJSON() if self.m_irl_pole_lap else None
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

        # The game always references personal best with index 2 and session best with index 0
        # If the personal best is the same as the session best, then we can use the session best index
        # since the personal best index may contain some unrelated car setup
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
        if 0 <= index < len(self.m_session_state.m_driver_data):
            driver = self.m_session_state.m_driver_data[index]
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
        telemetry_restrictions = str(driver_data.m_driver_info.telemetry_setting) \
            if driver_data.m_driver_info.telemetry_setting is not None else "N/A"

        return {
            "position": self._getValueOrDefaultValue(driver_data.m_driver_info.position),
            "grid-position": self._getValueOrDefaultValue(driver_data.m_driver_info.grid_position),
            "name": self._getValueOrDefaultValue(driver_data.m_driver_info.name),
            "team": self._getValueOrDefaultValue(driver_data.m_driver_info.team),
            "is-fastest": self._getValueOrDefaultValue(index == self.m_session_state.m_fastest_index),
            "is-player": self._getValueOrDefaultValue(driver_data.m_driver_info.is_player),
            "dnf-status": self._getValueOrDefaultValue(driver_data.m_driver_info.m_dnf_status_code),
            "index": self._getValueOrDefaultValue(index),
            "telemetry-setting": telemetry_restrictions, # Already NULL checked
            "is-pitting": self._getValueOrDefaultValue(driver_data.m_lap_info.m_is_pitting, default_value=False),
            "drs": self.__getDRSValue(driver_data.m_car_info.m_drs_activated,
                                    driver_data.m_car_info.m_drs_allowed,
                                    driver_data.m_car_info.m_drs_distance),
            "drs-activated": self._getValueOrDefaultValue(driver_data.m_car_info.m_drs_activated, default_value=False),
            "drs-allowed": self._getValueOrDefaultValue(driver_data.m_car_info.m_drs_allowed, default_value=False),
            "drs-distance": self._getValueOrDefaultValue(driver_data.m_car_info.m_drs_distance, default_value=0),
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
        ers_perc = f"{F1Utils.formatFloat(driver_data.m_car_info.m_ers_perc)}%" \
            if driver_data.m_car_info.m_ers_perc is not None else "0.00%"

        car_status = driver_data.m_packet_copies.m_packet_car_status
        ers_mode = str(car_status.m_ersDeployMode) if car_status else None

        return {
            "ers-percent": self._getValueOrDefaultValue(ers_perc),
            "ers-percent-float": self._getValueOrDefaultValue(driver_data.m_car_info.m_ers_perc),
            "ers-mode": self._getValueOrDefaultValue(ers_mode),
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
            "curr-lap": self._getCurrLapSubsection(driver_data),
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
            "sector-status": sector_status,
            "s1-time-ms": s1_time,
            "s2-time-ms": s2_time,
            "s3-time-ms": s3_time,
        }

    def _getCurrLapSubsection(self, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Create current lap subsection."""
        if delta_obj := driver_data.m_delta_mgr.get_delta():
            delta = delta_obj.delta_ms
        else:
            delta = None
        if driver_data.m_packet_copies.m_packet_lap_data:
            sc_delta = driver_data.m_packet_copies.m_packet_lap_data.m_safetyCarDelta
        else:
            sc_delta = None
        return {
            "lap-time-ms": driver_data.m_lap_info.m_curr_lap_ms,
            "s1-time-ms": driver_data.m_lap_info.m_curr_lap_s1_ms,
            "s2-time-ms": driver_data.m_lap_info.m_curr_lap_s2_ms,
            "s3-time-ms": driver_data.m_lap_info.m_curr_lap_s3_ms,
            "sector" : str(driver_data.m_lap_info.m_curr_sector),
            "driver-status" : str(driver_data.m_lap_info.m_curr_status),
            "sector-status" : driver_data.getCurrLapSectorStatus(self.m_fastest_s1_ms, self.m_fastest_s2_ms),
            "lap-num" : driver_data.m_lap_info.m_current_lap,
            "delta-ms" : delta,
            "delta-sc-sec": sc_delta,
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
            "corner-cutting-warnings": self._getValueOrDefaultValue(lap_data.m_cornerCuttingWarnings),
            "time-penalties": self._getValueOrDefaultValue(lap_data.m_penalties),
            "num-dt": self._getValueOrDefaultValue(lap_data.m_numUnservedDriveThroughPens),
            "num-sg": self._getValueOrDefaultValue(lap_data.m_numUnservedStopGoPens),
        }

    def _getTyreInfoJSON(self, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Extract tyre information section for JSON response."""
        return {
            "wear-prediction": driver_data.getFullTyreWearPredictions(self.m_next_pit_stop_window),
            "current-wear": driver_data.getCurrentTyreWearJSON(),
            "tyre-age": self._getValueOrDefaultValue(driver_data.m_tyre_info.tyre_age),
            "tyre-life-remaining": self._getValueOrDefaultValue(driver_data.m_tyre_info.tyre_life_remaining_laps),
            "visual-tyre-compound": str(self._getValueOrDefaultValue(driver_data.m_tyre_info.tyre_vis_compound, default_value="")),
            "actual-tyre-compound": str(self._getValueOrDefaultValue(driver_data.m_tyre_info.tyre_act_compound, default_value="")),
            "num-pitstops": self._getValueOrDefaultValue(driver_data.m_driver_info.m_num_pitstops),
        }

    def _getDamageInfoJSON(self, driver_data: DataPerDriver) -> Dict[str, Any]:
        """Extract damage information section for JSON response."""
        return {
            "fl-wing-damage": driver_data.m_car_info.m_fl_wing_damage,
            "fr-wing-damage": driver_data.m_car_info.m_fr_wing_damage,
            "rear-wing-damage": driver_data.m_car_info.m_rear_wing_damage,
        }
