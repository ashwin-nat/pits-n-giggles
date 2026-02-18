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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import logging
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple

from lib.collisions_analyzer import (CollisionAnalyzer, CollisionAnalyzerMode,
                                     CollisionRecord)
from lib.delta import LapDeltaManager
from lib.f1_types import (CarDamageData, F1Utils, LapData,
                          PacketLapPositionsData, ResultStatus, SafetyCarType,
                          SessionType, TrackID)
from lib.pending_events import DriverPendingEvents, PendingEventsManager
from lib.race_ctrl import (CarDamageRaceControlMessage,
                           DriverPittingRaceCtrlMsg, DriverRaceControlManager,
                           TyreChangeRaceControlMessage, WingChangeRaceCtrlMsg)
from lib.tyre_wear_extrapolator import TyreWearPerLap

from .car_info import CarInfo
from .driver_info import DriverInfo
from .lap_info import LapInfo
from .packet_copies import PacketCopies
from .per_lap_snapshot import PerLapSnapshotEntry
from .tyre_info import TyreInfo, TyreSetHistoryEntry, TyreSetInfo
from .warns_pens_info import WarningPenaltyHistory

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class DataPerDriver:
    """
    Class that models the data stored per race driver.

    Attributes:
        m_index (int): The index of the driver.
        m_logger (logging.Logger): Logger object
        m_driver_info (DriverInfo): Contains driver's position, name, and team.
        m_lap_info (LapInfo): Details regarding the driver's lap times.
        m_tyre_info (TyreInfo): Information about the driver's tire usage and condition.
        m_car_info (CarInfo): Data related to the driver's car performance.
        m_collision_records (List[CollisionRecord]): List of collision records involving the driver.
        m_warning_penalty_history (WarningPenaltyHistory): History of warnings and penalties received by the driver.
        m_packet_copies (PacketCopies): Copies of various data packets related to the driver's performance.
        m_per_lap_snapshots (Dict[int, PerLapSnapshotEntry]): Snapshots of the driver's performance per lap
        m_position_history (List[int]): List of positions of the driver
        m_pending_events_mgr_weird_track (PendingEventsManager): Manager for pending events involving the driver.
        m_pending_events_mgr_normal_track (PendingEventsManager): Manager for pending events involving the driver.
        m_delayed_tyre_change_data (TyreSetHistoryEntry): Delayed tyre change data
        m_race_ctrl (DriverRaceControlManager): Manager for race control messages specific to the driver.
        m_delta_mgr (LapDeltaManager): Lap delta manager
    """

    __slots__ = (
        "m_index",
        "m_logger",
        "m_driver_info",
        "m_lap_info",
        "m_tyre_info",
        "m_car_info",
        "m_collision_records",
        "m_warning_penalty_history",
        "m_packet_copies",
        "m_per_lap_snapshots",
        "m_position_history",
        "m_pending_events_mgr_weird_track",
        "m_pending_events_mgr_normal_track",
        "m_delayed_tyre_change_data",
        "m_race_ctrl",
        "m_delta_mgr",
    )

    CAR_DMG_RACE_CTRL_MSG_INTERESTED_FIELDS = [
        "m_frontLeftWingDamage",
        "m_frontRightWingDamage",
        "m_rearWingDamage",
    ]

    def __repr__(self) -> str:
        """Get the string representation of this object

        Returns:
            str: The string representation
        """

        return  f"DataPerDriver([{self.m_index}]|{self.m_driver_info.position}|" \
                f"{self.m_driver_info.name}|{self.m_driver_info.team})"

    def __str__(self) -> str:
        """Get the string representation of this object

        Returns:
            str: The string representation
        """

        return self.__repr__()

    def __init__(self,
                 index: int,
                 logger: logging.Logger,
                 total_laps: Optional[int]):
        """
        Init the data per driver fields

        Args:
            index (int): The index of the driver.
            logger (logging.Logger): Logger object
            total_laps (Optional[int]): The total number of laps. May be None
        """

        self.m_index = index
        self.m_logger = logger

        self.m_driver_info: DriverInfo = DriverInfo()
        self.m_lap_info: LapInfo = LapInfo()
        self.m_tyre_info: TyreInfo = TyreInfo(total_laps, self.m_logger)

        self.m_car_info: CarInfo = CarInfo(total_laps)

        self.m_collision_records: List[CollisionRecord] = []
        self.m_warning_penalty_history: WarningPenaltyHistory = WarningPenaltyHistory()

        # packet copies
        self.m_packet_copies: PacketCopies = PacketCopies()

        # Per lap snapshot
        self.m_per_lap_snapshots: Dict[int, PerLapSnapshotEntry] = {}

        # Positions history (F1 25+)
        if total_laps:
            self.m_position_history: List[int] = [0] * (total_laps + 1) # +1 for zeroth lap
        else:
            self.m_position_history: List[int] = None

        # Pending events
        self.m_pending_events_mgr_weird_track: PendingEventsManager = PendingEventsManager(
            callback=self._delayedTyreSetsChangeWeird
        )
        self.m_pending_events_mgr_normal_track: PendingEventsManager = PendingEventsManager(
            callback=self._delayedTyreSetsChangeNormal
        )

        # Race control manager
        self.m_race_ctrl: DriverRaceControlManager = DriverRaceControlManager(index)

        # Lap delta
        self.m_delta_mgr: LapDeltaManager = LapDeltaManager()

    @property
    def is_valid(self) -> bool:
        """Check if this DataPerDriver entry is valid. Reuse the same fields as __repr__

        Returns:
            bool: True if valid
        """

        # AI cars that have not been added to the race will have invalid/inactive result status
        if self.m_lap_info.m_result_status in {ResultStatus.INVALID, ResultStatus.INACTIVE}:
            return False

        has_valid_position = (
            self.m_driver_info.position is not None and
            1 <= self.m_driver_info.position <= 22
        )

        # In FP/quali, if someone has finished their laps, retired and disconnected, their participants data will
        # be removed. Hence we need to also look into their lap time history
        history = self.m_packet_copies.m_packet_session_history
        has_driver_info = (
            self.m_driver_info.name or
            self.m_driver_info.team or
            (history and history.is_valid)
        )

        return has_valid_position and bool(has_driver_info)

    def toJSON(self,
               index: Optional[int] = None,
               include_tyre_wear_prediction : Optional[bool] = False,
               selected_pit_stop_lap : Optional[int] = None,
               include_race_ctrl_msgs : Optional[bool] = False,
               driver_info_dict: Optional[Dict[int, dict]] = None) -> Dict[str, Any]:
        """Get a JSON representation of this DataPerDriver object

        Args:
            index (int): The index number. Defaults to None.
            include_tyre_wear_prediction (Optional[bool]): Whether to include the tyre wear prediction
            selected_pit_stop_lap (Optional[int]): The lap number of the selected pit stop
            include_race_ctrl_msgs (Optional[bool]): Whether to include race control messages
            driver_info_dict (Optional[Dict[int, dict]]): Dictionary of driver info

        Returns:
            Dict[str, Any]: The JSON dict
        """
        final_json = {}

        # Add the primary data
        if index is not None:
            final_json["index"] = index
        final_json["is-player"] = self.m_driver_info.is_player
        final_json["driver-name"] = self.m_driver_info.name
        final_json["track-position"] = self.m_driver_info.position
        final_json["team"] = self.m_driver_info.team
        final_json["telemetry-settings"] = str(self.m_driver_info.telemetry_setting)
        final_json["current-lap"] = self.m_lap_info.m_current_lap
        final_json["top-speed-kmph"] = self.m_lap_info.m_top_speed_kmph_overall

        # Insert packet copies if available
        final_json["car-damage"] = self.m_packet_copies.m_packet_car_damage.toJSON() if self.m_packet_copies.m_packet_car_damage else None
        final_json["car-status"] = self.m_packet_copies.m_packet_car_status.toJSON() if self.m_packet_copies.m_packet_car_status else None
        final_json["participant-data"] = self.m_packet_copies.m_packet_particpant_data.toJSON() if self.m_packet_copies.m_packet_particpant_data else None
        final_json["tyre-sets"] = self.m_packet_copies.m_packet_tyre_sets.toJSON() if self.m_packet_copies.m_packet_tyre_sets else None
        final_json["session-history"] = self.m_packet_copies.m_packet_session_history.toJSON() if self.m_packet_copies.m_packet_session_history else None
        final_json["final-classification"] = self.m_packet_copies.m_packet_final_classification.toJSON() if self.m_packet_copies.m_packet_final_classification else None
        final_json["lap-data"] = self.m_packet_copies.m_packet_lap_data.toJSON() if self.m_packet_copies.m_packet_lap_data else None
        final_json["car-setup"] = self.m_packet_copies.m_packet_car_setup.toJSON() if self.m_packet_copies.m_packet_car_setup else None
        final_json["warning-penalty-history"] = [entry.toJSON() for entry in self.m_warning_penalty_history.getEntries()]

        # Insert the tyre set history
        final_json["tyre-set-history"]= self._getTyreSetHistoryJSON()

        # Insert the per lap snapshot
        final_json["per-lap-info"] = []
        for lap_number, snapshot_entry in self._getNextLapSnapshot():
            final_json["per-lap-info"].append(snapshot_entry.toJSON(lap_number))

        if include_tyre_wear_prediction:
            final_json["tyre-wear-predictions"] = self.getFullTyreWearPredictions(selected_pit_stop_lap)

        # Insert the lap time history against tyre used
        final_json["lap-time-history"] = self._getLapTimeHistoryJSON() # can be None, handled in frontend

        # Collisions data
        final_json["collisions"] = self.getCollisionStatsJSON()

        # Race control
        if include_race_ctrl_msgs:
            final_json["race-control"] = self.m_race_ctrl.toJSON(driver_info_dict)

        # Return this fully prepped JSON
        return final_json

    def getFullTyreWearPredictions(self, selected_pit_stop_lap: Optional[int] = None) -> Dict[str, Any]:
        """Get a JSON list with the tyre wear predictions for all remaining laps

        Args:
            selected_pit_stop_lap (Optional[int], optional): The next pit window lap number.

        Returns:
            List[Dict[str, Any]]: List of JSON objects, each containing tyre wear predictions for a specific lap
        """

        tyre_wear_rate = {
            "front-left" : self.m_tyre_info.m_tyre_wear_extrapolator.fl_rate,
            "front-right" : self.m_tyre_info.m_tyre_wear_extrapolator.fr_rate,
            "rear-left" : self.m_tyre_info.m_tyre_wear_extrapolator.rl_rate,
            "rear-right" : self.m_tyre_info.m_tyre_wear_extrapolator.rr_rate,
        }

        if self.m_tyre_info.m_tyre_wear_extrapolator.isDataSufficient():
            return {
                "status" : True,
                "desc" : "Data is sufficient for extrapolation",
                "predictions": [item.toJSON() for item in self.m_tyre_info.m_tyre_wear_extrapolator.predicted_tyre_wear],
                "rate" : tyre_wear_rate,
                "selected-pit-stop-lap": selected_pit_stop_lap
            }
        return {
            "status" : False,
            "desc" : "Insufficient data for extrapolation",
            "predictions": [],
            "rate" : tyre_wear_rate,
            "selected-pit-stop-lap": None
        }

    def getTyrePredictionsJSONList(self, next_pit_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get a JSON list with the tyre wear predictions for next stop/mid point and end of race

        Args:
            next_pit_window (Optional[int], optional): The next pit window lap number.
                If None, then returns the predictions for final lap and half way through between current and final lap

        Returns:
            List[Dict[str, Any]]: List of JSON objects, each containing tyre wear predictions for a specific lap
        """

        if not self.m_tyre_info.m_tyre_wear_extrapolator.isDataSufficient():
            # Data unavailable, return empty list
            return []

        predictions_list = []

        # Input sanitization
        if next_pit_window is None or (next_pit_window == 0) or (next_pit_window < self.m_lap_info.m_current_lap):
            # Lets return the lap midway between current lap and final lap
            next_pit_window = (self.m_lap_info.m_current_lap + self.m_tyre_info.m_tyre_wear_extrapolator.total_laps) // 2

        # NOTE: Flashbacks or delayed telemetry starts can cause the prediction to not be available.
        # This happens in the last lap
        if next_pit_window == self.m_tyre_info.m_tyre_wear_extrapolator.total_laps:
            # We are already in the final lap, so return the final prediction
            if predicted_tyre_wear := self.m_tyre_info.m_tyre_wear_extrapolator.getTyreWearPrediction():
                predictions_list.append(predicted_tyre_wear.toJSON())
        else:

            # Add prediction for next window if available
            pit_lap_prediction = self.m_tyre_info.m_tyre_wear_extrapolator.getTyreWearPrediction(next_pit_window)
            if pit_lap_prediction and next_pit_window:
                predictions_list.append(pit_lap_prediction.toJSON())

            # Add final lap prediction if available
            final_lap_prediction = self.m_tyre_info.m_tyre_wear_extrapolator.getTyreWearPrediction()
            if final_lap_prediction:
                predictions_list.append(final_lap_prediction.toJSON())
        return predictions_list

    def getCurrentTyreWearJSON(self) -> Dict[str, Any]:
        """Get the current tyre wear in JSON format

        Returns:
            JSON object: JSON object containing the current tyre wear
        """

        wear = self.m_tyre_info.tyre_wear.latest
        if not wear:
            return None
        return wear.toJSON()

    def _getTyreSetHistoryJSON(self, include_wear_history: Optional[bool] = True) -> List[Dict[str, Any]]:
        """Get the list of tyre sets used in JSON format

        Args:
            include_wear_history (Optional[bool]): Whether to include the tyre wear history. Defaults to True.

        Returns:
            JSON list: JSON list containing multiple JSON objects, each representing one set of tyres used, in order.
        """

        return self.m_tyre_info.m_tyre_set_history_manager.toJSON(include_wear_history,
                                                    self.m_packet_copies.m_packet_tyre_sets,
                                                    self.m_packet_copies.m_packet_session_history.m_numLaps)

    def _getTyreWearHistoryJSON(self, start_lap : int, end_lap : int):
        """
        Generate JSON data for tyre wear history within specified lap range.

        Args:
            start_lap (int): The starting lap number.
            end_lap (int): The ending lap number.

        Returns:
            list: A list of dictionaries containing lap number and tyre wear data.
        """

        range_of_laps = range(start_lap, end_lap + 1)
        tyre_wear_history = []
        if start_lap == 1:
            tyre_wear_history.append({
                'lap-number': 0,
                'front-right-wear': self.m_per_lap_snapshots[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                'front-left-wear': self.m_per_lap_snapshots[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                'rear-right-wear': self.m_per_lap_snapshots[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                'rear-left-wear': self.m_per_lap_snapshots[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
            })
        for lap_number in range_of_laps:
            if lap_number in self.m_per_lap_snapshots:
                if car_damage_data := self.m_per_lap_snapshots[lap_number].m_car_damage_packet:
                    tyre_wear_history.append({
                        'lap-number': lap_number,
                        'front-right-wear': car_damage_data.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                        'front-left-wear': car_damage_data.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                        'rear-right-wear': car_damage_data.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                        'rear-left-wear': car_damage_data.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                    })
                else:
                    self.m_logger.debug('car damage data not available for lap %d driver %s', lap_number,
                        self.m_driver_info.name)
            else:
                self.m_logger.debug('per lap snapshot not available for lap %d driver %s', lap_number,
                    self.m_driver_info.name)
        return tyre_wear_history

    def _getLapTimeHistoryJSON(self) -> Dict[str, Any]:
        """Get the lap time history in JSON format

        Returns:
            JSON object: JSON object containing the lap time history and tyre info for each lap
        """

        if not self.m_packet_copies.m_packet_session_history:
            return None

        per_lap_tyre_info = self._getPerLapTyreInfoJSON()
        lap_history_data = []
        for index, entry in enumerate(self.m_packet_copies.m_packet_session_history.m_lapHistoryData):
            # Get tyre set history at start of lap (i.e.) end of previous lap
            lap_number = index + 1
            top_speed_kmph = self.m_per_lap_snapshots[lap_number].m_top_speed_kmph \
                if lap_number in self.m_per_lap_snapshots else None
            # Find the tyre set at the specified lap
            tyre_set_info = next((obj for obj in per_lap_tyre_info if obj.get("lap-number") == lap_number), None)
            lap_history_data.append({
                "lap-time-in-ms": entry.m_lapTimeInMS,
                "lap-time-str": F1Utils.millisecondsToMinutesSecondsMilliseconds(entry.m_lapTimeInMS),
                "sector-1-time-in-ms": entry.m_sector1TimeInMS,
                "sector-1-time-minutes": entry.m_sector1TimeMinutes,
                "sector-1-time-str" : F1Utils.getLapTimeStrSplit(entry.m_sector1TimeMinutes,
                    entry.m_sector1TimeInMS),
                "sector-2-time-in-ms": entry.m_sector2TimeInMS,
                "sector-2-time-minutes": entry.m_sector2TimeMinutes,
                "sector-2-time-str": F1Utils.getLapTimeStrSplit(entry.m_sector2TimeMinutes,
                    entry.m_sector2TimeInMS),
                "sector-3-time-in-ms": entry.m_sector3TimeInMS,
                "sector-3-time-minutes": entry.m_sector3TimeMinutes,
                "sector-3-time-str": F1Utils.getLapTimeStrSplit(entry.m_sector3TimeMinutes,
                    entry.m_sector3TimeInMS),
                "lap-valid-bit-flags": entry.m_lapValidBitFlags,
                "tyre-set-info" : tyre_set_info,
                "top-speed-kmph" : top_speed_kmph,
            })
        return {
            "best-lap-time-lap-num": self.m_packet_copies.m_packet_session_history.m_bestLapTimeLapNum,
            "best-sector-1-lap-num": self.m_packet_copies.m_packet_session_history.m_bestSector1LapNum,
            "best-sector-2-lap-num": self.m_packet_copies.m_packet_session_history.m_bestSector2LapNum,
            "best-sector-3-lap-num": self.m_packet_copies.m_packet_session_history.m_bestSector3LapNum,
            "lap-history-data": lap_history_data,
        }

    def _getPerLapTyreInfoJSON(self) -> List[Dict[str, Any]]:
        """Get the per lap tyre info in JSON format

        Returns:
            JSON list: JSON list containing multiple JSON objects, each representing one lap time, in order.
        """

        ret = []
        for tyre_set_meta_data in self.m_tyre_info.m_tyre_set_history_manager.getEntries():
            for tyre_wear in tyre_set_meta_data.m_tyre_wear_history:
                lap_snapshot = self.m_per_lap_snapshots.get(tyre_wear.lap_number)
                tyre_set_data = None

                if not lap_snapshot:
                    self.m_logger.debug("%s - No lap snapshot found for lap number %s. Possible red flag",
                        str(self), tyre_wear.lap_number)
                elif not lap_snapshot.m_tyre_sets_packet:
                    self.m_logger.warning("%s - No tyre sets packet found for lap number %s",
                                        str(self), tyre_wear.lap_number)
                elif not (0 <= tyre_set_meta_data.m_fitted_index < len(lap_snapshot.m_tyre_sets_packet.m_tyreSetData)):
                    self.m_logger.warning("%s - Tyre set index %s out of bounds for lap number %s (array size: %s)",
                        str(self), tyre_set_meta_data.m_fitted_index,tyre_wear.lap_number,
                        len(lap_snapshot.m_tyre_sets_packet.m_tyreSetData))
                else:
                    tyre_set_data = lap_snapshot.m_tyre_sets_packet.m_tyreSetData[tyre_set_meta_data.m_fitted_index]

                ret.append({
                    'tyre-wear' : tyre_wear.toJSON(),
                    'lap-number' : tyre_wear.lap_number,
                    'tyre-set' : tyre_set_data.toJSON() if tyre_set_data else None,
                })
        return ret

    def updateTotalLaps(self, total_laps: int) -> None:
        """Update the total number of laps in all relevant members

        Args:
            total_laps (int): The total number of laps.
        """

        self.m_tyre_info.m_tyre_wear_extrapolator.total_laps = total_laps
        self.m_car_info.m_fuel_rate_recommender.total_laps   = total_laps

        if not self.m_position_history:
            self.m_position_history = [0] * (total_laps + 1) # +1 for zeroth lap

    def _handleFlashBack(self, old_lap_number: int) -> None:
        """Handle a flashback. Remove data from the histories

        Args:
            old_lap_number (int): The old lap number.
        """

        # Ignore practice sessions, since lap count is per practice programme, not overall
        outdated_laps = [key for key in self.m_per_lap_snapshots if key >= old_lap_number]

        # Remove outdated laps from snapshot history
        for lap_num in outdated_laps:
            del self.m_per_lap_snapshots[lap_num]

        # Remove outdated laps from managed objects
        self.m_tyre_info.handleFlashback(outdated_laps)
        self.m_car_info.m_fuel_rate_recommender.remove(outdated_laps)

        self.m_logger.debug("Driver %s - detected flashback. outdated_laps: %s", str(self), outdated_laps)

    def onLapChange(self,
        old_lap_number: int,
        session_type: SessionType,
        is_flashback: Optional[bool] = False) -> None:
        """
        Perform snapshot and projection updates for the given lap change.

        This method is triggered when a lap change is detected. It handles
        per-lap bookkeeping, flashback handling, and projection logic for tyre wear and fuel usage.

        Args:
            old_lap_number (int): The completed lap number.
            session_type (SessionType): The current session type.
            is_flashback (Optional[bool], optional): Whether the lap change is due to a flashback. Defaults to False.

        Behavior:
            - Can be safely called multiple times for the same lap. If data for the lap
            has already been captured, the method will skip processing.

        Operations performed:
            - **Flashback Handling**:
                - If the current lap number is lower than the last recorded lap and it's not a practice session,
                this indicates a flashback or restart. Stale laps are idenified and removed and a snapshot is taken.

            - **Per-Lap Bookkeeping**:
                - Car damage and car status packet copies.
                - Driver's track position at the end of the lap.
                - Top speed achieved during the lap.
                - Maximum safety car status encountered.
                - Tyre sets in use.

            - **Tyre Set History**:
                - Tyre set ID and wear (FL/FR/RL/RR) are recorded into the tyre set history for this lap.

            - **Tyre Wear Projection**:
                - Record tyre wear and racing status of current lap and recompute

            - **Fuel Usage Projection**:
                - Record fuel usage and racing status of current lap and recompute

            - **Cleanup for Next Lap**:
                - Resets temporary per-lap metrics like top speed and safety car status
                to prepare for the next lap.
        """

        # Handle flashbacks/retry practice programmes
        # If old_lap_number is less than max lap num in the dict, then scrap the now outdated data
        if is_flashback and session_type and session_type.isRaceTypeSession():
            self._handleFlashBack(old_lap_number)

        # Check if the old lap number is already present in the snapshots (lap already processed)
        if old_lap_number in self.m_per_lap_snapshots:
            self.m_logger.debug("Driver %s - lap %d already in per_lap_snapshots. Possible flashback",
                             str(self), old_lap_number)
            return

        # Store the snapshot data for the old lap
        self.m_per_lap_snapshots[old_lap_number] = PerLapSnapshotEntry(
            car_damage=self.m_packet_copies.m_packet_car_damage,
            car_status=self.m_packet_copies.m_packet_car_status,
            max_sc_status=self.m_driver_info.m_curr_lap_max_sc_status,
            tyre_sets=self.m_packet_copies.m_packet_tyre_sets,
            track_position=self.m_driver_info.position,
            top_speed_kmph=self.m_lap_info.m_top_speed_kmph_this_lap,
        )

        # Add the tyre wear data into the tyre stint history
        tyre_set_key = self._getCurrentTyreSetKey()
        if old_lap_number and self.m_tyre_info.m_tyre_set_history_manager.length:
            wear = TyreWearPerLap(
                fl_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                fr_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                rl_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                rr_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                lap_number=old_lap_number,
                is_racing_lap=self.m_driver_info.m_curr_lap_max_sc_status,
                desc=f"end of lap {old_lap_number} snapshot. {tyre_set_key}"
            )
            self.m_tyre_info.m_tyre_set_history_manager.addTyreWear(wear)

            # TODO: remove
            if self.m_driver_info.is_player:
                self.m_logger.debug("[ASHWIN] - Added tyre wear %s", wear)

        # Add the tyre wear data into the extrapolator
        if tyre_set_id := self._getCurrentTyreSetKey():
            self.m_tyre_info.m_tyre_wear_extrapolator.add(TyreWearPerLap(
                fl_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                fr_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                rl_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                rr_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                lap_number=old_lap_number,
                is_racing_lap=(self.m_driver_info.m_curr_lap_max_sc_status == SafetyCarType.NO_SAFETY_CAR),
                desc=tyre_set_id
            ))

        # Fuel stuff
        if self.m_packet_copies.m_packet_car_status:
            self.m_car_info.m_fuel_rate_recommender.add(
                self.m_packet_copies.m_packet_car_status.m_fuelInTank,
                old_lap_number,
                (self.m_driver_info.m_curr_lap_max_sc_status == SafetyCarType.NO_SAFETY_CAR), # is_racing_lap
                desc=f"end of lap {old_lap_number} snapshot {tyre_set_key}"
            )

        # Now clear the per lap max stuff
        self.m_lap_info.m_top_speed_kmph_this_lap = None
        self.m_driver_info.m_curr_lap_max_sc_status = None
        self.m_logger.debug("Driver %s - lap %d added to per_lap_snapshots", str(self), old_lap_number)
        if self.m_driver_info.is_player: # TODO: remove
            self.m_logger.debug("[ASHWIN] - lap changed to %d", old_lap_number)

    def shouldCaptureZerothLapSnapshot(self) -> bool:
        """
        Checks if the zeroth lap snapshot should be captured.

        Returns:
            bool - True if the zeroth lap snapshot should be captured
        """

        return (
            self.m_lap_info.m_current_lap == 1 and
            self.isZerothLapSnapshotDataAvailable() and
            not self.isZerothLapSnapshotAlreadyCaptured()
        )

    def isZerothLapSnapshotDataAvailable(self) -> bool:
        """
        Checks if zeroth lap snapshot data is available.

        Returns:
            bool - True if zeroth lap snapshot data is available
        """

        return bool(
            self.m_packet_copies.m_packet_car_damage and
            self.m_packet_copies.m_packet_car_status and
            self.m_packet_copies.m_packet_tyre_sets and
            self.m_driver_info.position and
            (self.m_lap_info.m_top_speed_kmph_this_lap is not None) and
            (self.m_driver_info.m_curr_lap_max_sc_status is not None)
        )

    def isZerothLapSnapshotAlreadyCaptured(self) -> bool:
        """
        Checks if zeroth lap snapshot data has already been captured

        Returns:
            bool - True if zeroth lap snapshot data is available
        """

        return bool(self.m_per_lap_snapshots.get(0))

    def updateTyreSetData(self, fitted_index: int, track: TrackID) -> None:
        """Update the current tyre set in the history list, if required.
               NOTE: The tyre history is ignored if the player has disabled telemetry

        Args:
            fitted_index (int): The fitted tyre set index
            track (TrackID): The track ID enum
        """

        # If telemetry restrictions is none, that means participants packet has not yet arrived. it eventuall will
        # and we can process this then.
        # doing this because some fields in the player obj may be none and handling this is a mess
        # several none checks will be required to handle players that have disabled telemetry. not worth it
        if not self.m_driver_info.telemetry_setting:
            return

        # This can happen if tyre sets packets arrives before lap data packet
        fitted_tyre_set_key = self._getCurrentTyreSetKey()
        if self.m_lap_info.m_current_lap is not None:
            if not self.m_tyre_info.m_tyre_set_history_manager.length:
                if zeroth_lap_snapshot := self.m_per_lap_snapshots.get(0):
                    if car_dmg_pkt := zeroth_lap_snapshot.m_car_damage_packet:
                        # Start of race, enter the tyre wear data along with starting value
                        initial_tyre_wear = TyreWearPerLap(
                            fl_tyre_wear=car_dmg_pkt.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                            fr_tyre_wear=car_dmg_pkt.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                            rl_tyre_wear=car_dmg_pkt.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                            rr_tyre_wear=car_dmg_pkt.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                            lap_number=0,
                            is_racing_lap=True,
                            desc=f"end of zeroth lap data point {fitted_tyre_set_key}"
                        )
                        entry = TyreSetHistoryEntry(
                            start_lap=self.m_lap_info.m_current_lap,
                            index=fitted_index,
                            tyre_set_key=fitted_tyre_set_key,
                            initial_tyre_wear=initial_tyre_wear,
                        )
                        self.m_tyre_info.m_tyre_set_history_manager.add(entry)
                        if self.m_driver_info.is_player: # TODO: remove
                            self.m_logger.debug("[ASHWIN] - Added new entry %s", entry)
                    else:
                        self.m_logger.debug("Driver %s - zeroth lap snapshot available but no car damage packet. "
                                         "Hence clearing the zeroth lap snapshot to trigger it to happen again",
                                            str(self))
                        del self.m_per_lap_snapshots[0]

            elif fitted_index != self.m_tyre_info.m_tyre_set_history_manager.getLastEntry().m_fitted_index:
                # Tyre set change detected
                is_weird = F1Utils.isFinishLineAfterPitGarage(track)
                if is_weird:
                    # In these tracks, the tyre set change happens before lap completion. this causes the prev lap's
                    # tyre wear data could get lost. Hence, tyre set change operation is delayed and handled after
                    #     - lap change
                    #     - car damage packet (new updated tyre wear for the new tyre set)
                    event_mgr = self.m_pending_events_mgr_weird_track
                    events = [
                        DriverPendingEvents.LAP_CHANGE_EVENT,
                        DriverPendingEvents.CAR_DMG_PKT_EVENT,
                    ]

                else:
                    # The game's telemetry emitting task is periodic. It cycles through all types of packets, and
                    #   sleeping between emits based on configured frequency
                    # This means that even the following sequence of events is possible
                    #       1. Car dmg pkt emitted (old tyre value)
                    #       2. Tyre set change event emitted and processed (new tyre set, but old tyre wear value)
                    #       3. Car dmg pkt emitted again (new tyre value)
                    # Without delaying the tyre change event on our end, the new stint's extrapolator could be
                    #   initialised on old tyre's wear value. This means the slope of the new stint's extrapolator
                    #   could be negative, fully breaking the extrapolation logic
                    # Simple fix - delay tyre change event until new car dmg pkt arrives. This will contain the new
                    #   tyre's wear data
                    event_mgr = self.m_pending_events_mgr_normal_track
                    events = [DriverPendingEvents.CAR_DMG_PKT_EVENT]

                if not event_mgr.areEventsPending():
                    event_mgr.register(events=events)
                    self.m_logger.debug("Driver %s - lap %d tyre set change detected. Registering for delayed handling",
                                        str(self), self.m_lap_info.m_current_lap)

    def onTyreSetChange(self, fitted_index: int, fitted_tyre_set_key: str, lap_number: int, initial_tyre_wear: TyreWearPerLap) -> None:
        """Update the tyre set history list, if required.

        Args:
            fitted_index (int): The fitted tyre set index
            fitted_tyre_set_key (str): The fitted tyre set key
            lap_number (int): The lap number
            initial_tyre_wear (TyreWearPerLap): The initial tyre wear
        """

        entry = TyreSetHistoryEntry(
                                    start_lap=lap_number,
                                    index=fitted_index,
                                    tyre_set_key=fitted_tyre_set_key,
                                    initial_tyre_wear=initial_tyre_wear,
        )
        self.m_tyre_info.m_tyre_set_history_manager.add(entry)
        if self.m_driver_info.is_player: # TODO: remove
            self.m_logger.debug("[ASHWIN] - Added new entry %s", entry)

        # Tyre set change detected. clear the extrapolation data
        self.m_tyre_info.m_tyre_wear_extrapolator.clear()
        self.m_tyre_info.m_tyre_wear_extrapolator.add(initial_tyre_wear)

        # Add race control message - there needs to be atleast 2 tyre set history entries (one prev and one current)
        if self.m_tyre_info.m_tyre_set_history_manager.length >= 2:
            prev_entry = self.m_tyre_info.m_tyre_set_history_manager.getLastEntry()
            curr_entry = self.m_tyre_info.m_tyre_set_history_manager.getEntry(index=-2)
            if prev_entry and curr_entry and self.m_packet_copies.m_packet_tyre_sets:
                prev_index = prev_entry.m_fitted_index
                curr_index = curr_entry.m_fitted_index
                prev_set = self.m_packet_copies.m_packet_tyre_sets.getTyreSet(prev_index)
                curr_set = self.m_packet_copies.m_packet_tyre_sets.getTyreSet(curr_index)
                if prev_set and curr_set:
                    self.m_logger.debug("Driver %s - tyre set change detected. prev tyre set: %s, curr tyre set: %s",
                                        str(self), str(prev_set), str(curr_set))
                    self.m_race_ctrl.add_message(TyreChangeRaceControlMessage(
                        timestamp=time.time(),
                        driver_index=self.m_index,
                        lap_number=lap_number,
                        old_tyre_compound=str(prev_set.m_visualTyreCompound),
                        old_tyre_index=prev_index,
                        new_tyre_compound=str(curr_set.m_visualTyreCompound),
                        new_tyre_index=curr_index))

    def processPittingStatus(self, lap_data: LapData) -> None:
        """Process the pit status data

        Args:
            lap_data (LapData): The lap data
        """

        curr_is_pitting = lap_data.m_pitStatus in {LapData.PitStatus.PITTING, LapData.PitStatus.IN_PIT_AREA}
        if not self.m_lap_info.m_is_pitting and curr_is_pitting:
            # entering pits
            self.m_logger.debug("Driver %s - entering pits.", str(self))
            self.m_race_ctrl.add_message(DriverPittingRaceCtrlMsg(
                timestamp=time.time(),
                driver_index=self.m_index,
                lap_number=lap_data.m_currentLapNum))
        elif self.m_lap_info.m_is_pitting and not curr_is_pitting:
            # leaving pits
            self.m_logger.debug("Driver %s - leaving pits.", str(self))

        self.m_lap_info.m_is_pitting = lap_data.m_pitStatus in \
                [LapData.PitStatus.PITTING, LapData.PitStatus.IN_PIT_AREA]
        self.m_driver_info.m_num_pitstops = lap_data.m_numPitStops

    def _getDelayedTyreChangeDataWeird(self) -> Optional[TyreWearPerLap]:
        """Get the initial tyre wear data for the delayed tyre set change handling"""
        idx, initial_tyre_wear = self.m_tyre_info.tyre_wear.get_max_average_with_index()
        if not initial_tyre_wear:
            self.m_logger.warning("Driver %s - unable to process delayed tyre set "
                                  "change since initial wear data is unavailable", str(self))
            return None
        initial_tyre_wear.lap_number = self.m_lap_info.m_current_lap - 1
        self.m_logger.debug("Driver %s - delayed tyre set change. initial tyre wear data: %s. index: %s",
                            str(self), str(initial_tyre_wear), idx)
        return initial_tyre_wear

    def _delayedTyreSetsChangeWeird(self) -> None:
        """Process the delayed tyre set change for weird tracks (where garages are BEFORE the finish line)
        """

        self.m_logger.debug("Driver %s - processing delayed tyre set change for weird track", str(self))
        last_stint_max_wear = self._getDelayedTyreChangeDataWeird()
        tyre_set_key = self.m_packet_copies.m_packet_tyre_sets.getFittedTyreSetKey()
        last_stint_max_wear.desc = f"Delayed tyre set change weird. old tyre val. key={tyre_set_key}"

        # First, overwrite the end of last stint's wear history
        old_val = self.m_tyre_info.m_tyre_set_history_manager.overwriteTyreWear(last_stint_max_wear, stint_index=-1)
        if self.m_driver_info.is_player: # TODO: remove
            self.m_logger.debug("[ASHWIN] - Overwrote latest tyre wear for delayed tyre set change on weird track"
                                ". old val: %s, new val: %s", str(old_val), str(last_stint_max_wear))

        curr_tyre_wear = TyreWearPerLap(
            fl_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
            fr_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
            rl_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
            rr_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
            lap_number=self.m_lap_info.m_current_lap-1,
            is_racing_lap=True,
            desc=f"Delayed tyre set change weird. new tyre val. key={self._getCurrentTyreSetKey()}"
        )
        self.onTyreSetChange(
            fitted_index=self.m_packet_copies.m_packet_tyre_sets.m_fittedIdx,
            fitted_tyre_set_key=tyre_set_key,
            lap_number=self.m_lap_info.m_current_lap,
            initial_tyre_wear=curr_tyre_wear
        )
        self.m_logger.debug("Driver %s - completed processing delayed tyre set change for weird track. "
                            "Initial tyre wear: [%s] New tyre wear: [%s]. History: [%s]",
                                str(self), str(last_stint_max_wear), str(curr_tyre_wear),
                                str(self.m_tyre_info.m_tyre_set_history_manager))

    def _delayedTyreSetsChangeNormal(self) -> None:
        """Process the delayed tyre set change for non-weird tracks (where garages are AFTER the finish line)"""

        self.m_logger.debug("Driver %s - processing delayed tyre set change for non-weird track", str(self))
        fitted_tyre_set_key = self.m_packet_copies.m_packet_tyre_sets.getFittedTyreSetKey()
        initial_tyre_wear = TyreWearPerLap(
            fl_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
            fr_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
            rl_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
            rr_tyre_wear=self.m_packet_copies.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
            lap_number=self.m_lap_info.m_current_lap-1, # -1 because this is the end of last lap value
            is_racing_lap=True,
            desc=f"tyre set change detected. key={str(fitted_tyre_set_key)}"
        )
        self.onTyreSetChange(
            fitted_index=self.m_packet_copies.m_packet_tyre_sets.m_fittedIdx,
            fitted_tyre_set_key=fitted_tyre_set_key,
            lap_number=self.m_lap_info.m_current_lap,
            initial_tyre_wear=initial_tyre_wear
        )

    def _getCurrentTyreSetKey(self) -> Optional[str]:
        """Get the unique ID key for the currently equipped tyre set

        Returns:
            Optional[str]: The tyre set key
        """

        return self.m_packet_copies.m_packet_tyre_sets.getFittedTyreSetKey() \
            if self.m_packet_copies.m_packet_tyre_sets else None

    def _getCurrentTyreSetID(self) -> Optional[int]:
        """Get the ID/index for the currently equipped tyre set

        Returns:
            Optional[int]: The tyre set ID
        """

        return self.m_packet_copies.m_packet_tyre_sets.m_fittedIdx if self.m_packet_copies.m_packet_tyre_sets else None

    def _getNextLapSnapshot(self) -> Iterator[Tuple[int, PerLapSnapshotEntry]]:
        """Yields (lap number, snapshot) for each lap in chronological order."""
        for lap_number in sorted(self.m_per_lap_snapshots.keys()):
            yield lap_number, self.m_per_lap_snapshots[lap_number]

    def getTyreSetInfoAtLap(self, lap_num: Optional[int] = None) -> Optional[TyreSetInfo]:
        """Get the tyre set info at the specified lap number

        Args:
            lap_num (Optional[int]): The lap number. If None, uses current lap number

        Returns:
            Optional[TyreSetInfo]: The tyre set info. None if data not found or invalid lap num
        """

        if self.m_lap_info.m_current_lap is None:
            return None

        if lap_num is None:
            lap_num = self.m_lap_info.m_current_lap

        if lap_num == self.m_lap_info.m_current_lap and self.m_packet_copies.m_packet_car_status:
            return TyreSetInfo(
                actual_tyre_compound=self.m_packet_copies.m_packet_car_status.m_actualTyreCompound,
                visual_tyre_compound=self.m_packet_copies.m_packet_car_status.m_visualTyreCompound,
                tyre_set_id=self._getCurrentTyreSetID(),
                tyre_age_laps=self.m_packet_copies.m_packet_car_status.m_tyresAgeLaps
            )
        if (lap_num < self.m_lap_info.m_current_lap) and (lap_num in self.m_per_lap_snapshots):
            snapshot_at_lap       = self.m_per_lap_snapshots[lap_num]
            snapshot_car_status   = snapshot_at_lap.m_car_status_packet
            snapshot_tyre_sets    = snapshot_at_lap.m_tyre_sets_packet
            if not snapshot_car_status or not snapshot_tyre_sets:
                return None
            return TyreSetInfo(
                actual_tyre_compound=snapshot_car_status.m_actualTyreCompound,
                visual_tyre_compound=snapshot_car_status.m_visualTyreCompound,
                tyre_set_id=snapshot_tyre_sets.m_fittedIdx,
                tyre_age_laps=snapshot_car_status.m_tyresAgeLaps
            )

        return None

    def getCollisionStatsJSON(self) -> Dict[str, Any]:
        """Get the collision stats JSON.

        Returns:
            Dict[str, Any]: Collision stats JSON
        """

        collision_analyzer = CollisionAnalyzer(
            input_mode=CollisionAnalyzerMode.INPUT_MODE_LIST_COLLISION_RECORDS,
            input_data=self.m_collision_records)
        return collision_analyzer.toJSON()

    def getFuelStatsJSON(self) -> Dict[str, Any]:
        """Get the fuel stats JSON.

        Returns:
            Dict[str, Any]: Fuel stats JSON
        """

        if self.m_packet_copies.m_packet_car_status:
            return {
                "fuel-capacity" : self.m_packet_copies.m_packet_car_status.m_fuelCapacity,
                "fuel-mix" : str(self.m_packet_copies.m_packet_car_status.m_fuelMix),
                "fuel-remaining-laps" : self.m_packet_copies.m_packet_car_status.m_fuelRemainingLaps,
                "fuel-in-tank" : self.m_packet_copies.m_packet_car_status.m_fuelInTank,
                "curr-fuel-rate" :self.m_car_info.m_fuel_rate_recommender.curr_fuel_rate,
                "last-lap-fuel-used" : self.m_car_info.m_fuel_rate_recommender.fuel_used_last_lap,
                "target-fuel-rate-average" : self.m_car_info.m_fuel_rate_recommender.target_fuel_rate,
                "target-fuel-rate-next-lap" : self.m_car_info.m_fuel_rate_recommender.target_next_lap_fuel_usage,
                "surplus-laps-png" : self.m_car_info.m_fuel_rate_recommender.surplus_laps,
                "surplus-laps-game" : self.m_packet_copies.m_packet_car_status.m_fuelRemainingLaps,
            }

        return {
            "fuel-capacity" : 0.0,
            "fuel-mix" : 0,
            "fuel-remaining-laps" : 0.0,
            "fuel-in-tank" : 0.0,
            "curr-fuel-rate" : 0.0,
            "last-lap-fuel-used" : 0.0,
            "target-fuel-rate-average" : 0.0,
            "target-fuel-rate-next-lap" : 0.0,
            "surplus-laps-png" : 0.0,
            "surplus-laps-game" : 0.0,
        }

    def getPositionHistoryJSON(self) -> Dict[str, Any]:
        """Get the position history JSON.

        Returns:
            Dict[str, Any]: Position history JSON
        """
        return {
            "name": self.m_driver_info.name,
            "team": self.m_driver_info.team,
            "driver-number": self.m_driver_info.driver_number,
            "driver-position-history": [
                {"lap-number": lap, "position": snapshot.m_track_position}
                for lap, snapshot in self._getNextLapSnapshot()
            ],
        }

    def getSpeedTrapRecordJSON(self) -> Dict[str, Any]:
        """Get the speed trap record JSON.

        Returns:
            Dict[str, Any]: Speed trap record JSON
        """

        return {
            "name": self.m_driver_info.name,
            "team": self.m_driver_info.team,
            "driver-number": self.m_driver_info.driver_number,
            "speed-trap-record-kmph": self.m_lap_info.m_speed_trap_record,
        }

    def getTyreStintHistoryJSON(self) -> Dict[str, Any]:
        """Get the tyre stint history JSON.

        Returns:
            Dict[str, Any]: Tyre stint history JSON
        """

        return {
            "name": self.m_driver_info.name,
            "team": self.m_driver_info.team,
            "telemetry-settings" : str(self.m_driver_info.telemetry_setting),
            "driver-number": self.m_driver_info.driver_number,
            "index": self.m_index,
            "delta-to-leader" : self.m_lap_info.m_delta_to_leader,
            "position" : self.m_driver_info.position,
            "tyre-stint-history": self._getTyreSetHistoryJSON(include_wear_history=False),
        }

    def getTyreStintHistoryJSONv2(self) -> Dict[str, Any]:
        """Get the tyre stint history JSON.

        Returns:
            Dict[str, Any]: Tyre stint history JSON
        """

        return {
            "name": self.m_driver_info.name,
            "team": self.m_driver_info.team,
            "telemetry-settings" : str(self.m_driver_info.telemetry_setting),
            "driver-number": self.m_driver_info.driver_number,
            "index": self.m_index,
            "delta-to-leader" : self.m_lap_info.m_delta_to_leader,
            "race-time" : self.m_lap_info.m_total_race_time,
            "result-status" : self.m_driver_info.m_dnf_status_code,
            "position" : self.m_driver_info.position,
            "grid-position" : self.m_driver_info.grid_position,
            "tyre-stint-history": self._getTyreSetHistoryJSON(include_wear_history=False),
        }

    def updateLapDataPacketCopy(self, lap_data: LapData, full_lap_distance: int) -> None:
        """Add to the warning/penalty history if required and update the lap data packet copy

        Args:
            lap_data (LapData): The incoming lap data packet
            full_lap_distance (int): The distance of the entire lap in metres
        """

        # Update the history and packet copy
        self.m_warning_penalty_history.update(lap_data, full_lap_distance, self.m_packet_copies.m_packet_lap_data)
        self.m_packet_copies.m_packet_lap_data = lap_data

    def getSectorStatus(self,
                        sector_1_best_ms: Optional[int],
                        sector_2_best_ms: Optional[int],
                        sector_3_best_ms: Optional[int],
                        for_best_lap: bool) -> List[Optional[int]]:

        """
        Determine sector status for either best or last lap.

        Args:
            sector_1_best_ms: Best sector 1 time in milliseconds
            sector_2_best_ms: Best sector 2 time in milliseconds
            sector_3_best_ms: Best sector 3 time in milliseconds
            for_best_lap: Whether to analyze best lap or last lap

        Returns:
            List of sector statuses (purple, green, yellow, invalid, or NA)
        """
        default_val = [
            F1Utils.SECTOR_STATUS_NA,
            F1Utils.SECTOR_STATUS_NA,
            F1Utils.SECTOR_STATUS_NA
        ]

        # Validate input/reference data
        if (not self.m_lap_info.m_pb_s1_ms or
            not self.m_lap_info.m_pb_s2_ms or
            not self.m_lap_info.m_pb_s3_ms or
            not sector_1_best_ms or
            not sector_2_best_ms or
            not sector_3_best_ms):
            return default_val

        # Validate driver's data. For best/last lap, all relevant fields must be present
        if for_best_lap and not self.m_lap_info.m_best_lap_obj:
            return default_val
        if not self.m_lap_info.m_last_lap_obj:
            return default_val

        # Select lap object
        lap_obj = self.m_lap_info.m_best_lap_obj if for_best_lap else self.m_lap_info.m_last_lap_obj
        if not lap_obj:
            return default_val

        return [
            self._get_sector_status(
                sector_time=lap_obj.s1TimeMS,
                sector_best_ms=sector_1_best_ms,
                is_personal_best_sector_lap=(lap_obj.s1TimeMS == self.m_lap_info.m_pb_s1_ms),
                sector_valid_flag=lap_obj.isSector1Valid()),
            self._get_sector_status(
                sector_time=lap_obj.s2TimeMS,
                sector_best_ms=sector_2_best_ms,
                is_personal_best_sector_lap=(lap_obj.s2TimeMS == self.m_lap_info.m_pb_s2_ms),
                sector_valid_flag=lap_obj.isSector2Valid()),
            self._get_sector_status(
                sector_time=lap_obj.s3TimeMS,
                sector_best_ms=sector_3_best_ms,
                is_personal_best_sector_lap=(lap_obj.s3TimeMS == self.m_lap_info.m_pb_s3_ms),
                sector_valid_flag=lap_obj.isSector3Valid()),
        ] if lap_obj else default_val

    def getCurrLapSectorStatus(self, s1_best_ms: int, s2_best_ms: int) -> list[Optional[int]]:
        """
        Determine sector status for the current lap.

        Note:
            - Sector 3 is not considered because once it's finished, the lap becomes
            the last lap, not the current lap. Hence, its status is always N/A.

        Args:
            s1_best_ms: Best sector 1 time in milliseconds
            s2_best_ms: Best sector 2 time in milliseconds

        Returns:
            List of sector statuses (purple, green, yellow, invalid, or N/A)
        """

        # If lap hasn't started or still in sector 1
        if not self.m_lap_info.m_curr_lap_ms or self.m_lap_info.m_curr_sector == LapData.Sector.SECTOR1:
            return [
                F1Utils.SECTOR_STATUS_NA,
                F1Utils.SECTOR_STATUS_NA,
                F1Utils.SECTOR_STATUS_NA,
            ]

        # Calculate S1 status (needed for both SECTOR2 and SECTOR3)
        s1_status = self._get_sector_status(
            sector_time=self.m_lap_info.m_curr_lap_s1_ms,
            sector_best_ms=s1_best_ms,
            is_personal_best_sector_lap=(self.m_lap_info.m_curr_lap_s1_ms == self.m_lap_info.m_pb_s1_ms),
            sector_valid_flag=not self.m_lap_info.m_curr_lap_invalid
        )

        # Sector 2 is ongoing
        if self.m_lap_info.m_curr_sector == LapData.Sector.SECTOR2:
            return [s1_status, F1Utils.SECTOR_STATUS_NA, F1Utils.SECTOR_STATUS_NA]

        # Sector 3 (final sector) is ongoing
        s2_status = self._get_sector_status(
            sector_time=self.m_lap_info.m_curr_lap_s2_ms,
            sector_best_ms=s2_best_ms,
            is_personal_best_sector_lap=(self.m_lap_info.m_curr_lap_s2_ms == self.m_lap_info.m_pb_s2_ms),
            sector_valid_flag=not self.m_lap_info.m_curr_lap_invalid
        )
        return [s1_status, s2_status, F1Utils.SECTOR_STATUS_NA]


    def _get_sector_status(
        self,
        sector_time: int,
        sector_best_ms: int,
        is_personal_best_sector_lap: bool,
        sector_valid_flag: bool
    ) -> int:
        """
        Determine the status of a single sector.

        Args:
            sector_time: Time of the current sector
            sector_best_ms: Best time for the sector
            is_personal_best_sector_lap: Whether this is the best lap for this sector
            sector_valid_flag: Whether the sector is valid

        Returns:
            Sector status (purple, green, yellow, invalid)
        """
        if sector_time == sector_best_ms:
            # Session best
            return F1Utils.SECTOR_STATUS_PURPLE
        if is_personal_best_sector_lap:
            # Personal best
            return F1Utils.SECTOR_STATUS_GREEN
        if not sector_valid_flag:
            # Invalidated
            return F1Utils.SECTOR_STATUS_INVALID
        # Meh sector
        return F1Utils.SECTOR_STATUS_YELLOW

    def processPositionsHistoryUpdate(self, packet: PacketLapPositionsData, position_history: List[int]) -> None:
        """Update the position history and packet copy.

        Args:
            packet (PacketLapPositionsData): The incoming lap positions packet
            position_history (List[int]): The position history
        """

        # Defer this update if the position history is not yet initialized
        if not self.m_position_history:
            self.m_logger.debug("Position history: %s", str(self.m_position_history))
            return

        assert len(position_history) == packet.m_numLaps

        # Update the history and packet copy
        self._insert_sublist(
            target=self.m_position_history,
            insert=position_history,
            start=packet.m_lapStart
        )

    def _insert_sublist(self,target: List[int], insert: List[int], start: int) -> None:
        """
        Inserts elements of `insert` into `target` starting at index `start`.

        Modifies the `target` list in-place.

        Args:
            target (List[int]): The list to insert into (must be large enough).
            insert (List[int]): The list of items to insert.
            start (int): The index in `target` at which to start inserting.

        Raises:
            ValueError: If the insertion would exceed the bounds of `target`.
        """
        if start < 0 or start + len(insert) > len(target):
            raise ValueError("Insert range goes out of bounds of the target list.")

        target[start:start + len(insert)] = insert

    def addCarDamageRaceCtrlMsg(self, car_damage: CarDamageData) -> None:
        """Add race control messages for car damage changes

        Args:
            car_damage (CarDamageData): The car damage data
        """

        prev_damage = self.m_packet_copies.m_packet_car_damage
        if not prev_damage:
            return

        changed_fields = prev_damage.diff_fields(
            car_damage,
            self.CAR_DMG_RACE_CTRL_MSG_INTERESTED_FIELDS
        )

        wing_change_emitted = False

        for field, diff in changed_fields.items():
            old = diff["old_value"]
            new = diff["new_value"]

            # ------------------------------------------------------------------
            # Case 1: Damage increased - always report
            # ------------------------------------------------------------------
            if new > old:
                msg = CarDamageRaceControlMessage(
                    timestamp=time.time(),
                    driver_index=self.m_index,
                    lap_number=self.m_lap_info.m_current_lap,
                    damaged_part=field,
                    old_value=old,
                    new_value=new
                )
                self.m_race_ctrl.add_message(msg)

                self.m_logger.debug(
                    "Driver %s - %s damage increased %s - %s. Added CAR_DAMAGE message",
                    str(self), field, old, new
                )
                continue

            # ------------------------------------------------------------------
            # Case 2: Wing damage reset to 0 - wing change (only once)
            # ------------------------------------------------------------------
            if new == 0 and old > 0:
                if not wing_change_emitted:
                    msg = WingChangeRaceCtrlMsg(
                        timestamp=time.time(),
                        driver_index=self.m_index,
                        lap_number=self.m_lap_info.m_current_lap
                    )
                    self.m_race_ctrl.add_message(msg)
                    wing_change_emitted = True

                    self.m_logger.debug(
                        "Driver %s - %s reset %s - 0. Added WING_CHANGE message",
                        str(self), field, old
                    )
                else:
                    self.m_logger.debug(
                        "Driver %s - %s reset %s - 0. Wing change already handled",
                        str(self), field, old
                    )
                continue

            # ------------------------------------------------------------------
            # Case 3: Damage decreased but not to zero (unexpected)
            # ------------------------------------------------------------------
            if new < old:
                self.m_logger.warning(
                    "Driver %s - unexpected damage decrease for %s: %s - %s",
                    str(self), field, old, new
                )
