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
from typing import Any, Dict, List, Optional, Tuple, Union

from apps.backend.state_mgmt_layer.data_per_driver import DataPerDriver
from apps.backend.state_mgmt_layer.overtakes import (GetOvertakesStatus,
                                                     OvertakesHistory)
from lib.collisions_analyzer import (CollisionAnalyzer, CollisionAnalyzerMode,
                                     CollisionRecord)
from lib.custom_marker_tracker import CustomMarkerEntry, CustomMarkersHistory
from lib.f1_types import (ActualTyreCompound, CarStatusData, F1Utils, LapData,
                          PacketCarDamageData, PacketCarSetupData,
                          PacketCarStatusData, PacketCarTelemetryData,
                          PacketEventData, PacketFinalClassificationData,
                          PacketLapData, PacketMotionData,
                          PacketParticipantsData, PacketSessionData,
                          PacketSessionHistoryData, PacketTimeTrialData,
                          PacketTyreSetsData, ResultStatus, SafetyCarType,
                          SessionType23, SessionType24, TrackID,
                          WeatherForecastSample)
from lib.inter_task_communicator import TyreDeltaMessage
from lib.overtake_analyzer import (OvertakeAnalyzer, OvertakeAnalyzerMode,
                                   OvertakeRecord)
from lib.race_analyzer import getFastestTimesJson, getTyreStintRecordsDict
from lib.tyre_wear_extrapolator import TyreWearPerLap

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class SessionInfo:
    """
    Class that stores global race data.

    Attributes:
         - m_track (Optional[TrackID]): The current track
         - m_track_len (Optional[int]): The length of the track in meters
         - m_session_type (Optional[Union[SessionType23, SessionType24]]): The type of the session,
                which can be either SessionType23 or SessionType24
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
    """

    def __init__(self):
        """
        Init the SessionInfo object fields to None
        """

        self.m_track : Optional[TrackID] = None
        self.m_track_len: Optional[int] = None
        self.m_session_type : Optional[Union[SessionType23, SessionType24]] = None
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

    def __str__(self) -> str:
        """Dump the SessionInfo object to a readable string

        Returns:
            str: Readable string
        """
        return (
            f"SessionInfo(m_track={str(self.m_track)}, "
            f"m_track_len={self.m_track_len}, "
            f"m_event_type={str(self.m_session_type)}, "
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

        self.m_track = None
        self.m_track_len = None
        self.m_session_type = None
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

    def processSessionUpdate(self, packet: PacketSessionData) -> bool:
        """Populates the fields from the session data packet
        Args:
            packet (PacketSessionData): The incoming session update packet

        Returns:
            bool - True if all data needs to be reset
        """

        ret_status = bool(
            self.m_packet_session
            and (
                packet.m_header.m_sessionUID
                != self.m_packet_session.m_header.m_sessionUID
            )
        )
        self.m_track = packet.m_trackId
        self.m_track_len = packet.m_trackLength
        self.m_track_temp = packet.m_trackTemperature
        self.m_air_temp = packet.m_airTemperature
        self.m_session_type = packet.m_sessionType
        self.m_weather_forecast_samples = packet.m_weatherForecastSamples
        self.m_pit_speed_limit = packet.m_pitSpeedLimit
        self.m_total_laps = packet.m_totalLaps
        self.m_packet_session = packet
        self.m_is_spectating = packet.m_isSpectating
        self.m_game_year = packet.m_header.m_gameYear
        self.m_safety_car_status = packet.m_safetyCarStatus
        return ret_status

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
    """

    MAX_DRIVERS: int = 22

    __slots__ = [
        'm_logger',
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
        'm_custom_markers_history'
    ]

    def __init__(self,
                 logger: logging.Logger,
                 process_car_setups: bool) -> None:
        """Init the DriverData object

        Args:
            logger (logging.Logger): Logger
            process_car_setups (bool): Whether to process car setups packets
        """

        self.m_logger = logger
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
        self.m_session_info: SessionInfo = SessionInfo()

        # Config params
        self.m_process_car_setups: bool = process_car_setups

        self.m_custom_markers_history = CustomMarkersHistory()

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
        self.m_session_info.clear()
        self.m_custom_markers_history.clear()

        # No need to clear config params

        self.m_logger.debug(f"Clearing all data structures. Reason: {reason}")

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

    ##### Packet event entry points #####

    def processLapDataUpdate(self, packet: PacketLapData) -> None:
        """Process the lap data packet and update the necessary fields

        Args:
            packet (PacketLapData): Lap data object
        """

        num_active_cars = 0
        should_recompute = False
        result_str_map = {
            ResultStatus.DID_NOT_FINISH : "DNF",
            ResultStatus.DISQUALIFIED : "DSQ",
            ResultStatus.RETIRED : "DNF"
        }
        for index, lap_data in enumerate(packet.m_lapData):
            if lap_data.m_resultStatus == ResultStatus.INVALID:
                continue

            num_active_cars += 1

            # Fetch the driver's object
            obj_to_be_updated = self._getObjectByIndex(index)

            # Update the position, time and other fields
            obj_to_be_updated.m_driver_info.position = lap_data.m_carPosition
            obj_to_be_updated.m_lap_info.m_delta_to_car_in_front = lap_data.m_deltaToCarInFrontInMS
            obj_to_be_updated.m_lap_info.m_delta_to_leader = lap_data.m_deltaToRaceLeaderInMS

            # Update the per lap snapshot data structure if lap info is available
            if (obj_to_be_updated.m_lap_info.m_current_lap is not None):
                if obj_to_be_updated.shouldCaptureZerothLapSnapshot():
                    obj_to_be_updated.onLapChange(old_lap_number=0, session_type=self.m_session_info.m_session_type)

                # Now, Take snapshots only at end of laps (i.e.) when m_current_lap is changing
                if (obj_to_be_updated.m_lap_info.m_current_lap != lap_data.m_currentLapNum):
                    # If flashback is used in the pits or just after crossing the start/finish line, the game may be
                    # rewound to the previous lap. In that case, we need to delete the snapshot for that lap
                    # so that it can be captured again.
                    if (flashback_detected := (obj_to_be_updated.m_lap_info.m_current_lap > lap_data.m_currentLapNum)):
                        self.m_logger.debug(f'Driver {obj_to_be_updated}. Lap change due to Flashback detected')

                    # In this case, the lap data packet lap num may be less than the stored current lap
                    old_lap_num = min(obj_to_be_updated.m_lap_info.m_current_lap, lap_data.m_currentLapNum)
                    obj_to_be_updated.onLapChange(old_lap_number=old_lap_num,
                                                  session_type=self.m_session_info.m_session_type,
                                                  is_flashback=flashback_detected)

            # Now, update the current lap number and other shit
            obj_to_be_updated.m_lap_info.m_current_lap =  lap_data.m_currentLapNum
            obj_to_be_updated.m_lap_info.m_is_pitting = lap_data.m_pitStatus in \
                [LapData.PitStatus.PITTING, LapData.PitStatus.IN_PIT_AREA]
            obj_to_be_updated.m_driver_info.m_num_pitstops = lap_data.m_numPitStops
            obj_to_be_updated.m_driver_info.m_dnf_status_code = result_str_map.get(lap_data.m_resultStatus, "")
            # If the player is retired, update the bool variable
            if index == self.m_player_index and len(obj_to_be_updated.m_driver_info.m_dnf_status_code) > 0:
                self.m_is_player_dnf = True

            # Update warning penalty history and copy of the packet
            obj_to_be_updated.updateLapDataPacketCopy(lap_data, self.m_session_info.m_track_len)

            # Check if fastest lap needs to be recomputed
            if not should_recompute:
                should_recompute = self._shouldRecomputeFastestLap(obj_to_be_updated)

        self.m_num_active_cars = num_active_cars
        # Recompute the fastest lap if required
        if should_recompute:
            self._recomputeFastestLap()

    def processFastestLapUpdate(self, packet: PacketEventData.FastestLap) -> None:
        """Process the fastest lap update event notification

        Args:
            packet (PacketEventData.FastestLap): The fastest lap update object
        """

        obj_to_be_updated = self._getObjectByIndex(packet.vehicleIdx)
        obj_to_be_updated.m_lap_info.m_best_lap_ms = int(packet.lapTime * 1000) # Convert to int ms, since everything is in int ms
        obj_to_be_updated.m_lap_info.m_best_lap_tyre = obj_to_be_updated.m_tyre_info.tyre_vis_compound
        self.m_fastest_index = packet.vehicleIdx

    def processRetirement(self, packet: PacketEventData.Retirement) -> None:
        """Process the retirement update event notification

        Args:
            packet (PacketEventData.Retirement): The retirement update object
        """

        obj_to_be_updated = self._getObjectByIndex(packet.vehicleIdx)
        obj_to_be_updated.m_driver_info.m_dnf_status_code = 'DNF'

        if packet.vehicleIdx == self.m_player_index:
            self.m_is_player_dnf = True

    def processParticipantsUpdate(self, packet: PacketParticipantsData) -> None:
        """Process the participants update packet and update the necessary fields

        Args:
            packet (PacketParticipantsData): Participants update packet
        """

        for index, participant in enumerate(packet.m_participants):
            obj_to_be_updated = self._getObjectByIndex(index)
            obj_to_be_updated.m_driver_info.name = participant.m_name
            obj_to_be_updated.m_driver_info.team = str(participant.m_teamId)
            obj_to_be_updated.m_driver_info.driver_number = participant.m_raceNumber
            if (index == packet.m_header.m_playerCarIndex):
                obj_to_be_updated.m_driver_info.is_player = True
                self.m_player_index = index
            else:
                obj_to_be_updated.m_driver_info.is_player = False
            obj_to_be_updated.m_driver_info.telemetry_restrictions = participant.m_yourTelemetry
            obj_to_be_updated.m_packet_copies.m_packet_particpant_data = participant

    def processCarTelemetryUpdate(self, packet: PacketCarTelemetryData) -> None:
        """Process the car telemetry update packet and update the necessary fields

        Args:
            packet (PacketCarTelemetryData): Car telemetry update packet
        """

        for index, car_telemetry_data in enumerate(packet.m_carTelemetryData):
            obj_to_be_updated = self._getObjectByIndex(index)
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
            obj_to_be_updated = self._getObjectByIndex(index)
            obj_to_be_updated.m_car_info.m_ers_perc = (car_status_data.m_ersStoreEnergy/CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0
            obj_to_be_updated.m_tyre_info.tyre_age = car_status_data.m_tyresAgeLaps
            obj_to_be_updated.m_tyre_info.tyre_vis_compound = car_status_data.m_visualTyreCompound
            obj_to_be_updated.m_tyre_info.tyre_act_compound = car_status_data.m_actualTyreCompound
            obj_to_be_updated.m_car_info.m_drs_allowed = bool(car_status_data.m_drsAllowed)
            obj_to_be_updated.m_car_info.m_drs_distance = car_status_data.m_drsActivationDistance
            obj_to_be_updated.m_packet_copies.m_packet_car_status = car_status_data

    def processFinalClassificationUpdate(self, packet: PacketFinalClassificationData) -> Dict[str, Any]:
        """Process the final classification update packet and update the necessary fields.
                Returns a JSON dict of all driver info

        Args:
            packet (PacketFinalClassificationData): The final classification update packet

        Returns:
            Dict[str, Any]: JSON dict of all driver info
        """

        final_json = packet.toJSON()
        is_position_history_supported = self.isPositionHistorySupported()
        if is_position_history_supported:
            final_json["position-history"] = []
            final_json["tyre-stint-history"] = []
        for index, data in enumerate(packet.m_classificationData):
            obj_to_be_updated = self._getObjectByIndex(index, create=False)
            # Perform the final snapshot
            obj_to_be_updated.onLapChange(
                old_lap_number=data.m_numLaps, session_type=self.m_session_info.m_session_type)
            # Sometimes, lapInfo is unreliable. update the track position
            obj_to_be_updated.m_per_lap_snapshots[data.m_numLaps].m_track_position = data.m_position
            obj_to_be_updated.m_driver_info.position = data.m_position
            obj_to_be_updated.m_packet_copies.m_packet_final_classification = data
            final_json["classification-data"][index] = obj_to_be_updated.toJSON(index)
            if is_position_history_supported:
                final_json["position-history"].append(obj_to_be_updated.getPositionHistoryJSON())
                final_json["tyre-stint-history"].append(obj_to_be_updated.getTyreStintHistoryJSON())
        final_json['classification-data'] = sorted(final_json['classification-data'], key=lambda x: x['track-position'])
        final_json['game-year'] = self.m_session_info.m_game_year

        final_json["session-info"] = self.m_session_info.m_packet_session.toJSON() \
            if self.m_session_info.m_packet_session else None
        self.m_session_info.m_packet_final_classification = packet

        self.setRaceCompleted()
        final_json['custom-markers'] = self.m_custom_markers_history.getJSONList()
        return final_json

    def processCarDamageUpdate(self, packet: PacketCarDamageData) -> None:
        """Process the car damage update packet and update the necessary fields

        Args:
            packet (PacketCarDamageData): The car damage update packet
        """
        for index, car_damage in enumerate(packet.m_carDamageData):
            obj_to_be_updated = self._getObjectByIndex(index)
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

    def processSessionHistoryUpdate(self, packet: PacketSessionHistoryData) -> None:
        """Process the session history update packet and update the necessary fields

        Args:
            packet (PacketSessionHistoryData): The session history update packet
        """

        # Update the fastest lap variable
        obj_to_be_updated = self._getObjectByIndex(packet.m_carIdx)
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

        obj_to_be_updated = self._getObjectByIndex(packet.m_carIdx)
        obj_to_be_updated.m_packet_copies.m_packet_tyre_sets = packet
        obj_to_be_updated.m_tyre_info.tyre_life_remaining_laps = packet.m_tyreSetData[packet.m_fittedIdx].m_lifeSpan

        # Update the tyre set history
        obj_to_be_updated.updateTyreSetData(fitted_index=packet.m_fittedIdx)

    def processMotionUpdate(self, packet: PacketMotionData) -> None:
        """Process the motion update packet and update the necessary fields

        Args:
            packet (PacketMotionData): The motion update packet
        """

        for index, motion_data in enumerate(packet.m_carMotionData):
            obj_to_be_updated = self._getObjectByIndex(index)
            obj_to_be_updated.m_packet_copies.m_packet_motion = motion_data

    def processCarSetupsUpdate(self, packet: PacketCarSetupData) -> None:
        """Process the car setup update packet and update the necessary fields

        Args:
            packet (PacketCarSetupData): The car setup update packet
        """

        for index, car_setup in enumerate(packet.m_carSetups):
            obj_to_be_updated = self._getObjectByIndex(index)
            obj_to_be_updated.m_packet_copies.m_packet_car_setup = car_setup

    def processTimeTrialUpdate(self, packet: PacketTimeTrialData) -> None:
        """Process the time trial update packet and update the necessary fields

        Args:
            packet (PacketTimeTrialData): The time trial update packet
        """

        self.m_time_trial_packet = packet


    def processSessionStarted(self) -> None:
        """
        Reset the data structures when SESSION_STARTED has been received
        """
        self.clear("session started")
        self.setRaceOngoing()

    def processSessionUpdate(self, packet: PacketSessionData) -> bool:
        """Update the data strctures with session data
        Args:
            packet (PacketSessionData): Session data packet

            bool - True if all data needs to be reset
        """

        self._processSessionUpdateHelper(packet)
        if should_clear := self.m_session_info.processSessionUpdate(packet):
            self.clear("session update")
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

    ##### Public Getters #####

    def getDriverInfoJsonByIndex(self, index: int) -> Optional[Dict[str, Any]]:
        """Get the driver info JSON for the specified index.

        Args:
            index (int): Index of the driver

        Returns:
            Optional[Dict[str, Any]]: Driver info JSON. None if invalid index or data not yet available
        """

        driver_info_obj = self._getObjectByIndex(index)
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
        final_json = driver_info_obj.toJSON(index, include_wear_prediction, selected_pit_stop_lap)
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
            # "overtakes" : self.getOvertakeStatsJSON()
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
        return self._getObjectByIndex(self.m_player_index) if self.m_player_index is not None else None


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
        if "records" not in final_json:
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

    ##### Internal Helpers #####

    def _getObjectByIndex(self, index: int, create: bool = True) -> DataPerDriver:
        """Looks up and retrieves the object at the specified index.
            If not found and create is True, creates the object, inserts into the list, and returns it.

        Args:
            index (int): The driver index
            create (bool, optional): Whether to create the object if not found. Defaults to True.

        Returns:
            DataPerDriver: The data object associated with the given index
        """

        if not (obj := self.m_driver_data[index]) and create:
            self.m_logger.debug(f"Creating new DataPerDriver for index {index}")
            obj = DataPerDriver(self.m_session_info.m_total_laps)
            self.m_driver_data[index] = obj
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

    def _processSessionUpdateHelper(self, packet: PacketSessionData) -> None:
        """Process the Session Update packet. Update the total laps and ideal pit window for the player

        Args:
            packet (PacketSessionData): The incoming parsed packet object
        """

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
            obj_to_be_updated.m_tyre_info.m_tyre_wear_extrapolator.total_laps = self.m_session_info.m_total_laps
            obj_to_be_updated.m_car_info.m_fuel_rate_recommender.total_laps = self.m_session_info.m_total_laps

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

        return [driver_data.toJSON(index) for index, driver_data in enumerate(self.m_driver_data) \
                if driver_data and driver_data.is_valid]


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


