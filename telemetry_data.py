
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

import threading
import copy
from f1_types import *
import csv
from io import StringIO
from typing import Optional, Generator
from collections import OrderedDict

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class GlobalData:
    """
    Class that stores global race data.

    Attributes:
         - m_circuit (str): The current circuit name
         - m_event_type (str): The current event type
         - m_track_temp (int): The current track temperature
         - m_total_laps (int): The total number of laps in the current event
         - m_safety_car_status (PacketSessionData.SafetyCarStatus): Current safety car status enum
         - m_is_spectating (bool): Whether the user is currently spectating
         - m_spectator_car_index (int): Which car the user is spectating
         - m_weather_forecast_samples (List[WeatherForecastSample]): The list of weather forecast samples
         - m_pit_speed_limit (int): The Pit Lane speed limit (in kmph)
         - m_final_classification_received (bool): Whether the final classification packet has been received
         - m_packet_session (PacketSessionData): Copy of the last saved session packet
    """

    def __init__(self):
        """
        Init the GlobalData object fields to None
        """

        self.m_circuit : Optional[str] = None
        self.m_event_type : Optional[str] = None
        self.m_track_temp : Optional[int] = None
        self.m_total_laps : Optional[int] = None
        self.m_safety_car_status : Optional[PacketSessionData.SafetyCarStatus] = None
        self.m_is_spectating : Optional[bool] = None
        self.m_spectator_car_index : Optional[int] = None
        self.m_weather_forecast_samples : Optional[List[WeatherForecastSample]] = None
        self.m_pit_speed_limit : Optional[int] = None
        self.m_final_classification_received : Optional[bool] = None
        self.m_packet_session: Optional[PacketSessionData] = None

    def __str__(self) -> str:
        """Dump the GlobalData object to a readable string

        Returns:
            str: Readable string
        """
        return (
            f"GlobalData(m_circuit={self.m_circuit}, "
            f"m_event_type={self.m_event_type}, "
            f"m_track_temp={self.m_track_temp}, "
            f"m_total_laps={self.m_total_laps}, "
            f"m_safety_car_status={str(self.m_safety_car_status)}, "
            f"m_is_spectating={str(self.m_is_spectating)}"
            f"m_spectator_car_index={str(self.m_spectator_car_index)}, "
            f"m_weather_forecast_samples={str(self.m_weather_forecast_samples)}, "
            f"m_pit_speed_limit={str(self.m_pit_speed_limit)}, "
            f"m_final_classification_received={str(self.m_final_classification_received)}")

    def clear(self) -> None:
        """
        Clear the objects contents. Resets m_final_classification_received to False
        """

        self.m_circuit = None
        self.m_event_type = None
        self.m_track_temp = None
        self.m_total_laps = None
        self.m_safety_car_status = None
        self.m_is_spectating = None
        self.m_spectator_car_index = None
        self.m_weather_forecast_samples = None
        self.m_pit_speed_limit = None
        self.m_final_classification_received = False
        self.m_packet_session = None

    def processSessionUpdate(self, packet: PacketSessionData) -> bool:
        """Populates the fields from the session data packet

        Args:
            packet (PacketSessionData): The incoming session update packet

        Returns:
            bool - True if all data needs to be reset
        """

        ret_status = False
        if self.m_packet_session:
            if packet.m_header.m_sessionUID != self.m_packet_session.m_header.m_sessionUID:
                ret_status = True

        self.m_circuit = str(packet.m_trackId)
        self.m_track_temp = packet.m_trackTemperature
        self.m_event_type = str(packet.m_sessionType)
        self.m_total_laps = packet.m_totalLaps
        self.m_safety_car_status = packet.m_safetyCarStatus
        self.m_is_spectating = bool(packet.m_isSpectating)
        self.m_spectator_car_index = packet.m_spectatorCarIndex
        self.m_weather_forecast_samples = packet.m_weatherForecastSamples
        self.m_pit_speed_limit = packet.m_pitSpeedLimit
        self.m_packet_session = packet
        return ret_status

class DataPerDriver:
    """
    Class that models the data stored per race driver.

    Attributes:
        m_position (Optional[int]): The current position of the driver in the race.
        m_name (Optional[str]): The name of the driver.
        m_team (Optional[str]): The team to which the driver belongs.
        m_delta (Optional[str]): The time difference between the driver and the leader.
        m_delta_to_leader (Optional[str]): The time difference to the race leader.
        m_ers_perc (Optional[float]): The percentage of ERS (Energy Recovery System) remaining.
        m_best_lap (Optional[str]): The best lap time achieved by the driver.
        m_last_lap (Optional[str]): The time taken for the last lap completed by the driver.
        m_tyre_wear (Optional[float]): The level of wear on the driver's tires.
        m_is_player (Optional[bool]): Indicates whether the driver is the player.
        m_current_lap (Optional[int]): The current lap the driver is on.
        m_penalties (Optional[str]): Penalties accumulated by the driver.
        m_tyre_age (Optional[int]): The age of the driver's current set of tires.
        m_tyre_compound_type (Optional[str]): The type of tire compound being used by the driver.
        m_tyre_surface_temp (Optional[float]): The surface temperature of the driver's tires.
        m_tyre_inner_temp (Optional[float]): The inner temperature of the driver's tires.
        m_is_pitting (Optional[bool]): Indicates whether the driver is currently in the pit lane.
        m_drs_activated (Optional[bool]): Indicates whether the DRS (Drag Reduction System) is activated for the driver.
        m_drs_allowed (Optional[bool]): Indicates whether DRS is allowed for the driver.
        m_drs_distance (Optional[int]): The distance to the car in front for DRS activation.
        m_num_pitstops (Optional[int]): The number of pitstops made by the driver.
        m_dnf_status_code (Optional[str]): Status code indicating if the driver did not finish the race.
        m_tyre_life_remaining_laps (Optional[int]): The remaining laps the tires are expected to last.
        m_telemetry_restrictions (Optional[ParticipantData.TelemetrySetting]):
            Telemetry settings indicating the level of data available for the driver.
        m_tyre_set_history (List[DataPerDriver.TyreSetHistoryEntry]):
            List of TyreSetHistoryEntry objects, representing the driver's tire set history.

        m_packet_lap_data (Optional[LapData]): Copy of LapData packet for the driver.
        m_packet_participant_data (Optional[ParticipantData]): Copy of ParticipantData packet for the driver.
        m_packet_car_telemetry (Optional[CarTelemetryData]): Copy of CarTelemetryData packet for the driver.
        m_packet_car_status (Optional[CarStatusData]): Copy of CarStatusData packet for the driver.
        m_packet_car_damage (Optional[CarDamageData]): Copy of CarDamageData packet for the driver.
        m_packet_session_history (Optional[PacketSessionHistoryData]):
            Copy of PacketSessionHistoryData packet for the driver.
        m_packet_tyre_sets (Optional[PacketTyreSetsData]): Copy of PacketTyreSetsData packet for the driver.
        m_packet_final_classification (Optional[FinalClassificationData]):
            Copy of FinalClassificationData packet for the driver.
    """

    class TyreSetHistoryEntry:
        """
        Class that models the data stored per entry in the tyre set history list.

        Attributes:
            m_start_lap (int): The lap at which the tire set was fitted.
            m_fitted_index (int): The index representing the fitted tire set.
            m_end_lap (Optional[int]): The lap at which the tire set was removed.
                                            Must be set using the _computeTyreStintEndLaps method
        """

        def __init__(self, start_lap: int, index: int):
            """Initialize the TyreSetHistoryEntry object. The m_end_lap attribute will be set to None

            Args:
                start_lap (int): The lap at which the tire set was fitted.
                index (int): The index representing the fitted tire set.
            """
            assert start_lap is not None
            self.m_start_lap = start_lap
            self.m_fitted_index = index
            self.m_end_lap = None

    class PerLapHistoryEntry:
        """
        Class that captures one lap's backup data

        Attributes:
            m_car_damage_packet (CarDamageData): The Car damage packet
            m_car_status_packet (CarStatusData): The Car Status packet
        """

        def __init__(self,
                     car_damage : CarDamageData,
                     car_status : CarStatusData):
            """Init the backup entry object

            Args:
                car_damage (CarDamageData): The Car damage packet
                car_status (CarStatusData): The Car Status packet
            """

            self.m_car_damage_packet: Optional[CarDamageData] = car_damage
            self.m_car_status_packet: Optional[CarStatusData] = car_status

        def toJSON(self, lap_number : int) -> Dict[str, Any]:

            return {
                "lap-number" : lap_number,
                "car-damage-data" : self.m_car_damage_packet.toJSON() if self.m_car_damage_packet else None,
                "car-status-data" : self.m_car_status_packet.toJSON() if self.m_car_status_packet else None
            }

    def __init__(self):
        """
        Init the data per driver fields
        """
        self.m_position: Optional[int] = None
        self.m_name: Optional[str] = None
        self.m_team: Optional[str] = None
        self.m_delta: Optional[str] = None
        self.m_delta_to_leader: Optional[str] = None
        self.m_ers_perc: Optional[float] = None
        self.m_best_lap: Optional[str] = None
        self.m_last_lap: Optional[str] = None
        self.m_tyre_wear: Optional[float] = None
        self.m_is_player: Optional[bool] = None
        self.m_current_lap: Optional[int] = None
        self.m_penalties: Optional[str] = None
        self.m_tyre_age: Optional[int] = None
        self.m_tyre_compound_type: Optional[str] = None
        self.m_tyre_surface_temp: Optional[float] = None
        self.m_tyre_inner_temp: Optional[float] = None
        self.m_is_pitting: Optional[bool] = None
        self.m_drs_activated: Optional[bool] = None
        self.m_drs_allowed: Optional[bool] = None
        self.m_drs_distance: Optional[int] = None
        self.m_num_pitstops: Optional[int] = None
        self.m_dnf_status_code: Optional[str] = None
        self.m_tyre_life_remaining_laps: Optional[int] = None
        self.m_telemetry_restrictions: Optional[ParticipantData.TelemetrySetting] = None
        self.m_tyre_set_history: List[DataPerDriver.TyreSetHistoryEntry] = []

        # packet copies
        self.m_packet_lap_data: Optional[LapData] = None
        self.m_packet_particpant_data: Optional[ParticipantData] = None
        self.m_packet_car_telemetry: Optional[CarTelemetryData] = None
        self.m_packet_car_status: Optional[CarStatusData] = None
        self.m_packet_car_damage: Optional[CarDamageData] = None
        self.m_packet_session_history: Optional[PacketSessionHistoryData] = None
        self.m_packet_tyre_sets: Optional[PacketTyreSetsData] = None
        self.m_packet_final_classification: Optional[FinalClassificationData] = None

        # Per lap backup
        self.m_per_lap_backups: Dict[int, DataPerDriver.PerLapHistoryEntry] = {}

    def toJSON(self, index: Optional[int] = None) -> Dict[str, Any]:
        """Get a JSON representation of this DataPerDriver object

        Args:
            index (int): The index number. Defaults to None.

        Returns:
            Dict[str, Any]: The JSON dict
        """
        final_json = {}

        # Add the primary data
        if index:
            final_json["index"] = index
        final_json["driver-name"] = self.m_name
        final_json["track-position"] = self.m_position
        final_json["telemetry-settings"] = str(self.m_telemetry_restrictions)

        # Insert packet copies if available
        if self.m_packet_car_damage:
            final_json["car-damage"] = self.m_packet_car_damage.toJSON()
        if self.m_packet_car_status:
            final_json["car-status"] = self.m_packet_car_status.toJSON()
        if self.m_packet_particpant_data:
            final_json["participant-data"] = self.m_packet_particpant_data.toJSON()
        if self.m_packet_tyre_sets:
            final_json["tyre-sets"] = self.m_packet_tyre_sets.toJSON()
        if self.m_packet_session_history:
            final_json["session-history"] = self.m_packet_session_history.toJSON()
        if self.m_packet_final_classification:
            final_json["final-classification"] = self.m_packet_final_classification.toJSON()
        if self.m_packet_lap_data:
            final_json["lap-data"] = self.m_packet_lap_data.toJSON()

        # Insert the tyre set history
        final_json["tyre-set-history"]= []
        self._computeTyreStintEndLaps()
        for entry in self.m_tyre_set_history:
            is_index_valid = 0 < entry.m_fitted_index < len(self.m_packet_tyre_sets.m_tyreSetData)
            final_json["tyre-set-history"].append({
                'start-lap' : entry.m_start_lap,
                'end-lap' : entry.m_end_lap,
                'stint-length' : (entry.m_end_lap+1-entry.m_start_lap),
                'fitted-index' : entry.m_fitted_index,
                'tyre-set-data' : self.m_packet_tyre_sets.m_tyreSetData[entry.m_fitted_index].toJSON() \
                                    if is_index_valid else None
            })

        # Insert the per lap backup
        final_json["per-lap-info"] = []
        for lap_number, backup_entry in self._getNextLapBackup():
            final_json["per-lap-info"].append(backup_entry.toJSON(lap_number))

        # Return this fully prepped JSON
        return final_json

    def onLapChange(self, old_lap_number: int) -> None:
        """
        Perform backup for the given lap change.

        Args:
            old_lap_number (int): The old lap number.

        Returns:
            None
        """
        # Check if the old lap number is already present in the backups
        if not old_lap_number in self.m_per_lap_backups:
            # Create a backup entry for the current lap
            backup_data = DataPerDriver.PerLapHistoryEntry(
                car_damage=self.m_packet_car_damage,
                car_status=self.m_packet_car_status
            )

            # Store the backup data for the old lap
            self.m_per_lap_backups[old_lap_number] = backup_data

    def _getNextLapBackup(self) -> Generator[Tuple[int, PerLapHistoryEntry], None, None]:
        """
        Returns a generator for each lap's backup in order.

        Yields:
            Tuple[int, PerLapHistoryEntry]: Tuple containing lap number and backup data for each lap.
        """
        for lap_number in sorted(self.m_per_lap_backups.keys()):
            yield lap_number, self.m_per_lap_backups[lap_number]

    def _computeTyreStintEndLaps(self) -> None:
        """
        Compute the end lap number for each tyre stint
        """

        # Don't do any of this if we have no tyre stint history. Fuck those guys who have telemetry off
        if len(self.m_tyre_set_history) > 0:
            self._cleanTyreStintHistory()
            for i in range(len(self.m_tyre_set_history) - 1):
                current_stint = self.m_tyre_set_history[i]
                next_stint = self.m_tyre_set_history[i + 1]
                current_stint.m_end_lap = next_stint.m_start_lap - 1
                assert current_stint.m_start_lap is not None

            # For the last tyre stint, get end lap num from session history
            self.m_tyre_set_history[-1].m_end_lap = self.m_packet_session_history.m_numLaps
            assert self.m_tyre_set_history[-1].m_start_lap is not None

    def _cleanTyreStintHistory(self) -> None:
        """If consecutive entries with same start lap exist, only the last instance will be retained.
             Consecutive duplicate entries are created when the player spams flashback in the pit lane
        """

        # Clean the input list by removing all but the last occurrence of consecutive items with the same m_start_lap
        cleaned_tyre_set_history_list = []
        last_occurrence_dict = OrderedDict()

        for entry in self.m_tyre_set_history:
            last_occurrence_dict[entry.m_start_lap] = entry

        # Collect the last occurrences into the cleaned list
        for last_occurrence in last_occurrence_dict.values():
            cleaned_tyre_set_history_list.append(last_occurrence)

        # Update the history list
        self.m_tyre_set_history = cleaned_tyre_set_history_list

class DriverData:
    """
    Class that models the data for multiple race drivers.

    Attributes:
        m_driver_data (Dict[int, DataPerDriver]): Dictionary containing driver data indexed by driver ID.
        m_player_index (int): The index of the player driver.
        m_fastest_index (int): The index of the driver who achieved the fastest lap.
        m_num_active_cars (int): The number of active cars in the race.
        m_num_dnf_cars (int): The number of cars that did not finish the race.
        m_race_completed (bool): Indicates whether the race has been completed.
        m_final_json (Dict[str, Any]): Dictionary containing the final JSON data for the driver.
    """

    def __init__(self):
        """
        Initialize the DriverData object.
        """
        self.m_driver_data: Dict[int, DataPerDriver] = {}
        self.m_player_index: int = None
        self.m_fastest_index: int = None
        self.m_num_active_cars: int = None
        self.m_num_dnf_cars: int = None
        self.m_race_completed: bool = None
        self.m_final_json: Dict[str, Any] = None

    def clear(self) -> None:
        """Clear this object. Clears the m_driver_data list and sets everything else to None
        """
        self.m_driver_data.clear()
        self.m_player_index = None
        self.m_fastest_index = None
        self.m_num_active_cars = None
        self.m_num_dnf_cars = None
        self.m_race_completed = None
        self.m_final_json = None

    def getIndexByTrackPosition(self, track_position) -> Tuple[Optional[int], Optional[DataPerDriver]]:
        """
        Get the driver index and data based on the provided track position.

        Args:
            track_position: The track position to search for.

        Returns:
            Tuple[Optional[int], Optional[DataPerDriver]]: A tuple containing the driver index and corresponding
                DataPerDriver object if found; otherwise, (None, None).
        """
        for index, driver_data in self.m_driver_data.items():
            if driver_data.m_position == track_position:
                return index, copy.deepcopy(driver_data)
        return None, None

    def _getPenaltyString(self, penalties_sec: int, num_dt: int, num_sg: int) -> str:
        """Computes and returns a printable string capturing all penalties

        Args:
            penalties_sec (int): The time penalty in second
            num_dt (int): Number of drive through penalties
            num_sg (int): Number of stop/go penalties

        Returns:
            str: The penalty string
        """

        if penalties_sec == 0 and num_dt == 0 and num_sg == 0:
            return ""
        penalty_string = "("
        started_filling = False
        if penalties_sec > 0:
            penalty_string += "+" + str(penalties_sec) + " sec"
            started_filling = True
        if num_dt > 0:
            if started_filling:
                penalty_string += " + "
            penalty_string += str(num_dt) + "DT"
            started_filling = True
        if num_sg:
            if started_filling:
                penalty_string += " + "
            penalty_string += str(num_sg) + "SG"
        penalty_string += ")"
        return penalty_string

    def _getObjectByIndexCreate(self, index: int) -> DataPerDriver:
        """Looks up and retrieves the object at the specified index.
                If not found, creates the object, inserts into the dict and returns

        Args:
            index (int): The driver index

        Returns:
            DataPerDriver: The data object associated with the given index
        """

        # create index if not found
        if index not in self.m_driver_data:
            self.m_driver_data[index] = DataPerDriver()
        return self.m_driver_data[index]

    def _recomputeFastestLap(self) -> None:
        """
        Recomputes the fastest lap and updates the necessary fields
        """
        # TODO - handle case where multiple cars have same fastest time.
        self.m_fastest_index = None
        fastest_time_ms = 500000000000 # cant be slower than this, right?
        for index, driver_data in self.m_driver_data.items():
            if driver_data.m_best_lap is not None:
                temp_lap_ms = F1Utils.timeStrToMilliseconds(driver_data.m_best_lap)
                if temp_lap_ms > 0 and temp_lap_ms < fastest_time_ms:
                    fastest_time_ms = temp_lap_ms
                    self.m_fastest_index = index

    def _shouldRecomputeFastestLap(self) -> bool:
        """Whether fastest lap needs to be recomputed

        Returns:
            bool: True if recomputation is required
        """

        if (self.m_fastest_index is None) and (self.m_num_active_cars is not None):
            count_null_best_times = 0
            for curr_index, driver_data in _driver_data.m_driver_data.items():
                if curr_index >= _driver_data.m_num_active_cars:
                    continue
                if driver_data.m_best_lap is None:
                    count_null_best_times += 1
            if count_null_best_times == 0:
                # only recompute once all the best lap times are available
                return True
            else:
                return False
        else:
            return False

    def _updateTyreSetData(self, driver_data: DataPerDriver, fitted_index: int) -> None:
        """Update the current tyre set in the history list, if required.
               NOTE: The tyre history is ignored if the player has disabled telemetry

        Args:
            driver_data (DataPerDriver): The driver data object
            fitted_index (int): The fitted tyre set index
        """

        # This can happen if tyre sets packets arrives before lap data packet
        if driver_data.m_current_lap is not None:
            # fuck those anti telemetry cunts
            if driver_data.m_telemetry_restrictions == ParticipantData.TelemetrySetting.PUBLIC:
                if len(driver_data.m_tyre_set_history) == 0:
                    driver_data.m_tyre_set_history.append(DataPerDriver.TyreSetHistoryEntry(
                                                start_lap=driver_data.m_current_lap,
                                                index=fitted_index))
                else:
                    if fitted_index != driver_data.m_tyre_set_history[-1].m_fitted_index:
                        driver_data.m_tyre_set_history.append(DataPerDriver.TyreSetHistoryEntry(
                                                start_lap=driver_data.m_current_lap,
                                                index=fitted_index))

    def processLapDataUpdate(self, packet: PacketLapData) -> None:
        """Process the lap data packet and update the necessary fields

        Args:
            packet (PacketLapData): Lap data object
        """

        num_active_cars = 0
        result_str_map = {
            ResultStatus.DID_NOT_FINISH : "DNF",
            ResultStatus.DISQUALIFIED : "DSQ",
            ResultStatus.RETIRED : "DNF"
        }
        for index, lap_data in enumerate(packet.m_LapData):

            if lap_data.m_resultStatus == ResultStatus.INVALID:
                continue
            num_active_cars += 1

            # Fetch the driver's object
            obj_to_be_updated = self._getObjectByIndexCreate(index)

            # Update the position, time and other fields
            obj_to_be_updated.m_position = lap_data.m_carPosition
            obj_to_be_updated.m_last_lap = F1Utils.millisecondsToMinutesSecondsMilliseconds(lap_data.m_lastLapTimeInMS) \
                if (lap_data.m_lastLapTimeInMS > 0) else "---"
            obj_to_be_updated.m_delta = lap_data.m_deltaToCarInFrontInMS
            obj_to_be_updated.m_delta_to_leader = lap_data.m_deltaToRaceLeaderInMS
            obj_to_be_updated.m_penalties = self._getPenaltyString(lap_data.m_penalties,
                                lap_data.m_numUnservedDriveThroughPens, lap_data.m_numUnservedStopGoPens)
            if (obj_to_be_updated.m_current_lap) and (obj_to_be_updated.m_current_lap != lap_data.m_currentLapNum):
                obj_to_be_updated.onLapChange(obj_to_be_updated.m_current_lap)
            obj_to_be_updated.m_current_lap =  lap_data.m_currentLapNum

            obj_to_be_updated.m_is_pitting = True if lap_data.m_pitStatus in \
                    [LapData.PitStatus.PITTING, LapData.PitStatus.IN_PIT_AREA] else False
            obj_to_be_updated.m_num_pitstops = lap_data.m_numPitStops
            obj_to_be_updated.m_dnf_status_code = result_str_map.get(lap_data.m_resultStatus, "")

            # Save a copy of the packet
            obj_to_be_updated.m_packet_lap_data = lap_data

        self.m_num_active_cars = num_active_cars
        # Recompute the fastest lap if required
        if self._shouldRecomputeFastestLap():
            self._recomputeFastestLap()

    def processFastestLapUpdate(self, packet: PacketEventData.FastestLap) -> None:
        """Process the fastest lap update event notification

        Args:
            packet (PacketEventData.FastestLap): The fastest lap update object
        """

        obj_to_be_updated = self._getObjectByIndexCreate(packet.vehicleIdx)
        obj_to_be_updated.m_best_lap = F1Utils.floatSecondsToMinutesSecondsMilliseconds(packet.lapTime)
        self.m_fastest_index = packet.vehicleIdx

    def processRetirement(self, packet: PacketEventData.Retirement) -> None:
        """Process the retirement update event notification

        Args:
            packet (PacketEventData.Retirement): The retirement update object
        """

        obj_to_be_updated = self._getObjectByIndexCreate(packet.vehicleIdx)
        obj_to_be_updated.m_dnf_status_code = True

    def processParticipantsUpdate(self, packet: PacketParticipantsData) -> None:
        """Process the participants update packet and update the necessary fields

        Args:
            packet (PacketParticipantsData): Participants update packet
        """

        for index, participant in enumerate(packet.m_participants):
            obj_to_be_updated = self._getObjectByIndexCreate(index)
            obj_to_be_updated.m_name = participant.m_name
            obj_to_be_updated.m_team = str(participant.m_teamId)
            if (index == packet.m_header.m_playerCarIndex):
                obj_to_be_updated.m_is_player = True
                self.m_player_index = index
            else:
                obj_to_be_updated.m_is_player = False
            obj_to_be_updated.m_telemetry_restrictions = participant.m_yourTelemetry
            obj_to_be_updated.m_packet_particpant_data = participant

    def processCarTelemetryUpdate(self, packet: PacketCarTelemetryData) -> None:
        """Process the car telemetry update packet and update the necessary fields

        Args:
            packet (PacketCarTelemetryData): Car telemetry update packet
        """

        for index, car_telemetry_data in enumerate(packet.m_carTelemetryData):
            obj_to_be_updated = self._getObjectByIndexCreate(index)
            obj_to_be_updated.m_drs_activated = bool(car_telemetry_data.m_drs)
            obj_to_be_updated.m_tyre_inner_temp = \
                    sum(car_telemetry_data.m_tyresInnerTemperature)/len(car_telemetry_data.m_tyresInnerTemperature)
            obj_to_be_updated.m_tyre_surface_temp = \
                    sum(car_telemetry_data.m_tyresSurfaceTemperature)/len(car_telemetry_data.m_tyresSurfaceTemperature)
            obj_to_be_updated.m_packet_car_telemetry = car_telemetry_data

    def processCarStatusUpdate(self, packet: PacketCarStatusData) -> None:
        """Process the car status update packet and update the necessary fields

        Args:
            packet (PacketCarStatusData): Car status update packet
        """

        for index, car_status_data in enumerate(packet.m_carStatusData):
            obj_to_be_updated = self._getObjectByIndexCreate(index)
            obj_to_be_updated.m_ers_perc = (car_status_data.m_ersStoreEnergy/CarStatusData.max_ers_store_energy) * 100.0
            obj_to_be_updated.m_tyre_age = car_status_data.m_tyresAgeLaps
            obj_to_be_updated.m_tyre_compound_type = str(car_status_data.m_actualTyreCompound) + ' - ' + \
                str(car_status_data.m_visualTyreCompound)
            obj_to_be_updated.m_drs_allowed = bool(car_status_data.m_drsAllowed)
            obj_to_be_updated.m_drs_distance = car_status_data.m_drsActivationDistance
            obj_to_be_updated.m_packet_car_status = car_status_data

    def processFinalClassificationUpdate(self, packet: PacketFinalClassificationData) -> Dict[str, Any]:
        """Process the final classification update packet and update the necessary fields.
                Returns a JSON dict of all driver info

        Args:
            packet (PacketFinalClassificationData): The final classification update packet

        Returns:
            Dict[str, Any]: JSON dict of all driver info
        """

        _driver_data.m_race_completed = True
        final_json = packet.toJSON()
        for index, data in enumerate(packet.m_classificationData):
            obj_to_be_updated = self.m_driver_data.get(index, None)
            # Perform the final backup
            obj_to_be_updated.onLapChange(data.m_numLaps)
            if obj_to_be_updated:
                obj_to_be_updated.m_position = data.m_position
                obj_to_be_updated.m_packet_final_classification = data
                final_json["classification-data"][index] = obj_to_be_updated.toJSON(index)
        final_json['classification-data'] = sorted(final_json['classification-data'], key=lambda x: x['track-position'])
        self.m_final_json = final_json
        return final_json

    def processCarDamageUpdate(self, packet: PacketCarDamageData) -> None:
        """Process the car damage update packet and update the necessary fields

        Args:
            packet (PacketCarDamageData): The car damage update packet
        """
        for index, car_damage in enumerate(packet.m_carDamageData):
            obj_to_be_updated = self._getObjectByIndexCreate(index)
            obj_to_be_updated.m_tyre_wear = sum(car_damage.m_tyresWear)/len(car_damage.m_tyresWear)
            obj_to_be_updated.m_packet_car_damage = car_damage

    def processSessionHistoryUpdate(self, packet: PacketSessionHistoryData) -> None:
        """Process the session history update packet and update the necessary fields

        Args:
            packet (PacketSessionHistoryData): The session history update packet
        """

        obj_to_be_updated = self._getObjectByIndexCreate(packet.m_carIdx)
        obj_to_be_updated.m_packet_session_history = packet
        if (packet.m_bestLapTimeLapNum > 0) and (packet.m_bestLapTimeLapNum <= packet.m_numLaps):
            obj_to_be_updated.m_best_lap = F1Utils.millisecondsToMinutesSecondsMilliseconds(
                packet.m_lapHistoryData[packet.m_bestLapTimeLapNum-1].m_lapTimeInMS)

        if self._shouldRecomputeFastestLap():
            self._recomputeFastestLap()

    def processTyreSetsUpdate(self, packet: PacketTyreSetsData) -> None:
        """Process the tyre sets update packet and update the necessary fields

        Args:
            packet (PacketTyreSetsData): The tyre sets update packet
        """

        obj_to_be_updated = self._getObjectByIndexCreate(packet.m_carIdx)
        obj_to_be_updated.m_packet_tyre_sets = packet
        obj_to_be_updated.m_tyre_life_remaining_laps = packet.m_tyreSetData[packet.m_fittedIdx].m_lifeSpan

        # Update the tyre set history
        self._updateTyreSetData(driver_data=obj_to_be_updated, fitted_index=packet.m_fittedIdx)

    def getDriverInfoJsonByIndex(self, index: int) -> Optional[Dict[str, Any]]:
        """Get the driver info JSON for the specified index.

        Args:
            index (int): Index of the driver

        Returns:
            Optional[Dict[str, Any]]: Driver info JSON. None if invalid index or data not yet available
        """

        obj_to_be_updated = self.m_driver_data.get(index, None)
        return obj_to_be_updated.toJSON(index) if obj_to_be_updated else None

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_globals = GlobalData()
_driver_data = DriverData()
_globals_lock = threading.Lock()
_driver_data_lock = threading.Lock()

# -------------------------------------- TELEMETRY PACKET HANDLERS -----------------------------------------------------

def processSessionStarted() -> None:
    """
    Reset the data structures when SESSION_STARTED has been received
    """
    with _driver_data_lock:
        _driver_data.clear()
        _driver_data.m_race_completed = False
    with _globals_lock:
        _globals.m_final_classification_received = False # Mark this as False because this is the start of the race

def processSessionUpdate(packet: PacketSessionData) -> bool:
    """Update the data strctures with session data

    Args:
        packet (PacketSessionData): Session data packet

    Returns:
        bool - True if all data needs to be reset
    """

    with _globals_lock:
        return _globals.processSessionUpdate(packet)

def processLapDataUpdate(packet: PacketLapData) -> None:
    """Update the data structures with lap data

    Args:
        packet (PacketLapData): Lap Data packet
    """

    with _driver_data_lock:
        _driver_data.processLapDataUpdate(packet)

def processFastestLapUpdate(packet: PacketEventData) -> None:
    """Update the data structures with the fastest lap

    Args:
        packet (PacketEventData): Fastest lap Event packet
    """

    with _driver_data_lock:
        _driver_data.processFastestLapUpdate(packet.mEventDetails)

def processRetirementEvent(packet: PacketEventData) -> None:
    """Update the data structures with the driver retirement udpate

    Args:
        packet (PacketEventData): Retirement event packet
    """

    with _driver_data_lock:
        _driver_data.processRetirement(packet.mEventDetails)

def processParticipantsUpdate(packet: PacketParticipantsData) -> None:
    """Update the data strucutre with participants information

    Args:
        packet (PacketParticipantsData): The pariticpants info packet
    """

    with _driver_data_lock:
        _driver_data.processParticipantsUpdate(packet)

def processCarTelemetryUpdate(packet: PacketCarTelemetryData) -> None:
    """Update the data structure with the car telemetry information

    Args:
        packet (PacketCarTelemetryData): The car telemetry update packet
    """

    with _driver_data_lock:
        _driver_data.processCarTelemetryUpdate(packet)

def processCarStatusUpdate(packet: PacketCarStatusData) -> None:
    """Update the data structures with car status information

    Args:
        packet (PacketCarStatusData): The car status update packet
    """

    with _driver_data_lock:
        _driver_data.processCarStatusUpdate(packet)

def processFinalClassificationUpdate(packet: PacketFinalClassificationData) -> Dict[str, Any]:
    """Update the data structures with the final classification information
        Returns a JSON object containing all drivers data

    Args:
        packet (PacketFinalClassificationData): The final classification update packet

    Returns:
        Dict[str, Any]: Driver data JSON
    """

    with _driver_data_lock:
        final_json = _driver_data.processFinalClassificationUpdate(packet)
    with _globals_lock:
        _globals.m_final_classification_received = True
    return final_json

def processCarDamageUpdate(packet: PacketCarDamageData):
    """Update the data strucutres with car damage information

    Args:
        packet (PacketCarDamageData): The car damage update packet
    """

    with _driver_data_lock:
        _driver_data.processCarDamageUpdate(packet)

def processSessionHistoryUpdate(packet: PacketSessionHistoryData):
    """Update the data structures with session history information

    Args:
        packet (PacketSessionHistoryData): The session history update packet
    """

    with _driver_data_lock:
        _driver_data.processSessionHistoryUpdate(packet)

def processTyreSetsUpdate(packet: PacketTyreSetsData) -> None:
    """Update the data structures with tyre history information

    Args:
        packet (PacketTyreSetsData): The tyre history update packet
    """

    with _driver_data_lock:
        _driver_data.processTyreSetsUpdate(packet)

# -------------------------------------- WEB API HANDLERS --------------------------------------------------------------

def getGlobals(num_weather_forecast_samples=4) -> Tuple[str, int, str, int, int, str, List[WeatherForecastSample], int, bool]:
    """
    Retrieves the global info regarding the current session

    Parameters:
    - num_weather_forecast_samples (int): Number of weather forecast samples to retrieve (default is 4).

    Returns:
        Tuple[str, int, str, int, int, str, List[WeatherForecastSample]]:
            1: Circuit name (str)
            2: Track temperature (int)
            3: Event type (str)
            4: Total number of laps in the race (int)
            5: Current lap of the player (int or None if player index is None)
            6: Safety car status (str)
            7: List of weather forecast samples (List[WeatherForecastSample])
            8: Pit speed limit (int)
            9: Final Classification Received (bool)
    """
    with _globals_lock:
        with _driver_data_lock: # we need this for current lap
            player_index = _driver_data.m_player_index
            curr_lap = _driver_data.m_driver_data[player_index].m_current_lap if player_index is not None else None
            if _globals.m_weather_forecast_samples is not None:
                weather_forecast_samples = _globals.m_weather_forecast_samples[:num_weather_forecast_samples]
            else:
                weather_forecast_samples = []
            return (_globals.m_circuit, _globals.m_track_temp, _globals.m_event_type,
                        _globals.m_total_laps, curr_lap, _globals.m_safety_car_status,
                            weather_forecast_samples, _globals.m_pit_speed_limit, _globals.m_final_classification_received)

def getDriverData(num_adjacent_cars: Optional[int] = 2) -> Tuple[List[DataPerDriver], str]:
    """Get the driver data for the race. During race, it returns

    Arguments:
        num_adjacent_cars (int, optional): The number of cars adjacent to the driver(above and below, assuming driver
                                                is in the middle of the pack)

    Returns:
        Tuple[List[DataPerDriver], str]: The final list of driver info and the fastest lap time
    """

    # TODO: tidy up
    with _globals_lock:
        is_spectator_mode = _globals.m_is_spectating
        track_length = _globals.m_packet_session.m_trackLength if _globals.m_packet_session else None
    with _driver_data_lock:
        final_list = []
        fastest_lap_time = "---"

        # If the data is not yet available, return default values
        if (_driver_data.m_player_index) is None or (_driver_data.m_num_active_cars is None):
            return final_list, fastest_lap_time

        # Compute the list of positions to be displayed
        player_position = _driver_data.m_driver_data[_driver_data.m_player_index].m_position
        total_cars = _driver_data.m_num_active_cars + \
                (0 if _driver_data.m_num_dnf_cars is None else _driver_data.m_num_dnf_cars)
        if _driver_data.m_race_completed or is_spectator_mode:
            positions = [i for i in range(1, _driver_data.m_num_active_cars+1)]
        else:
            positions = _getAdjacentPositions(player_position, total_cars, num_adjacent_cars)

        # Update the list data
        if _driver_data.m_fastest_index is not None:
            fastest_lap_time = _driver_data.m_driver_data[_driver_data.m_fastest_index].m_best_lap
        for position in positions:
            index, temp_data = _driver_data.getIndexByTrackPosition(position)
            if (index, temp_data) == (None, None):
                return []
            temp_data.m_is_fastest = True if (index == _driver_data.m_fastest_index) else False
            if temp_data.m_ers_perc is not None:
                temp_data.m_ers_perc = F1Utils.floatToStr(temp_data.m_ers_perc) + "%"
            if temp_data.m_tyre_wear is not None:
                temp_data.m_tyre_wear = F1Utils.floatToStr(temp_data.m_tyre_wear) + "%"
            temp_data.m_index = index
            if temp_data.m_telemetry_restrictions is not None:
                temp_data.m_telemetry_restrictions = str(temp_data.m_telemetry_restrictions)
            else:
                temp_data.m_telemetry_restrictions = "N/A"

            if temp_data.m_packet_lap_data and track_length:
                temp_data.m_lap_progress = (temp_data.m_packet_lap_data.m_lapDistance / track_length) * 100.0
            else:
                temp_data.m_lap_progress = None

            # Add this prepped record into the final list
            final_list.append(temp_data)

        if len(final_list) == 0:
            return final_list, fastest_lap_time

        milliseconds_to_seconds_str = lambda ms: ("+" if ms >= 0 else "") + "{:.3f}".format(ms / 1000)
        if is_spectator_mode:
            # just convert the deltas to str
            for data in final_list:
                data.m_delta = milliseconds_to_seconds_str(data.m_delta)
        else:
            # recompute the deltas if not spectator mode
            condition = lambda x: x.m_is_player == True
            player_index = next((index for index, item in enumerate(final_list) if condition(item)), None)

            # case 1: player is in the absolute front of this pack
            if player_index == 0:
                final_list[0].m_delta = "---"
                delta_so_far = 0
                for data in final_list[1:]:
                    delta_so_far += data.m_delta
                    data.m_delta = milliseconds_to_seconds_str(delta_so_far)

            # case 2: player is in the back of the pack
            # Iterate from back to front using reversed need to look at previous car's data for distance ahead
            elif player_index == len(final_list) - 1:
                delta_so_far = 0
                one_car_behind_index = len(final_list)-1
                one_car_behind_delta = final_list[one_car_behind_index].m_delta
                for data in reversed(final_list[:len(final_list)-1]):
                    delta_so_far -= one_car_behind_delta
                    one_car_behind_delta = data.m_delta
                    data.m_delta = milliseconds_to_seconds_str(delta_so_far)
                final_list[len(final_list)-1].m_delta = "---"

            # case 3: player is somewhere in the middle of the pack
            else:

                # First, set the deltas for the cars ahead
                delta_so_far = 0
                one_car_behind_index = player_index
                one_car_behind_delta = final_list[one_car_behind_index].m_delta
                for data in reversed(final_list[:player_index]):
                    delta_so_far -= one_car_behind_delta
                    one_car_behind_delta = data.m_delta
                    data.m_delta = milliseconds_to_seconds_str(delta_so_far)

                # Finally, set the deltas for the cars ahead
                delta_so_far = 0
                for data in final_list[player_index+1:]:
                    delta_so_far += data.m_delta
                    data.m_delta = milliseconds_to_seconds_str(delta_so_far)

                # finally set the delta for the player
                final_list[player_index].m_delta = "---"

        return final_list, fastest_lap_time

def getDriverInfoJsonByIndex(index: int) -> Optional[Dict[str, Any]]:
    """Get the driver info JSON for the given index

    Args:
        index (int): Index of the driver

    Returns:
        Optional[Dict[str, Any]]: The driver info JSON
    """

    with _driver_data_lock:
        return _driver_data.getDriverInfoJsonByIndex(index)

def clearData() -> None:
    """
    Clears all data on demand.
    """
    # All data is cleared when SESSION_STARTED is received. Pretend as if its the same situation
    processSessionStarted()


# -------------------------------------- UTILITIES ---------------------------------------------------------------------

def getEventInfoStr() -> Optional[str]:
    """Returns a string with the following format
            <event-type> _ <circuit> _

    Returns:
        Optional[str]: The event type string, or None if no data is available
    """
    with _globals_lock:
        if _globals.m_event_type and _globals.m_circuit:
            return (_globals.m_event_type + "_" + _globals.m_circuit).replace(' ', '_') + '_'
        else:
            return None

def getPlayerName() -> Optional[str]:
    """Get the player's name.

    Returns:
        Optional[str]: Player's name. None if not found (can be in spectator mode or
                            before PNG has received sufficient data)
    """
    with _driver_data_lock:
        player_data = _driver_data.m_driver_data.get(_driver_data.m_player_index, None)
        return player_data.m_name if player_data else None

def getDriverNameByIndex(index: int) -> str:
    """Get the driver's name for the given index

    Returns:
        str: Driver's name. None if not found (can be before PNG has received sufficient data)
    """
    with _driver_data_lock:
        driver_data = _driver_data.m_driver_data.get(index, None)
        return driver_data.m_name if driver_data else None

def getOvertakeString(overtaking_car_index: int, being_overtaken_index: int) -> str:
    """Returns a CSV-formatted string containing overtake information

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
    with _driver_data_lock:
        if not _driver_data.m_driver_data:
            return None
        overtaking_car_obj = _driver_data.m_driver_data.get(overtaking_car_index, None)
        being_overtaken_car_obj = _driver_data.m_driver_data.get(being_overtaken_index, None)
        if overtaking_car_obj is None or being_overtaken_car_obj is None:
            return None

        # Prepare data for CSV writing
        data = [
            overtaking_car_obj.m_current_lap,
            overtaking_car_obj.m_name,
            being_overtaken_car_obj.m_current_lap,
            being_overtaken_car_obj.m_name
        ]

        # Use CSV writer to handle quoting and escaping
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(data)

        # Get the CSV-formatted string
        csv_string = csv_buffer.getvalue().strip()
        return csv_string


def _getAdjacentPositions(position:int, total_cars:int, num_adjacent_cars:int) -> List[int]:
    """Get the list of positions of the race that are to be returned to the UI.
        It will include the player's position plus/minus num_adjacent_cars

    Args:
        position (int): Track position of the player
        total_cars (int): Total number of cars in the race.
        num_adjacent_cars (int): Number of adjacent cars to be displayed.

    Returns:
        List[int]: The final list of track positions to be displayed
    """
    if not (1 <= position <= total_cars):
        return []

    min_valid_lower_bound = 1
    max_valid_upper_bound = total_cars

    # In time trial, total_cars will be lower than num_adjacent_cars
    if num_adjacent_cars >= total_cars:
        num_adjacent_cars = total_cars
        lower_bound = min_valid_lower_bound
        upper_bound = max_valid_upper_bound

    # GP scenario, lower bound and upper bound are off input position by num_adjacent_cars
    else:
        lower_bound = position - num_adjacent_cars
        upper_bound = position + num_adjacent_cars

    # now correct if lower and upper bounds have become invalid
    if lower_bound < min_valid_lower_bound:
        # lower bound is negative, need to shift the entire window right
        upper_bound += min_valid_lower_bound - lower_bound
        lower_bound = min_valid_lower_bound
    if upper_bound > total_cars:
        # upper bound is greater than limit, need to shift the entire window left
        lower_bound = lower_bound - (upper_bound - total_cars)
        upper_bound = max_valid_upper_bound

    return list(range(lower_bound, upper_bound + 1))

