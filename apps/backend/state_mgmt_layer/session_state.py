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

import json
import logging
import time
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from apps.backend.state_mgmt_layer.data_per_driver import (DataPerDriver,
                                                           DriverPendingEvents)
from apps.backend.state_mgmt_layer.overtakes import (GetOvertakesStatus,
                                                     OvertakesHistory)
from lib.collisions_analyzer import (CollisionAnalyzer, CollisionAnalyzerMode,
                                     CollisionRecord)
from lib.config import PngSettings
from lib.custom_marker_tracker import CustomMarkerEntry, CustomMarkersHistory
from lib.f1_types import (ActualTyreCompound, CarStatusData, F1Utils,
                          FinalClassificationData, GameMode, LapData,
                          PacketCarDamageData, PacketCarSetupData,
                          PacketCarStatusData, PacketCarTelemetryData,
                          PacketEventData, PacketFinalClassificationData,
                          PacketLapData, PacketLapPositionsData,
                          PacketMotionData, PacketParticipantsData,
                          PacketSessionData, PacketSessionHistoryData,
                          PacketTimeTrialData, PacketTyreSetsData,
                          ResultReason, ResultStatus, SafetyCarType,
                          SessionType, TrackID, VisualTyreCompound,
                          WeatherForecastSample)
from lib.inter_task_communicator import (AsyncInterTaskCommunicator,
                                         SessionChangeNotification,
                                         TyreDeltaMessage)
from lib.openf1 import MostRecentPoleLap
from lib.overtake_analyzer import (OvertakeAnalyzer, OvertakeAnalyzerMode,
                                   OvertakeRecord)
from lib.race_analyzer import getFastestTimesJson, getTyreStintRecordsDict
from lib.race_ctrl import (DriverAiStatusChange, SessionRaceControlManager,
                           race_ctrl_event_msg_factory)
from lib.tyre_wear_extrapolator import TyreWearPerLap

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class SessionInfo:
    """
    Class that stores global race data.

    Attributes:
         - m_session_time_left (Optional[int]): The time left in the session in seconds
         - m_track (Optional[TrackID]): The current track
         - m_track_len (Optional[int]): The length of the track in meters
         - m_pit_time_loss (Optional[float]): The pit time loss in seconds
         - m_session_type (Optional[SessionType): The type of the session, will be an enum specific to game year
         - m_session_uid (Optional[int]): The unique identifier of the session
         - m_game_mode (Optional[GameMode]): The current game mode
         - m_track_temp (Optional[int]): The current track temperature in degrees Celsius
         - m_air_temp (Optional[int]): The current air temperature in degrees Celsius
         - m_total_laps (Optional[int]): The total number of laps in the current event
         - m_safety_car_status (Optional[SafetyCarType]): Current safety car status as an enum
         - m_is_spectating (Optional[bool]): Whether the user is currently spectating
         - m_spectator_car_index (Optional[int]): Index of the car the user is spectating
         - m_weather_forecast_samples (Optional[List[WeatherForecastSample]]): List of weather forecast samples
         - m_pit_speed_limit (Optional[int]): The pit lane speed limit in km/h
         - m_packet_session (Optional[PacketSessionData]): Copy of the last saved session packet
         - m_packet_final_classification (Optional[PacketFinalClassificationData]): The final classification packet
         - m_game_year (Optional[int]): The current game year
         - m_packet_format (Optional[int]): The current packet format
         - m_most_recent_pole_lap (Optional[MostRecentPoleLap]): The most recent pole lap IRL
    """

    __slots__ = (
        "m_logger",
        "m_formula",
        "m_track",
        "m_track_len",
        "m_pit_time_loss_f1_dict",
        "m_pit_time_loss_f2_dict",
        "m_pit_time_loss",
        "m_session_type",
        "m_session_uid",
        "m_game_mode",
        "m_track_temp",
        "m_air_temp",
        "m_total_laps",
        "m_safety_car_status",
        "m_is_spectating",
        "m_spectator_car_index",
        "m_weather_forecast_samples",
        "m_pit_speed_limit",
        "m_packet_session",
        "m_packet_final_classification",
        "m_game_year",
        "m_packet_format",
        "m_most_recent_pole_lap",
    )

    def __init__(self, settings: PngSettings, logger: logging.Logger) -> None:
        """
        Init the SessionInfo object fields to None

        Args:
            settings (PngSettings): App Settings
            logger (logging.Logger): Logger
        """

        self.m_logger: logging.Logger = logger
        self.m_formula: Optional[PacketSessionData.FormulaType] = None
        self.m_track : Optional[TrackID] = None
        self.m_track_len: Optional[int] = None
        self.m_pit_time_loss: Optional[float] = None
        self.m_session_type : Optional[SessionType] = None
        self.m_session_uid: Optional[int] = None
        self.m_game_mode: Optional[GameMode] = None
        self.m_track_temp : Optional[int] = None
        self.m_air_temp : Optional[int] = None
        self.m_total_laps : Optional[int] = None
        self.m_safety_car_status : Optional[SafetyCarType] = None
        self.m_is_spectating : Optional[bool] = None
        self.m_spectator_car_index : Optional[int] = None
        self.m_weather_forecast_samples : Optional[List[WeatherForecastSample]] = None
        self.m_pit_speed_limit : Optional[int] = None
        self.m_packet_session: Optional[PacketSessionData] = None
        self.m_packet_final_classification : Optional[PacketFinalClassificationData] = None
        self.m_game_year : Optional[int] = None
        self.m_packet_format : Optional[int] = None
        self.m_most_recent_pole_lap : Optional[MostRecentPoleLap] = None

        # Initialize the pit time loss dicts
        track_name_to_enum = {str(member): member for member in TrackID}
        self.m_pit_time_loss_f1_dict: Dict[TrackID, Optional[float]] = {
            track_name_to_enum[field if field.endswith("_Reverse") else field.replace("_", " ")]: value
            for field, value in settings.TimeLossInPitsF1.model_dump().items()
        }
        self.m_pit_time_loss_f2_dict: Dict[TrackID, Optional[float]] = {
            track_name_to_enum[field if field.endswith("_Reverse") else field.replace("_", " ")]: value
            for field, value in settings.TimeLossInPitsF2.model_dump().items()
        }

    def __str__(self) -> str:
        """Dump the SessionInfo object to a readable string

        Returns:
            str: Readable string
        """
        return (
            f"SessionInfo(m_track={str(self.m_track)}, "
            f"m_formula={str(self.m_formula)}, "
            f"m_track_len={self.m_track_len}, "
            f"m_event_type={str(self.m_session_type)}, "
            f"m_session_uid={self.m_session_uid}, "
            f"m_game_mode={str(self.m_game_mode)}, "
            f"m_track_temp={self.m_track_temp}, "
            f"m_air_temp={self.m_air_temp}, "
            f"m_total_laps={self.m_total_laps}, "
            f"m_safety_car_status={str(self.m_safety_car_status)}, "
            f"m_is_spectating={str(self.m_is_spectating)}"
            f"m_spectator_car_index={str(self.m_spectator_car_index)}, "
            f"m_weather_forecast_samples={str(self.m_weather_forecast_samples)}, "
            f"m_pit_speed_limit={str(self.m_pit_speed_limit)}, "
            f"m_packet_final_classification={str(self.m_packet_final_classification)}"
        )

    def clear(self) -> None:
        """
        Clear the objects contents.
        """

        self.m_formula = None
        self.m_track = None
        self.m_track_len = None
        self.m_session_type = None
        self.m_session_uid = None
        self.m_game_mode = None
        self.m_track_temp = None
        self.m_air_temp = None
        self.m_total_laps = None
        self.m_safety_car_status = None
        self.m_is_spectating = None
        self.m_spectator_car_index = None
        self.m_weather_forecast_samples = None
        self.m_pit_speed_limit = None
        self.m_packet_final_classification = None
        self.m_packet_session = None
        self.m_game_year = None
        self.m_packet_format = None
        self.m_pit_time_loss = None
        self.m_most_recent_pole_lap = None

        # Dont clear the pit loss dicts. they are static

    @property
    def is_valid(self) -> bool:
        """Checks if the SessionInfo object is valid (contains data) """
        return self.m_packet_session

    @property
    def session_ended(self) -> bool:
        """Checks if the session has ended"""
        return bool(self.m_packet_final_classification)

    @property
    def is_online_mode(self) -> bool:
        """Checks if the mode is an online mode."""
        return self.m_game_mode and self.m_game_mode.isOnlineMode()

    def processSessionUpdate(self, packet: PacketSessionData) -> bool:
        """Populates the fields from the session data packet
        Args:
            packet (PacketSessionData): The incoming session update packet

        Returns:
            bool - True if all data needs to be reset
        """

        ret_status = bool(
            self.m_packet_session and
            (packet.m_header.m_sessionUID != self.m_packet_session.m_header.m_sessionUID)
        )
        self.m_formula = packet.m_formula
        self.m_track = packet.m_trackId
        self.m_track_len = packet.m_trackLength
        self.m_track_temp = packet.m_trackTemperature
        self.m_air_temp = packet.m_airTemperature
        self.m_session_type = packet.m_sessionType
        self.m_session_uid = packet.m_header.m_sessionUID
        self.m_game_mode = packet.m_gameMode
        self.m_weather_forecast_samples = packet.m_weatherForecastSamples
        self.m_pit_speed_limit = packet.m_pitSpeedLimit
        self.m_total_laps = packet.m_totalLaps
        self.m_packet_session = packet
        self.m_is_spectating = packet.m_isSpectating
        self.m_spectator_car_index = packet.m_spectatorCarIndex if packet.m_spectatorCarIndex != 255 else None
        self.m_game_year = packet.m_header.m_gameYear
        self.m_packet_format = packet.m_header.m_packetFormat
        self.m_safety_car_status = packet.m_safetyCarStatus

        # Happens only once per session
        if ret_status or self.m_pit_time_loss is None:
            if not isinstance(self.m_formula, PacketSessionData.FormulaType):
                self._clear_pit_time_loss(reason="Invalid type. Could not cast to FormulaType")
            elif self.m_formula.is_f1:
                self.m_pit_time_loss = self.m_pit_time_loss_f1_dict.get(self.m_track)
            elif self.m_formula.is_f2:
                self.m_pit_time_loss = self.m_pit_time_loss_f2_dict.get(self.m_track)
            else:
                self._clear_pit_time_loss(reason="Unsupported formula")

        return ret_status

    def _clear_pit_time_loss(self, reason: str) -> None:
        """Clears the pit time loss value and logs it

        Args:
            reason (str): Reason for clearing
        """
        self.m_pit_time_loss = None
        self.m_logger.debug("%s: %s Clearing pit time loss", reason, str(self.m_formula))

class SessionState:
    """
    Class that models the data for multiple race drivers.

    Attributes:
        m_driver_data (Dict[int, DataPerDriver]): A dictionary mapping driver IDs (int) to their
                            corresponding DataPerDriver instances.
        m_player_index (Optional[int]): The index of the player driver
        m_fastest_index (Optional[int]): The index of the driver who achieved the fastest lap
        m_num_active_cars (Optional[int]): The number of active cars in the race
        m_num_dnf_cars (Optional[int]): The number of cars that did not finish the race
        m_race_completed (Optional[bool]): Indicates whether the race has been completed
        m_is_player_dnf (Optional[bool]): Indicates whether the player has not finished the race
        m_ideal_pit_stop_window (Optional[int]): The ideal pit stop window for the player, according to the selected strategy
        m_collision_records (List[CollisionRecord]): A list of collision records; empty if no collisions occurred.
        m_fastest_s1_ms (Optional[int]): The fastest sector 1 time in milliseconds
        m_fastest_s2_ms (Optional[int]): The fastest sector 2 time in milliseconds
        m_fastest_s3_ms (Optional[int]): The fastest sector 3 time in milliseconds
        m_time_trial_packet (Optional[PacketTimeTrialData]): A packet containing time trial data
        m_overtakes_history (OvertakesHistory): An instance tracking overtakes history.
        m_session_info (SessionInfo): An instance of SessionInfo containing global race data.
        m_post_race_autosave (bool): Flag indicating whether to save data to file after race.
        m_udp_custom_marker_action_code (Optional[int]): The UDP action code for custom marker
        m_udp_tyre_delta_action_code (Optional[int]): The UDP action code for tyre delta notification
        m_process_car_setups (bool): Flag indicating whether to process car setups packets.
        m_save_race_ctrl_msgs (bool): Flag indicating whether to save race control messages to file
                (will still be processed regardless)
        m_custom_markers_history (CustomMarkersHistory): An instance tracking custom markers history.
        m_first_session_update_received (bool): Flag indicating whether the first session update packet has been received.
        m_version (str): Version string
        m_connected_to_sim (bool): Flag indicating whether the client is connected to the simulator
        m_race_ctrl (RaceCtrl): The session race control messages manager
    """

    MAX_DRIVERS: int = 22

    __slots__ = (
        'm_logger',
        'm_pkt_count',
        'm_driver_data',
        'm_player_index',
        'm_fastest_index',
        'm_num_active_cars',
        'm_num_dnf_cars',
        'm_race_completed',
        'm_is_player_dnf',
        'm_ideal_pit_stop_window',
        'm_collision_records',
        'm_fastest_s1_ms',
        'm_fastest_s2_ms',
        'm_fastest_s3_ms',
        'm_time_trial_packet',
        'm_overtakes_history',
        'm_session_info',
        'm_process_car_setups',
        'm_save_race_ctrl_msgs',
        'm_custom_markers_history',
        'm_first_session_update_received',
        'm_version',
        'm_connected_to_sim',
        'm_race_ctrl',
    )

    def __init__(self,
                 logger: logging.Logger,
                 settings: PngSettings,
                 ver_str: str) -> None:
        """Init the DriverData object

        Args:
            logger (logging.Logger): Logger
            settings (PngSettings): Settings
            ver_str (str): Version string
        """

        self.m_logger = logger
        self.m_pkt_count: int = 0
        self.m_driver_data: List[Optional[DataPerDriver]] = [None] * self.MAX_DRIVERS
        self.m_player_index: Optional[int] = None
        self.m_fastest_index: Optional[int] = None
        self.m_num_active_cars: Optional[int] = None
        self.m_num_dnf_cars: Optional[int] = None
        self.m_race_completed: Optional[bool] = None
        self.m_is_player_dnf : Optional[bool] = None
        self.m_ideal_pit_stop_window : Optional[int] = None
        self.m_collision_records : List[CollisionRecord] = []
        self.m_fastest_s1_ms: Optional[int] = None
        self.m_fastest_s2_ms: Optional[int] = None
        self.m_fastest_s3_ms: Optional[int] = None
        self.m_time_trial_packet : Optional[PacketTimeTrialData] = None
        self.m_overtakes_history = OvertakesHistory()
        self.m_session_info: SessionInfo = SessionInfo(settings, logger)
        self.m_first_session_update_received: bool = False
        self.m_version: str = ver_str

        # Config params
        self.m_process_car_setups: bool = settings.Privacy.process_car_setup
        self.m_save_race_ctrl_msgs: bool = settings.Capture.save_race_ctrl_msg

        self.m_custom_markers_history = CustomMarkersHistory()
        self.m_connected_to_sim: bool = False

        self.m_race_ctrl: SessionRaceControlManager = SessionRaceControlManager()

    ####### Control Methods ########

    def clear(self, reason: str) -> None:
        """Clears the DriverData object members. Objects require explicit clearing, primitives can just be set to None

        Args:
            reason (str): Why the data structures should be cleared. Used for logging
        """
        self.m_driver_data = [None] * self.MAX_DRIVERS
        self.m_player_index = None
        self.m_fastest_index = None
        self.m_num_active_cars = None
        self.m_num_dnf_cars = None
        self.m_race_completed = None
        self.m_is_player_dnf = None
        self.m_ideal_pit_stop_window = None
        self.m_collision_records.clear()
        self.m_fastest_s1_ms = None
        self.m_fastest_s2_ms = None
        self.m_fastest_s3_ms = None
        self.m_overtakes_history.clear()
        self.m_first_session_update_received = False
        self.m_session_info.clear()
        self.m_custom_markers_history.clear()
        self.m_race_ctrl.clear()

        self.m_pkt_count = 0

        # No need to clear config params

        self.m_logger.info(f"Clearing all internals. Reason: {reason}")

    @property
    def is_data_available(self) -> bool:
        """Checks if data is available for at least one driver
        """
        return (
            self.m_session_info.is_valid and
            self.m_num_active_cars and
            any(obj and obj.is_valid for obj in self.m_driver_data)
        )

    def setRaceOngoing(self) -> None:
        """
        Set the race as ongoing.
        """
        self.m_race_completed = False

    def setRaceCompleted(self) -> None:
        """
        Set the race as completed.
        """
        self.m_race_completed = True

    def setConnectedToSim(self, connected: bool) -> None:
        """Set whether the client is connected to the simulator. Based on WDT

        Args:
            connected (bool): Whether the client is connected to the simulator
        """
        self.m_logger.debug("WDT: Connected to sim: [%s]->[%s]", self.m_connected_to_sim, connected)
        self.m_connected_to_sim = connected

    ##### Packet event entry points #####

    def processLapDataUpdate(self, packet: PacketLapData) -> None:
        """Process the lap data packet and update the necessary fields

        Args:
            packet (PacketLapData): Lap data object
        """

        num_active_cars = 0
        should_recompute_fastest_lap = False
        for index, lap_data in enumerate(packet.m_lapData):

            driver_obj = self._getObjectByIndex(index, reason="Lap data update")
            driver_obj.m_lap_info.m_result_status = lap_data.m_resultStatus
            if lap_data.m_resultStatus in {ResultStatus.INVALID, ResultStatus.INACTIVE}:
                continue

            num_active_cars += 1
            # Update driver position and timing data
            self._updateDriverPositionData(driver_obj, lap_data)

            # Handle lap changes and snapshots
            if driver_obj.m_lap_info.m_current_lap is not None:
                self._handleLapChangeLogic(driver_obj, lap_data)

            # Update current lap and process driver status
            self._updateDriverStatus(driver_obj, lap_data, index)

            # Update packet copy and check for fastest lap recomputation
            driver_obj.updateLapDataPacketCopy(lap_data, self.m_session_info.m_track_len)

            if not should_recompute_fastest_lap:
                should_recompute_fastest_lap = self._shouldRecomputeFastestLap(driver_obj)

        self.m_num_active_cars = num_active_cars

        if should_recompute_fastest_lap:
            self._recomputeFastestLap()

    def _updateDriverPositionData(self, driver_obj: DataPerDriver, lap_data: LapData) -> None:
        """Update driver position and timing information

        Args:
            driver_obj: Driver object to update
            lap_data: Lap data containing position and timing information
        """
        driver_obj.m_driver_info.position = lap_data.m_carPosition
        driver_obj.m_driver_info.grid_position = lap_data.m_gridPosition
        driver_obj.m_lap_info.processLapDataUpdate(lap_data)

    def _handleLapChangeLogic(self, driver_obj: DataPerDriver, lap_data: LapData) -> None:
        """Handle lap change detection and snapshot capture

        Args:
            driver_obj: Driver object to check for lap changes
            lap_data: Lap data containing current lap number
        """
        # Capture zeroth lap snapshot if needed
        if driver_obj.shouldCaptureZerothLapSnapshot():
            driver_obj.onLapChange(
                old_lap_number=0,
                session_type=self.m_session_info.m_session_type
            )

        current_lap = driver_obj.m_lap_info.m_current_lap
        new_lap = lap_data.m_currentLapNum

        # Check for lap change
        if current_lap != new_lap:
            flashback_detected = (not self.m_session_info.is_online_mode) and (current_lap > new_lap)

            if flashback_detected:
                self.m_logger.debug(f'Driver {driver_obj}. Lap change due to Flashback detected')

            # Use the minimum lap number to handle flashback scenarios
            old_lap_num = min(current_lap, new_lap)
            driver_obj.onLapChange(
                old_lap_number=old_lap_num,
                session_type=self.m_session_info.m_session_type,
                is_flashback=flashback_detected
            )

            driver_obj.m_lap_info.m_current_lap = new_lap
            driver_obj.m_pending_events_mgr.onEvent(DriverPendingEvents.LAP_CHANGE_EVENT)

    def _updateDriverStatus(self, driver_obj: DataPerDriver, lap_data: LapData, driver_index: int) -> None:
        """Update driver's current status including DNF status

        Args:
            driver_obj: Driver object to update
            lap_data: Lap data containing status information
            driver_index: Index of the driver in the race
        """
        RESULT_STATUS_MAP = {
            ResultStatus.DID_NOT_FINISH: "DNF",
            ResultStatus.DISQUALIFIED: "DSQ",
            ResultStatus.RETIRED: "DNF"
        }

        # Update current lap number
        driver_obj.m_lap_info.m_current_lap = lap_data.m_currentLapNum

        # Process pitting status
        driver_obj.processPittingStatus(lap_data, self.m_session_info.m_track)

        # Update DNF status
        driver_obj.m_driver_info.m_dnf_status_code = RESULT_STATUS_MAP.get(
            lap_data.m_resultStatus, ""
        )

        # Check if player is DNF
        if (driver_index == self.m_player_index and
            driver_obj.m_driver_info.m_dnf_status_code):
            self.m_is_player_dnf = True

        # Speed trap
        driver_obj.m_lap_info.m_speed_trap_record = lap_data.m_speedTrapFastestSpeed

    def processFastestLapUpdate(self, packet: PacketEventData.FastestLap) -> None:
        """Process the fastest lap update event notification

        Args:
            packet (PacketEventData.FastestLap): The fastest lap update object
        """

        if not (obj_to_be_updated := self._getObjectByIndex(packet.vehicleIdx, create=False)):
            self.m_logger.debug(f"Fastest lap update event. Driver object not found for index {packet.vehicleIdx}"
                                ". Skipping")
            return
        obj_to_be_updated.m_lap_info.m_best_lap_ms = int(packet.lapTime * 1000) # Convert to int ms, since everything is in int ms
        obj_to_be_updated.m_lap_info.m_best_lap_tyre = obj_to_be_updated.m_tyre_info.tyre_vis_compound
        self.m_fastest_index = packet.vehicleIdx

    def processRetirement(self, packet: PacketEventData.Retirement) -> None:
        """Process the retirement update event notification

        Args:
            packet (PacketEventData.Retirement): The retirement update object
        """

        if not (obj_to_be_updated := self._getObjectByIndex(packet.vehicleIdx, create=False)):
            self.m_logger.debug(f"Retirement update event. Driver object not found for index {packet.vehicleIdx}"
                                ". Skipping")
            return

        obj_to_be_updated.m_driver_info.m_dnf_status_code = 'DNF'
        if packet.vehicleIdx == self.m_player_index:
            self.m_is_player_dnf = True

    def processParticipantsUpdate(self, packet: PacketParticipantsData) -> None:
        """Process the participants update packet and update the necessary fields

        Args:
            packet (PacketParticipantsData): Participants update packet
        """

        self.m_player_index = packet.m_header.m_playerCarIndex if packet.m_header.m_playerCarIndex != 255 else None
        for index, participant in enumerate(packet.m_participants):
            obj_to_be_updated = self._getObjectByIndex(index, reason='Participants update')
            obj_to_be_updated.m_driver_info.name = participant.name
            obj_to_be_updated.m_driver_info.team = str(participant.m_teamId)
            obj_to_be_updated.m_driver_info.driver_number = participant.m_raceNumber
            obj_to_be_updated.m_driver_info.is_player = (index == packet.m_header.m_playerCarIndex)
            obj_to_be_updated.m_driver_info.telemetry_setting = participant.m_yourTelemetry

            if obj_to_be_updated.m_packet_copies.m_packet_particpant_data:
                # Capture all AI state transitions
                old_ai = obj_to_be_updated.m_packet_copies.m_packet_particpant_data.m_aiControlled
                new_ai = participant.m_aiControlled
                if old_ai != new_ai:
                    self.m_logger.debug("%s AI state changed from %s to %s", obj_to_be_updated, old_ai, new_ai)
                    msg = DriverAiStatusChange(
                        timestamp=time.time(),
                        driver_index=index,
                        lap_number=obj_to_be_updated.m_lap_info.m_current_lap,
                        old_state=old_ai,
                        new_state=new_ai,
                    )
                    obj_to_be_updated.m_race_ctrl.add_message(msg)

            # Update pkt copy
            obj_to_be_updated.m_packet_copies.m_packet_particpant_data = participant

    def processCarTelemetryUpdate(self, packet: PacketCarTelemetryData) -> None:
        """Process the car telemetry update packet and update the necessary fields

        Args:
            packet (PacketCarTelemetryData): Car telemetry update packet
        """

        for index, car_telemetry_data in enumerate(packet.m_carTelemetryData):
            obj_to_be_updated = self._getObjectByIndex(index, reason='Car Telemetry update')
            obj_to_be_updated.m_car_info.m_drs_activated = bool(car_telemetry_data.m_drs)
            obj_to_be_updated.m_tyre_info.tyre_inner_temp = \
                    sum(car_telemetry_data.m_tyresInnerTemperature)/len(car_telemetry_data.m_tyresInnerTemperature)
            obj_to_be_updated.m_tyre_info.tyre_surface_temp = \
                    sum(car_telemetry_data.m_tyresSurfaceTemperature)/len(car_telemetry_data.m_tyresSurfaceTemperature)
            obj_to_be_updated.m_lap_info.m_top_speed_kmph_this_lap = (
                car_telemetry_data.m_speed
                if obj_to_be_updated.m_lap_info.m_top_speed_kmph_this_lap is None
                else max(car_telemetry_data.m_speed, obj_to_be_updated.m_lap_info.m_top_speed_kmph_this_lap)
            )
            obj_to_be_updated.m_packet_copies.m_packet_car_telemetry = car_telemetry_data

    def processCarStatusUpdate(self, packet: PacketCarStatusData) -> None:
        """Process the car status update packet and update the necessary fields

        Args:
            packet (PacketCarStatusData): Car status update packet
        """

        for index, car_status_data in enumerate(packet.m_carStatusData):
            obj_to_be_updated = self._getObjectByIndex(index, reason='Car Status update')
            obj_to_be_updated.m_car_info.m_ers_perc = (car_status_data.m_ersStoreEnergy/CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0
            obj_to_be_updated.m_tyre_info.tyre_age = car_status_data.m_tyresAgeLaps
            obj_to_be_updated.m_tyre_info.tyre_vis_compound = car_status_data.m_visualTyreCompound
            obj_to_be_updated.m_tyre_info.tyre_act_compound = car_status_data.m_actualTyreCompound
            obj_to_be_updated.m_car_info.m_drs_allowed = bool(car_status_data.m_drsAllowed)
            obj_to_be_updated.m_car_info.m_drs_distance = car_status_data.m_drsActivationDistance
            obj_to_be_updated.m_packet_copies.m_packet_car_status = car_status_data

    def processFinalClassificationUpdate(self, packet: PacketFinalClassificationData) -> Dict[str, Any]:
        """
        Updates internal state with data from final classification packet.

        Args:
            packet (PacketFinalClassificationData): The incoming final classification packet.
        """

        self.finalClassificationEventUpdater(packet)
        return self.buildFinalClassificationJSON()

    def finalClassificationEventUpdater(self, packet: PacketFinalClassificationData) -> None:
        """Updates internal state with data from final classification packet.

        Args:
            packet (PacketFinalClassificationData): The incoming final classification packet.
        """
        self.m_session_info.m_packet_final_classification = packet

        for index, data in enumerate(packet.m_classificationData):
            driver = self._getObjectByIndex(index, create=False)

            driver.onLapChange(
                old_lap_number=data.m_numLaps,
                session_type=self.m_session_info.m_session_type
            )

            if data.m_position and data.m_position != 255:
                driver.m_driver_info.position = data.m_position
                driver.m_per_lap_snapshots[data.m_numLaps].m_track_position = data.m_position

            driver.m_packet_copies.m_packet_final_classification = data
            driver.m_lap_info.m_total_race_time = data.m_totalRaceTime

            if data.m_position and data.m_position != 255:
                driver.m_driver_info.position = data.m_position

        self.setRaceCompleted()

    def buildFinalClassificationJSON(self) -> Dict[str, Any]:
        """
        Constructs the final classification JSON from internal state.
        If no final classification packet is available, uses an empty skeleton object and fills it.

        Returns:
            Dict[str, Any]: JSON-compatible dict with full final classification info.
        """
        # --- Determine session info and packet format
        session_info = self.m_session_info
        # Use dummy packet if final classification has not been received yet
        packet = session_info.m_packet_final_classification or self._getDummyFinalClassificationPacket()

        packet_format = session_info.m_packet_format
        is_old_format = packet_format == 2023
        is_new_format = packet_format > 2023
        is_position_history_supported = self.isPositionHistorySupported()
        is_speed_trap_supported = is_new_format  # Only supported in F1 2024+

        # --- Start constructing base JSON from packet
        final_json = {
            "classification-data" : []
        }

        speed_trap_records = []
        driver_info_dict = self._getRaceCtrlHelperDict() if self.m_save_race_ctrl_msgs else None

        # --- Initialize optional structures
        if is_position_history_supported:
            final_json["position-history"] = []
            if is_old_format:
                final_json["tyre-stint-history"] = []

        # --- Loop through all drivers in the final classification
        for index, _ in enumerate(packet.m_classificationData):
            driver = self._getObjectByIndex(index, create=False)
            if driver and driver.is_valid:
                # Add driver’s classification info
                final_json["classification-data"].append(driver.toJSON(index=index,
                                                                       include_race_ctrl_msgs=self.m_save_race_ctrl_msgs,
                                                                       driver_info_dict=driver_info_dict))
                # Collect speed trap info
                speed_trap_records.append(driver.getSpeedTrapRecordJSON())

                # Add position history if supported
                if is_position_history_supported:
                    final_json["position-history"].append(driver.getPositionHistoryJSON())
                    if is_old_format:
                        final_json["tyre-stint-history"].append(driver.getTyreStintHistoryJSON())

        # --- Handle speed trap records
        if is_speed_trap_supported:
            final_json["speed-trap-records"] = sorted(
                speed_trap_records, key=lambda x: x["speed-trap-record-kmph"], reverse=True
            )
        else:
            final_json["speed-trap-records"] = []

        # --- Add core metadata (game year, format, session info)
        final_json["game-year"] = session_info.m_game_year
        final_json["packet-format"] = session_info.m_packet_format
        final_json["session-info"] = (
            session_info.m_packet_session.toJSON() if session_info.m_packet_session else None
        )

        # --- Add tyre stint history (v2) if supported
        if is_position_history_supported:
            if is_new_format:
                final_json["tyre-stint-history-v2"] = self.getTyreStintHistoryJSONv2()
            else:
                final_json["tyre-stint-history"].sort(key=lambda x: x["position"])

        # --- Mark race as completed and add any final annotations
        self.setRaceCompleted()
        final_json["custom-markers"] = self.m_custom_markers_history.getJSONList()

        # Add the overtakes as well
        final_json['overtakes'] = {
            'records': [record.toJSON() for record in self.m_overtakes_history.getRecords()]
        }

        # Next, fastest lap and sector records
        final_json['records'] = {
            'fastest' : getFastestTimesJson(final_json),
            'tyre-stats' : getTyreStintRecordsDict(final_json)
        }

        # Finally, race control messages and app version
        if self.m_save_race_ctrl_msgs:
            final_json['race-control'] = self.getRaceControlMessagesJSON(driver_info_dict)
        final_json['version'] = self.m_version
        return final_json

    def processCarDamageUpdate(self, packet: PacketCarDamageData) -> None:
        """Process the car damage update packet and update the necessary fields

        Args:
            packet (PacketCarDamageData): The car damage update packet
        """
        for index, car_damage in enumerate(packet.m_carDamageData):
            obj_to_be_updated = self._getObjectByIndex(index, reason='Car damage update')
            obj_to_be_updated.addCarDamageRaceCtrlMsg(car_damage)
            obj_to_be_updated.m_packet_copies.m_packet_car_damage = car_damage
            obj_to_be_updated.m_tyre_info.tyre_wear = TyreWearPerLap(
                fl_tyre_wear=car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                fr_tyre_wear=car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                rl_tyre_wear=car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                rr_tyre_wear=car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                desc="curr tyre wear"
            )
            obj_to_be_updated.m_car_info.m_fl_wing_damage = car_damage.m_frontLeftWingDamage
            obj_to_be_updated.m_car_info.m_fr_wing_damage = car_damage.m_frontRightWingDamage
            obj_to_be_updated.m_car_info.m_rear_wing_damage = car_damage.m_rearWingDamage
            if obj_to_be_updated.m_pending_events_mgr.areEventsPending():
                obj_to_be_updated.m_pending_events_mgr.data = deepcopy(obj_to_be_updated.m_tyre_info.tyre_wear)
                obj_to_be_updated.m_pending_events_mgr.onEvent(DriverPendingEvents.CAR_DMG_PKT_EVENT)

    def processSessionHistoryUpdate(self, packet: PacketSessionHistoryData) -> None:
        """Process the session history update packet and update the necessary fields

        Args:
            packet (PacketSessionHistoryData): The session history update packet
        """

        # Update the fastest lap variable
        obj_to_be_updated = self._getObjectByIndex(packet.m_carIdx, reason='Session history update')
        obj_to_be_updated.m_packet_copies.m_packet_session_history = packet
        if (packet.m_bestLapTimeLapNum > 0) and (packet.m_bestLapTimeLapNum <= packet.m_numLaps):
            obj_to_be_updated.m_lap_info.m_best_lap_ms = packet.m_lapHistoryData[packet.m_bestLapTimeLapNum-1].m_lapTimeInMS
            tyre_set_info_at_best_lap = obj_to_be_updated.getTyreSetInfoAtLap(packet.m_bestLapTimeLapNum-1)
            obj_to_be_updated.m_lap_info.m_best_lap_tyre = tyre_set_info_at_best_lap.m_visual_tyre_compound \
                if tyre_set_info_at_best_lap else None

        # Recompute fastest lap if required
        if self._shouldRecomputeFastestLap(obj_to_be_updated):
            self._recomputeFastestLap()

        # Update fastest sector times and personal best sector times
        if (packet.m_bestSector1LapNum > 0) and (packet.m_bestSector1LapNum <= packet.m_numLaps):
            obj_to_be_updated.m_lap_info.m_pb_s1_ms = packet.m_lapHistoryData[packet.m_bestSector1LapNum-1].s1TimeMS
            self.m_fastest_s1_ms = self._safeMin(obj_to_be_updated.m_lap_info.m_pb_s1_ms, self.m_fastest_s1_ms)
        if (packet.m_bestSector2LapNum > 0) and (packet.m_bestSector2LapNum <= packet.m_numLaps):
            obj_to_be_updated.m_lap_info.m_pb_s2_ms = packet.m_lapHistoryData[packet.m_bestSector2LapNum-1].s2TimeMS
            self.m_fastest_s2_ms = self._safeMin(obj_to_be_updated.m_lap_info.m_pb_s2_ms, self.m_fastest_s2_ms)
        if (packet.m_bestSector3LapNum > 0) and (packet.m_bestSector3LapNum <= packet.m_numLaps):
            obj_to_be_updated.m_lap_info.m_pb_s3_ms = packet.m_lapHistoryData[packet.m_bestSector3LapNum-1].s3TimeMS
            self.m_fastest_s3_ms = self._safeMin(obj_to_be_updated.m_lap_info.m_pb_s3_ms, self.m_fastest_s3_ms)

        # Update last lap sector time
        last_lap_obj = packet.getLastLapData()
        if last_lap_obj:
            obj_to_be_updated.m_lap_info.m_last_lap_ms = last_lap_obj.m_lapTimeInMS
            obj_to_be_updated.m_lap_info.m_last_lap_obj = last_lap_obj
        else:
            # Clear the best lap obj (can linger if flashback is used or practice programme is restarted)
            if obj_to_be_updated.m_lap_info.m_last_lap_obj:
                self.m_logger.debug(f"Clearing lingering last lap obj for car "
                                 f"{packet.m_carIdx} - {obj_to_be_updated.m_driver_info.name}")
                obj_to_be_updated.m_lap_info.m_last_lap_obj = None
            obj_to_be_updated.m_lap_info.m_last_lap_ms = None

        # Update best lap sector time
        best_lap_obj = packet.getBestLapData()
        if best_lap_obj:
            obj_to_be_updated.m_lap_info.m_best_lap_ms = best_lap_obj.m_lapTimeInMS
            obj_to_be_updated.m_lap_info.m_best_lap_obj = best_lap_obj
            obj_to_be_updated.m_lap_info.m_best_lap_tyre = obj_to_be_updated.m_tyre_info.tyre_vis_compound
        else:
            # Clear the last lap obj (can linger if flashback is used or practice programme is restarted)
            if obj_to_be_updated.m_lap_info.m_best_lap_obj:
                self.m_logger.debug(f"Clearing lingering best lap obj for car {packet.m_carIdx} - "
                                 f"{obj_to_be_updated.m_driver_info.name}")
                obj_to_be_updated.m_lap_info.m_best_lap_obj = None
            obj_to_be_updated.m_lap_info.m_best_lap_ms = None
            obj_to_be_updated.m_lap_info.m_best_lap_tyre = None
            if packet.m_carIdx == self.m_fastest_index:
                self.m_fastest_index = None
                self.m_logger.debug(f"Cleared fastest_index f{packet.m_carIdx}")

    def processTyreSetsUpdate(self, packet: PacketTyreSetsData) -> None:
        """Process the tyre sets update packet and update the necessary fields

        Args:
            packet (PacketTyreSetsData): The tyre sets update packet
        """

        obj_to_be_updated = self._getObjectByIndex(packet.m_carIdx, reason='Tyre sets update')
        obj_to_be_updated.m_packet_copies.m_packet_tyre_sets = packet
        obj_to_be_updated.m_tyre_info.tyre_life_remaining_laps = packet.m_tyreSetData[packet.m_fittedIdx].m_lifeSpan

        # Update the tyre set history
        obj_to_be_updated.updateTyreSetData(fitted_index=packet.m_fittedIdx, track=self.m_session_info.m_track)

    def processMotionUpdate(self, packet: PacketMotionData) -> None:
        """Process the motion update packet and update the necessary fields

        Args:
            packet (PacketMotionData): The motion update packet
        """

        for index, motion_data in enumerate(packet.m_carMotionData):
            obj_to_be_updated = self._getObjectByIndex(index, reason='Motion update')
            obj_to_be_updated.m_packet_copies.m_packet_motion = motion_data

    def processCarSetupsUpdate(self, packet: PacketCarSetupData) -> None:
        """Process the car setup update packet and update the necessary fields

        Args:
            packet (PacketCarSetupData): The car setup update packet
        """

        for index, car_setup in enumerate(packet.m_carSetups):
            obj_to_be_updated = self._getObjectByIndex(index, reason='Car setup update')
            obj_to_be_updated.m_packet_copies.m_packet_car_setup = car_setup

    def processTimeTrialUpdate(self, packet: PacketTimeTrialData) -> None:
        """Process the time trial update packet and update the necessary fields

        Args:
            packet (PacketTimeTrialData): The time trial update packet
        """

        self.m_time_trial_packet = packet

    def processLapPositionsUpdate(self, packet: PacketLapPositionsData) -> None:
        """Process the lap positions update packet and update the necessary fields

        Args:
            packet (PacketLapPositionsData): The lap positions update packet
        """

        if not self.isPositionHistorySupported():
            return

        position_hist_by_index = F1Utils.transposeLapPositions(packet.m_lapPositions)
        for index, position_hist in enumerate(position_hist_by_index):
            if obj_to_be_updated := self._getObjectByIndex(index, create=False):
                obj_to_be_updated.processPositionsHistoryUpdate(packet, position_hist)

    def processSessionStarted(self, reason: str) -> None:
        """
        Reset the data structures when SESSION_STARTED has been received

        Args:
            reason (str): Reason for clearing
        """
        self.clear(reason)
        self.setRaceOngoing()

    async def processSessionUpdate(self, packet: PacketSessionData) -> bool:
        """Update the data strctures with session data
        Args:
            packet (PacketSessionData): Session data packet

            bool - True if all data needs to be reset
        """

        session_changed = self._processSessionUpdateHelper(packet)
        if should_clear := self.m_session_info.processSessionUpdate(packet):
            self.clear("session update")
        if session_changed:
            await self._notifyExternalApiTask()
        return should_clear

    def processCollisionEvent(self, packet: PacketEventData.Collision) -> None:
        """Process the collision event update packet and update the necessary fields

        Args:
            packet (PacketEventData.Collision): The collision event update packet
        """

        collision_obj = self._getCollisionObj(packet.m_vehicle_1_index, packet.m_vehicle_2_index)
        if collision_obj:
            self.m_driver_data[packet.m_vehicle_1_index].m_collision_records.append(collision_obj)
            self.m_driver_data[packet.m_vehicle_2_index].m_collision_records.append(collision_obj)
            self.m_collision_records.append(collision_obj)

    def processOvertakeEvent(self, record: PacketEventData.Overtake) -> None:
        """Processes an overtake event and adds it to the overtake history

        Args:
            record (PacketEventData.Overtake): The overtake event packet
        """

        if (overtake_obj := self._getOvertakeObj(record.overtakingVehicleIdx,
                                                 record.beingOvertakenVehicleIdx)):
            self.m_overtakes_history.insert(overtake_obj)

    def handleEvent(self, packet: PacketEventData):
        """Handle the event packet

        Args:
            packet (PacketEventData): The parsed object containing the event data packet's contents
        """

        # if not self.m_save_race_ctrl_msg:
        #     return

        # Get lap number from leader
        if driver := self.getDriverInfoByPosition(1):
            lap_num = driver.m_lap_info.m_current_lap
        else:
            lap_num = None

        if msg := race_ctrl_event_msg_factory(packet, lap_number=lap_num):
            self.m_race_ctrl.add_message(msg)

    ##### Public Getters #####

    def getDriverInfoJsonByIndex(self, index: int) -> Optional[Dict[str, Any]]:
        """Get the driver info JSON for the specified index.

        Args:
            index (int): Index of the driver

        Returns:
            Optional[Dict[str, Any]]: Driver info JSON. None if invalid index or data not yet available
        """

        driver_info_obj = self._getObjectByIndex(index, create=False)
        if not driver_info_obj:
            return None
        if self.m_race_completed:
            include_wear_prediction = False
            selected_pit_stop_lap = None
        else:
            include_wear_prediction = True
            # Update the pit window for the player if valid
            if driver_info_obj.m_driver_info.is_player and self.m_ideal_pit_stop_window >= driver_info_obj.m_lap_info.m_current_lap:
                selected_pit_stop_lap = self.m_ideal_pit_stop_window
            else:
                selected_pit_stop_lap = None
        driver_info_dict = self._getRaceCtrlHelperDict()
        final_json = driver_info_obj.toJSON(index, include_wear_prediction, selected_pit_stop_lap,
                                            include_race_ctrl_msgs=True, driver_info_dict=driver_info_dict)
        final_json["circuit"] = str(self.m_session_info.m_track)
        final_json["session-type"] = str(self.m_session_info.m_session_type)
        final_json["is-finish-line-after-pit-garage"] = F1Utils.isFinishLineAfterPitGarage(self.m_session_info.m_track) \
            if self.m_session_info.m_track is not None else None

        return final_json

    def getRaceInfoJSON(self) -> Dict[str, Any]:
        """Get the race info JSON.

        Returns:
            Dict[str, Any]: Race info JSON
        """

        return {
            "classification-data" : self._getClassificationDataListJSON(),
            "collisions" : self.getCollisionStatsJSON(),
            "session-info" : self.m_session_info.m_packet_session.toJSON() \
                if self.m_session_info.m_packet_session else None,
            "race-control" : self.getRaceControlMessagesJSON()
            # "race-control" : self.getRaceControlMessagesJSON() if self.m_save_race_ctrl_msg else None
        }

    def getCollisionStatsJSON(self) -> Dict[str, Any]:
        """Get the collision stats JSON.

        Returns:
            Dict[str, Any]: Collision stats JSON
        """

        collision_analyzer = CollisionAnalyzer(
            input_mode=CollisionAnalyzerMode.INPUT_MODE_LIST_COLLISION_RECORDS,
            input_data=self.m_collision_records)
        return collision_analyzer.toJSON()

    def getOvertakeJSON(self, driver_name: str=None) -> Tuple[GetOvertakesStatus, Dict[str, Any]]:
        """Get the JSON value containing key overtake information

        Arguments:
            driver_name (str) - Name of the driver if specific overtake info is required

        Returns:
            Tuple[GetOvertakesStatus, Dict]: Status, JSON value (may be empty)
        """
        final_classification_received = bool(self.m_session_info.m_packet_final_classification)
        if not final_classification_received:
            if len(self.m_overtakes_history.m_overtakes_history) == 0:
                return GetOvertakesStatus.NO_DATA, {}
            return GetOvertakesStatus.RACE_ONGOING, OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS,
                input_data=self.m_overtakes_history.m_overtakes_history).toJSON(
                    driver_name=driver_name,
                    is_case_sensitive=True)
        return GetOvertakesStatus.RACE_COMPLETED, OvertakeAnalyzer(
            input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS,
            input_data=self.m_overtakes_history.m_overtakes_history).toJSON(
                driver_name=driver_name,
                is_case_sensitive=True)

    def getTyreDeltaNotificationMessages(self) -> List[TyreDeltaMessage]:
        """Returns a list of tyre delta notification messages

        Returns:
            List[TyreDeltaMessage]: A list of tyre delta notification messages
        """

        # sourcery skip: assign-if-exp, extract-method
        # N/A for spectating or after race - maybe support this later
        if (self.m_session_info.m_is_spectating or
            self.m_session_info.m_packet_final_classification or
            str(self.m_session_info.m_session_type) == "Time Trial"):
            return []

        # If player ded, not applicable
        if (self.m_player_index is None) or (self.m_is_player_dnf):
            return []
        # Need tyre set packet info
        tyre_sets = self.m_driver_data[self.m_player_index].m_packet_copies.m_packet_tyre_sets
        if not tyre_sets :
            return []

        # Fitted index needs to be valid
        fitted_tyre = tyre_sets.m_fitted_tyre_set
        if not fitted_tyre:
            self.m_logger.error(f"Invalid fitted tyre index: {json.dumps(tyre_sets.toJSON())}")

        # First find the fitted tyre
        wet_tyre_compounds = {
            ActualTyreCompound.WET,
            ActualTyreCompound.WET_CLASSIC,
            ActualTyreCompound.WET_F2
        }
        inter_tyre_compounds = {
            ActualTyreCompound.INTER,
        }
        slick_tyre_compounds = {
            ActualTyreCompound.C6,
            ActualTyreCompound.C5,
            ActualTyreCompound.C4,
            ActualTyreCompound.C3,
            ActualTyreCompound.C2,
            ActualTyreCompound.C1,
            ActualTyreCompound.C0,
            ActualTyreCompound.DRY,
            ActualTyreCompound.SUPER_SOFT,
            ActualTyreCompound.SOFT,
            ActualTyreCompound.MEDIUM,
            ActualTyreCompound.HARD,
        }
        if fitted_tyre.m_actualTyreCompound in wet_tyre_compounds:
            curr_tyre_type = TyreDeltaMessage.TyreType.WET
        elif fitted_tyre.m_actualTyreCompound in inter_tyre_compounds:
            curr_tyre_type = TyreDeltaMessage.TyreType.INTER
        else:
            curr_tyre_type = TyreDeltaMessage.TyreType.SLICK

        if TyreDeltaMessage.TyreType.SLICK == curr_tyre_type:
            # Search for the first wet tyre
            other_tyre_1 = next((tyre_set for tyre_set in reversed(tyre_sets.m_tyreSetData) \
                                if tyre_set.m_actualTyreCompound in wet_tyre_compounds), None)
            other_tyre_1_type = TyreDeltaMessage.TyreType.WET

            # Search for the first inter tyre
            other_tyre_2 = next((tyre_set for tyre_set in reversed(tyre_sets.m_tyreSetData) \
                                if tyre_set.m_actualTyreCompound in inter_tyre_compounds), None)
            other_tyre_2_type = TyreDeltaMessage.TyreType.INTER

        elif TyreDeltaMessage.TyreType.INTER == curr_tyre_type:
            # Search for the first wet tyre
            other_tyre_1 = next((tyre_set for tyre_set in reversed(tyre_sets.m_tyreSetData) \
                                if tyre_set.m_actualTyreCompound in wet_tyre_compounds), None)
            other_tyre_1_type = TyreDeltaMessage.TyreType.WET

            # Search for the first slick tyre
            other_tyre_2 = next((tyre_set for tyre_set in tyre_sets.m_tyreSetData \
                                if tyre_set.m_actualTyreCompound in slick_tyre_compounds), None)
            other_tyre_2_type = TyreDeltaMessage.TyreType.SLICK

        else:
            # Search for the first slick tyre
            other_tyre_1 = next((tyre_set for tyre_set in tyre_sets.m_tyreSetData \
                                if tyre_set.m_actualTyreCompound in slick_tyre_compounds), None)
            other_tyre_1_type = TyreDeltaMessage.TyreType.SLICK

            # Search for the first inter tyre
            other_tyre_2 = next((tyre_set for tyre_set in tyre_sets.m_tyreSetData \
                                if tyre_set.m_actualTyreCompound in inter_tyre_compounds), None)
            other_tyre_2_type = TyreDeltaMessage.TyreType.INTER

        assert other_tyre_1
        assert other_tyre_2
        assert other_tyre_1 != other_tyre_2
        assert other_tyre_1_type != other_tyre_2_type

        if (not other_tyre_1) or (not other_tyre_2):
            self.m_logger.error(f"Invalid other tyre index: {json.dumps(tyre_sets.toJSON())}")
            return []

        return [
            TyreDeltaMessage(
                curr_tyre_type=curr_tyre_type,
                other_tyre_type=other_tyre_1_type,
                delta=(other_tyre_1.m_lapDeltaTime / 1000)),
            TyreDeltaMessage(
                curr_tyre_type=curr_tyre_type,
                other_tyre_type=other_tyre_2_type,
                delta=(other_tyre_2.m_lapDeltaTime / 1000)),
        ]

    def getInsertCustomMarkerEntryObj(self) -> Optional[CustomMarkerEntry]:
        """
        Retrieves the custom marker entry object for the player.

        Returns:
            CustomMarkerEntry: The custom marker entry object for the player. None if any data points is not available
        """
        # Check if player data is available
        if self.m_player_index is None:
            self.m_logger.debug("Player index is None. Cannot generate player_recorded_event_str")
            return None

        if player_data := self._getObjectByIndex(self.m_player_index, create=False):
            # CSV string - <track>,<event-type>,<lap-num>,<sector-num>
            lap_num = player_data.m_lap_info.m_current_lap
            sector = player_data.m_packet_copies.m_packet_lap_data.m_sector
            curr_lap_time = F1Utils.millisecondsToMinutesSecondsMilliseconds(
                player_data.m_packet_copies.m_packet_lap_data.m_currentLapTimeInMS)
            curr_lap_dist = player_data.m_packet_copies.m_packet_lap_data.m_lapDistance

            track = str(self.m_session_info.m_track)
            event_type = str(self.m_session_info.m_session_type)
            curr_lap_percent = (
                f"{F1Utils.floatToStr(float(curr_lap_dist) / float(self.m_session_info.m_track_len) * 100.0)}%"
                if curr_lap_dist is not None
                else None
            )

        else:
            lap_num = None
            sector = None
            curr_lap_time = None
            curr_lap_dist = None

            track = None
            event_type = None
            curr_lap_percent = None

        mandatory_vars = [track, event_type, lap_num, sector, curr_lap_time, curr_lap_percent]
        if any(var is None for var in mandatory_vars):
            self.m_logger.warning("Unable to generate player_recorded_event_str")
            return None

        obj = CustomMarkerEntry(
            track=track,
            event_type=event_type,
            lap=lap_num,
            sector=sector,
            curr_lap_time=curr_lap_time,
            curr_lap_perc=curr_lap_percent
        )
        self.m_custom_markers_history.insert(obj)
        return obj

    def getDriverInfoByPosition(self, position: int) -> Optional[DataPerDriver]:
        """
        Get the driver data by position

        Args:
            position (int): The position of the driver

        Returns:
            Optional[DataPerDriver]: The driver data object
        """
        return next(
            (
                driver_data
                for driver_data in self.m_driver_data
                if (driver_data and driver_data.is_valid) and(driver_data.m_driver_info.position == position)
            ),
            None,
        )

    def getPlayerDriverInfo(self) -> Optional[DataPerDriver]:
        """
        Get the player driver data

        Returns:
            Optional[DataPerDriver]: The player driver data object
        """
        if self.m_player_index is None:
            return None
        return self._getObjectByIndex(self.m_player_index, create=False)

    def getEventInfoStr(self) -> Optional[str]:
        """Returns a string with the following format
                <event-type> _ <circuit> _

        Returns:
            Optional[str]: The event type string (ends with an underscore), or None if no data is available
        """

        if self.m_session_info.m_track and self.m_session_info.m_session_type:
            session_type = str(self.m_session_info.m_session_type)
            track = str(self.m_session_info.m_track)
            return f"{session_type}_{track}".replace(' ', '_') + '_'
        return None

    def getRaceInfo(self) -> Dict[str, Any]:
        """
        Returns the race information as a dictionary with string keys and any values.
        """

        final_json = self.getRaceInfoJSON()
        final_json['records'] = {
            'fastest' : getFastestTimesJson(final_json),
            'tyre-stats' : getTyreStintRecordsDict(final_json),
        }
        return final_json

    def isPositionHistorySupported(self) -> bool:
        """Returns whether the position history is supported for the given event type
            Position history is only supported in race events

        Returns:
            bool: True if the position history is supported, False otherwise
        """
        return bool(self.m_session_info.m_session_type and "Race" in str(self.m_session_info.m_session_type))

    def getTyreStintHistoryJSONv2(self) -> List[Dict[str, Any]]:
        """Get tyre stint history.

        Returns:
            List[Dict[str, Any]]: The tyre stint history JSON
        """

        ret = [
            driver_data.getTyreStintHistoryJSONv2()
            for driver_data in self.m_driver_data
            if driver_data and driver_data.is_valid
        ]
        ret.sort(key=lambda x: x['position'])
        return ret

    def getSaveDataJSON(self) -> Dict[str, Any]:
        """Get the save data JSON."""
        return self.buildFinalClassificationJSON() if self.is_data_available else None

    def getRaceControlMessagesJSON(self, driver_info_dict: Optional[Dict[int, dict]] = None) -> List[Dict[str, Any]]:
        """Get the race control messages JSON."""

        if not driver_info_dict:
            driver_info_dict = self._getRaceCtrlHelperDict()
        return self.m_race_ctrl.toJSON(driver_info_dict)

    ##### Utils #####

    def isIndexValid(self, index: int) -> bool:
        """Check if the given index is a valid driver index

        Args:
            index (int): Index of the driver

        Returns:
            bool: True if valid
        """

        return  (0 <= index < len(self.m_driver_data)) and \
                (self.m_driver_data[index] and self.m_driver_data[index].is_valid)

    ##### Internal Helpers #####

    def _getRaceCtrlHelperDict(self) -> Dict[str, Any]:
        """Get the race control messages helper dictionary. This is a mapping of index against driver info JSON,
        which contains the following keys: `name`, `team`, `driver-number`."""
        return {
            index: {
                'name': driver.m_driver_info.name,
                'team': driver.m_driver_info.team,
                'driver-number': driver.m_driver_info.driver_number,
            }
            for index, driver in enumerate(self.m_driver_data)
            if driver and driver.is_valid
        }

    def _getObjectByIndex(self, index: int, create: bool = True, reason: str = None) -> DataPerDriver:
        """Looks up and retrieves the object at the specified index.
            If not found and create is True, creates the object, inserts into the list, and returns it.

        Args:
            index (int): The driver index
            create (bool, optional): Whether to create the object if not found. Defaults to True.
            reason (str, optional): The reason for creating the object. Defaults to None.

        Returns:
            DataPerDriver: The data object associated with the given index
        """

        assert index is not None, "Index cannot be None"

        if not (obj := self.m_driver_data[index]) and create:
            self.m_logger.debug(f"Creating new DataPerDriver for index {index}. Reason: {reason}")
            obj = DataPerDriver(
                index=index,
                logger=self.m_logger,
                total_laps=self.m_session_info.m_total_laps)
            self.m_driver_data[index] = obj
            self.m_race_ctrl.register_driver(index, obj.m_race_ctrl)
        return obj

    def _recomputeFastestLap(self) -> None:
        """
        Recomputes the fastest lap and updates the necessary fields
        """

        self.m_fastest_index = None
        fastest_time_ms = 500000000000 # cant be slower than this, right?
        for index, driver_data in enumerate(self.m_driver_data):
            if not driver_data or not driver_data.is_valid:
                continue
            if (driver_data.m_lap_info.m_best_lap_ms) and driver_data.m_lap_info.m_best_lap_ms < fastest_time_ms:
                fastest_time_ms = driver_data.m_lap_info.m_best_lap_ms
                self.m_fastest_index = index

    def _shouldRecomputeFastestLap(self, driver_data: DataPerDriver) -> bool:
        """
        Check if the fastest lap needs to be recomputed based on a given driver's data.

        Args:
            driver_data (DataPerDriver): The data for the driver.

        Returns:
            bool: True if the fastest lap needs to be recomputed, False otherwise.
        """

        # False if no data is available
        if self.m_num_active_cars is None or self.m_num_active_cars == 0:
            return False

        # Driver data is not available
        if driver_data.m_lap_info.m_best_lap_ms == 0:
            return False

        # True if fastest lap has not been determined yet
        if self.m_fastest_index is None:
            return True

        # Determine this guy's best lap
        driver_best_lap_ms = None
        if driver_data.m_packet_copies.m_packet_session_history:
            # First option, session history data
            best_lap_index: int = driver_data.m_packet_copies.m_packet_session_history.m_bestLapTimeLapNum - 1
            # sourcery skip: merge-nested-ifs
            if 0 <= best_lap_index < len(driver_data.m_packet_copies.m_packet_session_history.m_lapHistoryData):
                if driver_data.m_packet_copies.m_packet_session_history.m_lapHistoryData[best_lap_index].isLapValid():
                    driver_best_lap_ms = \
                        driver_data.m_packet_copies.m_packet_session_history.m_lapHistoryData[best_lap_index].m_lapTimeInMS
        if driver_best_lap_ms is None:
            # Second option, from the object itself
            driver_best_lap_ms = driver_data.m_lap_info.m_best_lap_ms

        # False if this guy does not have a valid best lap
        if driver_data.m_lap_info.m_best_lap_ms is None:
            return False

        # Check if this guy's lap is faster than the best lap
        return self.m_driver_data[self.m_fastest_index].m_lap_info.m_best_lap_ms > driver_best_lap_ms

    def _processSessionUpdateHelper(self, packet: PacketSessionData) -> bool:
        """Process the Session Update packet. Update the total laps and ideal pit window for the player

        Args:
            packet (PacketSessionData): The incoming parsed packet object

        Returns:
            bool: True if all data needs to be reset
        """

        session_changed = False
        if not self.m_first_session_update_received:
            # This is the first session update for this session. log the session info only once
            self.m_first_session_update_received = True
            session_changed = True
            self.m_logger.info("Session update received: "
                               f"Game Year: {packet.m_header.m_gameYear}, "
                               f"ID: {packet.m_header.m_sessionUID}, "
                               f"Formula: {packet.m_formula}, "
                               f"Game mode: {packet.m_gameMode}, "
                               f"Track: {str(packet.m_trackId)}, "
                               f"Session Type: {str(packet.m_sessionType)}, "
                               f"Weather: {str(packet.m_weather)}, "
                               f"Total Laps: {packet.m_totalLaps}, ")

        self.m_ideal_pit_stop_window = packet.m_pitStopWindowIdealLap

        # First time total laps notification has arrived after driver info (out of order)
        if packet.m_totalLaps:

            # First update the total laps
            self.m_session_info.m_total_laps = packet.m_totalLaps

        # Update the max SC status for all drivers
        for obj_to_be_updated in self.m_driver_data:
            if not obj_to_be_updated or not obj_to_be_updated.is_valid:
                continue
            obj_to_be_updated.m_driver_info.m_curr_lap_max_sc_status = (
                packet.m_safetyCarStatus
                if obj_to_be_updated.m_driver_info.m_curr_lap_max_sc_status is None
                else max(packet.m_safetyCarStatus, obj_to_be_updated.m_driver_info.m_curr_lap_max_sc_status)
            )
            obj_to_be_updated.updateTotalLaps(packet.m_totalLaps)

        return session_changed

    async def _notifyExternalApiTask(self) -> None:
        """Notify the external api task that the session has been updated"""
        await AsyncInterTaskCommunicator().send("external-api-update", SessionChangeNotification(
            trackID=self.m_session_info.m_track,
            session_type=self.m_session_info.m_session_type,
            formula_type=self.m_session_info.m_formula
        ))

    def _getCollisionObj(self, driver_1_index: int, driver_2_index: int) -> Optional[CollisionRecord]:
        """Returns a collision object containing collision information

        Args:
            driver_1_index (int): The index of the first driver
            driver_2_index (int): The index of the second driver

        Returns:
            Optional[CollisionRecord]: A collision object containing collision information
        """

        if not self.m_driver_data:
            return None
        driver_1_obj = self._getObjectByIndex(driver_1_index, create=False)
        driver_2_obj = self._getObjectByIndex(driver_2_index, create=False)
        if driver_1_obj is None or driver_2_obj is None:
            return None

        if driver_1_obj.m_driver_info.name is None or \
            driver_1_obj.m_lap_info.m_current_lap is None or \
                driver_2_obj.m_driver_info.name is None or \
                    driver_2_obj.m_lap_info.m_current_lap is None:
            return None

        return CollisionRecord(
            driver_1_name=driver_1_obj.m_driver_info.name,
            driver_1_lap=driver_1_obj.m_lap_info.m_current_lap,
            driver_1_index=driver_1_index,
            driver_2_name=driver_2_obj.m_driver_info.name,
            driver_2_lap=driver_2_obj.m_lap_info.m_current_lap,
            driver_2_index=driver_2_index
        )

    def _getClassificationDataListJSON(self):
        """
        Return a list of dictionaries containing index, driver name, position, and participant data.
        """
        driver_info_dict = self._getRaceCtrlHelperDict()
        return [driver_data.toJSON(index, include_race_ctrl_msgs=True, driver_info_dict=driver_info_dict) \
                for index, driver_data in enumerate(self.m_driver_data) if driver_data and driver_data.is_valid]

    def _safeMin(self, arg1: int, arg2: Optional[int]) -> int:
        """
        Returns the minimum of two arguments. One is guaranteed to be an integer,
        and the other may be None. If one argument is None, returns the other.

        :param arg1: An integer value (guaranteed).
        :param arg2: An integer or None.
        :return: The smaller of the two integers, or the non-None value if one is None.
        """
        return arg1 if arg2 is None else min(arg1, arg2)

    def _getOvertakeObj(self, overtaking_car_index: int, being_overtaken_index: int) -> Optional[OvertakeRecord]:
        """Returns an overtake object containing overtake information

        Args:
            overtaking_car_index (int): The index of the overtaking car
            being_overtaken_index (int): The index of the car being overtaken

        Returns:
            str: CSV-formatted string containing 4 values
                - Current Lap number of overtaking car
                - Name of driver of overtaking car
                - Current Lap number of car being overtaken
                - Name of driver of car being overtaken
        """
        if not self.m_driver_data:
            return None
        overtaking_car_obj = self._getObjectByIndex(overtaking_car_index, create=False)
        being_overtaken_car_obj = self._getObjectByIndex(being_overtaken_index, create=False)
        if overtaking_car_obj is None or being_overtaken_car_obj is None:
            return None

        # Prepare data for CSV writing
        if overtaking_car_obj.m_driver_info.name is None or \
            overtaking_car_obj.m_lap_info.m_current_lap is None or \
                being_overtaken_car_obj.m_driver_info.name is None or \
                    being_overtaken_car_obj.m_lap_info.m_current_lap is None:
            return None
        return OvertakeRecord(
            overtaking_driver_name=overtaking_car_obj.m_driver_info.name,
            overtaking_driver_lap=overtaking_car_obj.m_lap_info.m_current_lap,
            overtaken_driver_name=being_overtaken_car_obj.m_driver_info.name,
            overtaken_driver_lap=being_overtaken_car_obj.m_lap_info.m_current_lap,
        )

    def _getDummyFinalClassificationPacket(self) -> PacketFinalClassificationData:
        """Returns a dummy final classification packet object

        Returns:
            PacketFinalClassificationData: A dummy final classification packet
        """
        packet = PacketFinalClassificationData.from_values(None, 0, [])
        packet.m_numCars = self.m_num_active_cars
        packet.m_classificationData = [self._getDummyFinalClassificationData() for _ in range(self.m_num_active_cars)]
        return packet

    def _getDummyFinalClassificationData(self) -> FinalClassificationData:
        """Returns a dummy final classification data object

        Returns:
            FinalClassificationData: A dummy final classification data object
        """
        return FinalClassificationData.from_values(
            packet_format=self.m_session_info.m_packet_format,
            position=0,
            num_laps=0,
            grid_position=0,
            points=0,
            num_pit_stops=0,
            result_status=ResultStatus.INVALID,
            result_reason=ResultReason.INVALID,
            best_lap_time_in_ms=0,
            total_race_time=0,
            penalties_time=0,
            num_penalties=0,
            num_tyre_stints=0,
            # tyre_stints_actual,  # array of 8
            tyre_stints_actual_0=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_1=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_2=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_3=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_4=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_5=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_6=ActualTyreCompound.UNKNOWN,
            tyre_stints_actual_7=ActualTyreCompound.UNKNOWN,
            # tyre_stints_visual,  # array of 8
            tyre_stints_visual_0=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_1=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_2=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_3=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_4=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_5=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_6=VisualTyreCompound.UNKNOWN,
            tyre_stints_visual_7=VisualTyreCompound.UNKNOWN,
            # tyre_stints_end_laps,  # array of 8
            tyre_stints_end_laps_0=0,
            tyre_stints_end_laps_1=0,
            tyre_stints_end_laps_2=0,
            tyre_stints_end_laps_3=0,
            tyre_stints_end_laps_4=0,
            tyre_stints_end_laps_5=0,
            tyre_stints_end_laps_6=0,
            tyre_stints_end_laps_7=0
        )
