
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
from typing import Optional, Generator, Tuple, List, Dict, Any
from collections import OrderedDict
import logging
from lib.f1_types import *
from lib.race_analyzer import getFastestTimesJson, getTyreStintRecordsDict
from lib.overtake_analyzer import OvertakeRecord
from lib.tyre_wear_extrapolator import TyreWearExtrapolator, TyreWearPerLap

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
         - m_packet_final_classification (PacketFinalClassificationData): The final classification packet
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
        self.m_packet_session: Optional[PacketSessionData] = None
        self.m_packet_final_classification : Optional[PacketFinalClassificationData] = None

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
            f"m_packet_final_classification={str(self.m_packet_final_classification)}")

    def clear(self) -> None:
        """
        Clear the objects contents.
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
        self.m_packet_final_classification = None
        self.m_packet_session = None

    def processSessionUpdate(self, packet: PacketSessionData) -> bool:
        """Populates the fields from the session data packet
        Args:
            packet (PacketSessionData): The incoming session update packet

        Returns:
            bool - True if all data needs to be reset
        """

        ret_status = False
        if self.m_packet_session and (packet.m_header.m_sessionUID != self.m_packet_session.m_header.m_sessionUID):
            ret_status = True

        self.m_circuit = str(packet.m_trackId)
        self.m_track_temp = packet.m_trackTemperature
        self.m_track_temp = packet.m_trackTemperature
        self.m_event_type = str(packet.m_sessionType)
        self.m_event_type = str(packet.m_sessionType)
        self.m_weather_forecast_samples = packet.m_weatherForecastSamples
        self.m_weather_forecast_samples = packet.m_weatherForecastSamples
        self.m_pit_speed_limit = packet.m_pitSpeedLimit
        self.m_pit_speed_limit = packet.m_pitSpeedLimit
        self.m_total_laps = packet.m_totalLaps
        self.m_packet_session = packet
        return ret_status

class DataPerDriver:
    """
    Class that models the data stored per race driver.

    Attributes:
        m_position (Optional[int]): The current position of the driver in the race.
        m_name (Optional[str]): The name of the driver.
        m_team (Optional[str]): The team to which the driver belongs.
        m_delta_to_car_in_front (Optional[str]): The time difference between the driver and the car in front.
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
        m_tyre_wear_extrapolator (TyreWearExtrapolator): Predicts the tyre wear for upcoming laps
        m_curr_lap_sc_status (PacketSessionData.SafetyCarStatus): The current lap's safety car status

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
            m_tyre_set_key (Optional[str]): The key of the fitted tire set.
            m_end_lap (Optional[int]): The lap at which the tire set was removed.
                                            Must be set using the _computeTyreStintEndLaps method
            m_tyre_wear_history (List[TyreWearPerLap]): The list of tyre wears for the fitted tire set.
        """

        def __init__(self,
                     start_lap: int,
                     index: int,
                     tyre_set_key: Optional[str] = None,
                     initial_tyre_wear: Optional[TyreWearPerLap] = None):
            """Initialize the TyreSetHistoryEntry object. The m_end_lap attribute will be set to None

            Args:
                start_lap (int): The lap at which the tire set was fitted.
                index (int): The index representing the fitted tire set.
                initial_tyre_wear (TyreWearPerLap): The starting tyre wear for this set (can be non 0 in case of reuse)
            """
            self.m_start_lap : int                          = start_lap
            self.m_fitted_index : int                       = index
            self.m_tyre_set_key : Optional[str]             = tyre_set_key
            self.m_end_lap : int                            = None
            if initial_tyre_wear:
                self.m_tyre_wear_history : List[TyreWearPerLap] = [initial_tyre_wear]
            else:
                self.m_tyre_wear_history : List[TyreWearPerLap] = []

        def getTyreWearJSONList(self):
            """Dump this object into JSON

            Returns:
                List[Dict[str, Any]]: The JSON dump
            """

            return [entry.toJSON() for entry in self.m_tyre_wear_history]

    class PerLapHistoryEntry:
        """
        Class that captures one lap's backup data

        Attributes:
            m_car_damage_packet (CarDamageData): The Car damage packet
            m_car_status_packet (CarStatusData): The Car Status packet
            m_sc_status (PacketSessionData.SafetyCarStatus): The lap's safety car status
        """

        def __init__(self,
                     car_damage : CarDamageData,
                     car_status : CarStatusData,
                     sc_status  : PacketSessionData.SafetyCarStatus):
            """Init the backup entry object

            Args:
                car_damage (CarDamageData): The Car damage packet
                car_status (CarStatusData): The Car Status packet
            """

            self.m_car_damage_packet: Optional[CarDamageData] = car_damage
            self.m_car_status_packet: Optional[CarStatusData] = car_status
            self.m_sc_status: Optional[PacketSessionData.SafetyCarStatus] = sc_status

        def toJSON(self, lap_number : int) -> Dict[str, Any]:
            """Dump this object into JSON

            Args:
                lap_number (int): The lap number corresponding to this history item

            Returns:
                Dict[str, Any]: The JSON dump
            """

            return {
                "lap-number" : lap_number,
                "car-damage-data" : self.m_car_damage_packet.toJSON() if self.m_car_damage_packet else None,
                "car-status-data" : self.m_car_status_packet.toJSON() if self.m_car_status_packet else None,
            }

    def __init__(self, total_laps):
        """
        Init the data per driver fields
        """

        self.m_position: Optional[int] = None
        self.m_name: Optional[str] = None
        self.m_team: Optional[str] = None
        self.m_delta_to_car_in_front: Optional[int] = None
        self.m_delta_to_leader: Optional[int] = None
        self.m_ers_perc: Optional[float] = None
        self.m_best_lap_str: Optional[str] = None
        self.m_best_lap_ms: Optional[str] = None
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
        self.m_tyre_wear_extrapolator: TyreWearExtrapolator = TyreWearExtrapolator([], total_laps=total_laps)
        self.m_curr_lap_sc_status: Optional[PacketSessionData.SafetyCarStatus] = None

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

    def toJSON(self,
               index: Optional[int] = None,
               include_tyre_wear_prediction : Optional[bool] = False) -> Dict[str, Any]:
        """Get a JSON representation of this DataPerDriver object

        Args:
            index (int): The index number. Defaults to None.
            include_tyre_wear_prediction (Optional[bool]): Whether to include the tyre wear prediction

        Returns:
            Dict[str, Any]: The JSON dict
        """
        final_json = {}

        # Add the primary data
        if index is not None:
            final_json["index"] = index
        final_json["is-player"] = self.m_is_player
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
        self._computeTyreStintEndLaps()
        final_json["tyre-set-history"]= self._getTyreSetHistoryJSON()

        # Insert the per lap backup
        final_json["per-lap-info"] = []
        for lap_number, backup_entry in self._getNextLapBackup():
            final_json["per-lap-info"].append(backup_entry.toJSON(lap_number))

        if include_tyre_wear_prediction:
            # final_json["tyre-wear-predictions"] = self.getTyrePredictionsJSONList()
            pass # TODO - implement

        # Return this fully prepped JSON
        return final_json

    def getTyrePredictionsJSONList(self, next_pit_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get a JSON list with the tyre wear predictions

        Args:
            next_pit_window (Optional[int], optional): The next pit window lap number.
                If None, then returns the predictions for final lap and half way through between current and final lap

        Returns:
            List[Dict[str, Any]]: List of JSON objects, each containing tyre wear predictions for a specific lap
        """

        if self.m_tyre_wear_extrapolator.isDataSufficient():
            if next_pit_window is None or (next_pit_window == 0) or (next_pit_window < self.m_current_lap):
                # Lets return the lap midway between current lap and final lap
                next_pit_window = (self.m_current_lap + self.m_tyre_wear_extrapolator.total_laps) // 2
            if next_pit_window == self.m_tyre_wear_extrapolator.total_laps:
                # We are already in the final lap, so return the final prediction
                return [self.m_tyre_wear_extrapolator.getTyreWearPrediction().toJSON()]
            else:
                # Return the tyre wear extrapolator predictions for the next pit window and final lap
                return [
                    self.m_tyre_wear_extrapolator.getTyreWearPrediction(next_pit_window).toJSON(),
                    self.m_tyre_wear_extrapolator.getTyreWearPrediction().toJSON()
                ]
        else:
            # Data unavailable, return empty list
            return []

    def _getTyreSetHistoryJSON(self) -> List[Dict[str, Any]]:
        """Get the list of tyre sets used in JSON format

        Returns:
            JSON list: JSON list containing multiple JSON objects, each representing one set of tyres used, in order.
        """

        tyre_set_history = []
        for entry in self.m_tyre_set_history:
            is_index_valid = 0 < entry.m_fitted_index < len(self.m_packet_tyre_sets.m_tyreSetData)
            tyre_set_history.append({
                'start-lap' : entry.m_start_lap,
                'end-lap' : entry.m_end_lap,
                'stint-length' : (entry.m_end_lap+1-entry.m_start_lap),
                'fitted-index' : entry.m_fitted_index,
                'tyre-set-data' : self.m_packet_tyre_sets.m_tyreSetData[entry.m_fitted_index].toJSON() \
                                    if is_index_valid else None,
                'tyre-wear-history' : entry.getTyreWearJSONList(),
                'tyre-set-key' : entry.m_tyre_set_key
            })

        return tyre_set_history

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
                'front-right-wear': self.m_per_lap_backups[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                'front-left-wear': self.m_per_lap_backups[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                'rear-right-wear': self.m_per_lap_backups[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                'rear-left-wear': self.m_per_lap_backups[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
            })
        for lap_number in range_of_laps:
            if lap_number in self.m_per_lap_backups:
                car_damage_data = self.m_per_lap_backups[lap_number].m_car_damage_packet
                if car_damage_data:
                    tyre_wear_history.append({
                        'lap-number': lap_number,
                        'front-right-wear': car_damage_data.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                        'front-left-wear': car_damage_data.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                        'rear-right-wear': car_damage_data.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                        'rear-left-wear': car_damage_data.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                    })
                else:
                    logging.debug('car damage data not available for lap %d driver %s'
                                    %(lap_number, self.m_name))
            else:
                logging.debug('per lap backup not available for lap %d driver %s'
                                %(lap_number, self.m_name))
        return tyre_wear_history

    def onLapChange(self,
        old_lap_number: int) -> None:
        """
        Perform backup for the given lap change.

        Args:
            old_lap_number (int): The old lap number.
        """

        # Check if the old lap number is already present in the backups (lap already processed)
        if old_lap_number in self.m_per_lap_backups:
            return

        # Store the backup data for the old lap
        self.m_per_lap_backups[old_lap_number] = DataPerDriver.PerLapHistoryEntry(
            car_damage=self.m_packet_car_damage,
            car_status=self.m_packet_car_status,
            sc_status=self.m_curr_lap_sc_status
        )

        # Add the tyre wear data into the tyre stint history
        if old_lap_number > 0:
            self.m_tyre_set_history[-1].m_tyre_wear_history.append(TyreWearPerLap(
                lap_number=old_lap_number,
                fl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                fr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                rl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                rr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                is_racing_lap=True,
                desc="end of lap " + str(old_lap_number) + " backup"
            ))

        # Add the tyre wear data into the extrapolator
        tyre_set_id = self._getCurrentTyreSetID()
        if tyre_set_id:
            # Clear the extrapolator if tyre set has been changed
            if self._hasTyreSetChanged():
                logging.debug("Tyre set change detected for " + self.m_name)
                self.m_tyre_wear_extrapolator.clear()
            self.m_tyre_wear_extrapolator.updateDataLap(TyreWearPerLap(
                lap_number=old_lap_number,
                fl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                fr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                rl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                rr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                is_racing_lap=True,
                desc=self._getCurrentTyreSetID()
            ))

    def _hasTyreSetChanged(self) -> bool:
        """Check if the driver has changed tyre sets (has pitted)

        Returns:
            bool: True if this lap has a changed tyre set
        """

        if len(self.m_tyre_wear_extrapolator.m_initial_data) > 0:
            return self.m_tyre_wear_extrapolator.m_initial_data[-1].m_desc != self._getCurrentTyreSetID()
        else:
            return False

    def isZerothLapBackupDataAvailable(self) -> bool:
        """
        Checks if zeroth lap backup data is available.

        Returns:
            bool - True if zeroth lap backup data is available
        """

        return True if \
            self.m_packet_car_damage and \
            self.m_packet_car_status and \
            self.m_packet_tyre_sets \
        else False

    def updateTyreSetData(self, fitted_index: int) -> None:
        """Update the current tyre set in the history list, if required.
               NOTE: The tyre history is ignored if the player has disabled telemetry

        Args:
            fitted_index (int): The fitted tyre set index
        """

        # fuck those anti telemetry cunts
        if self.m_telemetry_restrictions != ParticipantData.TelemetrySetting.PUBLIC:
            return

        # This can happen if tyre sets packets arrives before lap data packet
        if self.m_current_lap is not None:
            if len(self.m_tyre_set_history) == 0:
                if 0 in self.m_per_lap_backups:
                    # Start of race, enter the tyre wear data along with starting value
                    initial_tyre_wear = TyreWearPerLap(
                        lap_number=0,
                        fl_tyre_wear=self.m_per_lap_backups[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                        fr_tyre_wear=self.m_per_lap_backups[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                        rl_tyre_wear=self.m_per_lap_backups[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                        rr_tyre_wear=self.m_per_lap_backups[0].m_car_damage_packet.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                        is_racing_lap=True,
                        desc="end of zeroth lap data point"
                    )
                    self.m_tyre_set_history.append(DataPerDriver.TyreSetHistoryEntry(
                                                start_lap=self.m_current_lap,
                                                index=fitted_index,
                                                initial_tyre_wear=initial_tyre_wear,
                                                tyre_set_key=self.m_packet_tyre_sets.getFittedTyreSetKey()
                    ))
            else:
                if fitted_index != self.m_tyre_set_history[-1].m_fitted_index:
                    lap_number = self.m_current_lap - 1
                    # create a new tyre set entry with initial data.
                    initial_tyre_wear = TyreWearPerLap(
                        lap_number=lap_number,
                        fl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                        fr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                        rl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                        rr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                        is_racing_lap=True,
                        desc="tyre set change detected. key=" + str(self.m_packet_tyre_sets.getFittedTyreSetKey())
                    )
                    self.m_tyre_set_history.append(DataPerDriver.TyreSetHistoryEntry(
                                                start_lap=lap_number,
                                                index=fitted_index,
                                                initial_tyre_wear=initial_tyre_wear,
                                                tyre_set_key=self.m_packet_tyre_sets.getFittedTyreSetKey()
                    ))

                    # Tyre set change detected. clear the extrapolation data
                    self.m_tyre_wear_extrapolator.clear()
                    self.m_tyre_wear_extrapolator.updateDataLap(initial_tyre_wear)

    def _getCurrentTyreSetID(self) -> Optional[str]:
        """Get the unique ID key for the currently equipped tyre set

        Returns:
            Optional[str]: The tyre set key
        """

        return self.m_packet_tyre_sets.getFittedTyreSetKey() if self.m_packet_tyre_sets else None

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
            # self._cleanTyreStintHistory()
            for i in range(len(self.m_tyre_set_history) - 1):
                current_stint = self.m_tyre_set_history[i]
                next_stint = self.m_tyre_set_history[i + 1]
                current_stint.m_end_lap = next_stint.m_start_lap

            # For the last tyre stint, get end lap num from session history
            self.m_tyre_set_history[-1].m_end_lap = self.m_packet_session_history.m_numLaps

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
        m_total_laps (int): The total number of laps in this race
        m_ideal_pit_stop_window (int): The ideal pit stop window for the player, according to the selected strategy
    """

    def __init__(self):
        """
        Initialize the DriverData object.
        """
        self.m_driver_data: Dict[int, DataPerDriver] = {}
        self.m_player_index: Optional[int] = None
        self.m_fastest_index: Optional[int] = None
        self.m_num_active_cars: Optional[int] = None
        self.m_num_dnf_cars: Optional[int] = None
        self.m_race_completed: Optional[bool] = None
        self.m_final_json: Dict[str, Any] = None
        self.m_is_player_dnf : Optional[bool] = None
        self.m_total_laps : Optional[int] = None
        self.m_ideal_pit_stop_window : Optional[int] = None

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
        self.m_is_player_dnf = None
        self.m_total_laps = None
        self.m_ideal_pit_stop_window = None

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
            self.m_driver_data[index] = DataPerDriver(self.m_total_laps)
        return self.m_driver_data[index]

    def _recomputeFastestLap(self) -> None:
        """
        Recomputes the fastest lap and updates the necessary fields
        """

        self.m_fastest_index = None
        fastest_time_ms = 500000000000 # cant be slower than this, right?
        for index, driver_data in self.m_driver_data.items():
            if driver_data.m_best_lap_str is not None:
                if driver_data.m_best_lap_ms > 0 and driver_data.m_best_lap_ms < fastest_time_ms:
                    fastest_time_ms = driver_data.m_best_lap_ms
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
        if driver_data.m_best_lap_str is None:
            return False

        # True if fastest lap has not been determined yet
        if self.m_fastest_index is None:
            return True

        # Determine this guy's best lap
        driver_best_lap_ms = None
        if driver_data.m_packet_session_history:
            # First option, session history data
            best_lap_index: int = driver_data.m_packet_session_history.m_bestLapTimeLapNum - 1
            if 0 <= best_lap_index < len(driver_data.m_packet_session_history.m_lapHistoryData):
                if driver_data.m_packet_session_history.m_lapHistoryData[best_lap_index].isLapValid():
                    driver_best_lap_ms = driver_data.m_packet_session_history.m_lapHistoryData[best_lap_index].m_lapTimeInMS
        if driver_best_lap_ms is None:
            # Second option, from the object itself
            driver_best_lap_ms = driver_data.m_best_lap_ms

        # False if this guy does not have a valid best lap
        if driver_data.m_best_lap_ms is None:
            return False

        # Check if this guy's lap is faster than the best lap
        if self.m_driver_data[self.m_fastest_index].m_best_lap_ms > driver_best_lap_ms:
            return True
        else:
            return False

    def processSessionUpdate(self, packet: PacketSessionData) -> None:
        """Process the Session Update packet. Update the total laps and ideal pit window for the player

        Args:
            packet (PacketSessionData): The incoming parsed packet object
        """

        self.m_total_laps = packet.m_totalLaps
        self.m_ideal_pit_stop_window = packet.m_pitStopWindowIdealLap

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
            obj_to_be_updated.m_delta_to_car_in_front = lap_data.m_deltaToCarInFrontInMS
            obj_to_be_updated.m_delta_to_leader = lap_data.m_deltaToRaceLeaderInMS
            obj_to_be_updated.m_penalties = self._getPenaltyString(lap_data.m_penalties,
                                lap_data.m_numUnservedDriveThroughPens, lap_data.m_numUnservedStopGoPens)

            # Update the per lap backup data structure if lap info is available
            if (obj_to_be_updated.m_current_lap is not None):
                if (obj_to_be_updated.m_current_lap == 1):
                    if (obj_to_be_updated.isZerothLapBackupDataAvailable()):
                        # Enter data for the zeroth lap
                        obj_to_be_updated.onLapChange(
                            old_lap_number=0)

                # Now, add shit only if there is change (this should handle lap 1 to lap 2 transition)
                if (obj_to_be_updated.m_current_lap != lap_data.m_currentLapNum):
                    obj_to_be_updated.onLapChange(
                        old_lap_number=obj_to_be_updated.m_current_lap)

            # Now, update the current lap number and other shit
            obj_to_be_updated.m_current_lap =  lap_data.m_currentLapNum
            obj_to_be_updated.m_is_pitting = True if lap_data.m_pitStatus in \
                    [LapData.PitStatus.PITTING, LapData.PitStatus.IN_PIT_AREA] else False
            obj_to_be_updated.m_num_pitstops = lap_data.m_numPitStops
            obj_to_be_updated.m_dnf_status_code = result_str_map.get(lap_data.m_resultStatus, "")
            # If the player is retired, update the bool variable
            if index == self.m_player_index and len(obj_to_be_updated.m_dnf_status_code) > 0:
                self.m_is_player_dnf = True

            # Save a copy of the packet
            obj_to_be_updated.m_packet_lap_data = lap_data

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

        obj_to_be_updated = self._getObjectByIndexCreate(packet.vehicleIdx)
        obj_to_be_updated.m_best_lap_str = F1Utils.floatSecondsToMinutesSecondsMilliseconds(packet.lapTime)
        obj_to_be_updated.m_best_lap_ms = packet.lapTime
        self.m_fastest_index = packet.vehicleIdx

    def processRetirement(self, packet: PacketEventData.Retirement) -> None:
        """Process the retirement update event notification

        Args:
            packet (PacketEventData.Retirement): The retirement update object
        """

        obj_to_be_updated = self._getObjectByIndexCreate(packet.vehicleIdx)
        obj_to_be_updated.m_dnf_status_code = True

        if packet.vehicleIdx == self.m_player_index:
            self.m_is_player_dnf = True

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
            obj_to_be_updated.m_ers_perc = (car_status_data.m_ersStoreEnergy/CarStatusData.MAX_ERS_STORE_ENERGY) * 100.0
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

        final_json = packet.toJSON()
        for index, data in enumerate(packet.m_classificationData):
            obj_to_be_updated = self.m_driver_data.get(index, None)
            # Perform the final backup
            obj_to_be_updated.onLapChange(
                old_lap_number=data.m_numLaps)
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
            obj_to_be_updated.m_best_lap_ms = packet.m_lapHistoryData[packet.m_bestLapTimeLapNum-1].m_lapTimeInMS
            obj_to_be_updated.m_best_lap_str = F1Utils.millisecondsToMinutesSecondsMilliseconds(
                obj_to_be_updated.m_best_lap_ms)

        # if self._shouldRecomputeFastestLap():
        if self._shouldRecomputeFastestLap(obj_to_be_updated):
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
        obj_to_be_updated.updateTyreSetData(fitted_index=packet.m_fittedIdx)

    def getDriverInfoJsonByIndex(self, index: int) -> Optional[Dict[str, Any]]:
        """Get the driver info JSON for the specified index.

        Args:
            index (int): Index of the driver

        Returns:
            Optional[Dict[str, Any]]: Driver info JSON. None if invalid index or data not yet available
        """

        obj_to_be_updated = self.m_driver_data.get(index, None)
        return obj_to_be_updated.toJSON(index) if obj_to_be_updated else None

    def getRaceInfoJSON(self) -> Dict[str, Any]:
        """Get the race info JSON.

        Returns:
            Dict[str, Any]: Race info JSON
        """

        if self.m_race_completed and self.m_final_json:
            return self.m_final_json
        else:
            final_json = {}
            final_json["classification-data"] = self._getClassificationDataListJSON()
            return final_json

    def _getClassificationDataListJSON(self):
        """
        Return a list of dictionaries containing index, driver name, position, and participant data.
        """

        return [driver_data.toJSON(index) for index, driver_data in self.m_driver_data.items()]

class CustomMarkerEntry:
    """Class representing the data points related to a custom time marker.
    """

    def __init__(self,
        track: str,
        event_type: str,
        lap: int,
        sector: LapData.Sector,
        curr_lap_time: str,
        curr_lap_perc: str):
        """
        Initializes a CustomMarkerEntry instance.

        Parameters:
            - track: A string representing the track name.
            - event_type: A string representing the type of event.
            - lap: An integer representing the lap number.
            - sector: An instance of LapData.Sector enum representing the sector.
            - curr_lap_time: A string representing the current lap time.
            - curr_lap_perc: A string representing the current lap percentage.
        """

        self.m_track: str               = track
        self.m_event_type: str          = event_type
        self.m_lap: int                 = lap
        self.m_sector: LapData.Sector   = sector
        self.m_curr_lap_time: str       = curr_lap_time
        self.m_curr_lap_percent: str    = curr_lap_perc

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert CustomMarkerEntry instance to a JSON-compatible dictionary.

        Returns:
            A dictionary representation of the CustomMarkerEntry.
        """
        return {
            "track": self.m_track,
            "event-type": self.m_event_type,
            "lap": str(self.m_lap),
            "sector": str(self.m_sector),
            "curr-lap-time": self.m_curr_lap_time,
            "curr-lap-percentage": self.m_curr_lap_percent
        }

    def toCSV(self) -> str:
        """
        Convert CustomMarkerEntry instance to a CSV string.

        Returns:
            A CSV string representation of the CustomMarkerEntry.
        """
        return \
            f"{self.m_track}, " \
            f"{self.m_event_type}, " \
            f"{str(self.m_lap)}, " \
            f"{str(self.m_sector)}, " \
            f"{self.m_curr_lap_time}, " \
            f"{self.m_curr_lap_percent}"

    def __str__(self):
        """
        Return string representation of CustomMarkerEntry instance.

        Returns:
            A string representation of the CustomMarkerEntry instance.
        """
        return self.toCSV()

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
        _driver_data.setRaceOngoing()
    with _globals_lock:
        _globals.m_packet_final_classification = None # Clear this because this is the start of the race

def processSessionUpdate(packet: PacketSessionData) -> bool:
    """Update the data strctures with session data
    Args:
        packet (PacketSessionData): Session data packet

    Returns:
        bool - True if all data needs to be reset
    """

    with _driver_data_lock:
        _driver_data.processSessionUpdate(packet)
    with _globals_lock:
        return _globals.processSessionUpdate(packet)

def processLapDataUpdate(packet: PacketLapData) -> None:
    """Update the data structures with lap data

    Args:
        packet (PacketLapData): Lap Data packet
    """

    with _driver_data_lock:
        if _driver_data.m_total_laps is not None:
            _driver_data.processLapDataUpdate(packet)
            _driver_data.setRaceOngoing()

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
        _driver_data.setRaceOngoing()

def processCarStatusUpdate(packet: PacketCarStatusData) -> None:
    """Update the data structures with car status information

    Args:
        packet (PacketCarStatusData): The car status update packet
    """

    with _driver_data_lock:
        _driver_data.processCarStatusUpdate(packet)
        _driver_data.setRaceOngoing()

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
        _driver_data.setRaceCompleted()
    with _globals_lock:
        final_json["session-info"] = _globals.m_packet_session.toJSON() if _globals.m_packet_session else None
        _globals.m_packet_final_classification = packet
    return final_json

def processCarDamageUpdate(packet: PacketCarDamageData):
    """Update the data strucutres with car damage information

    Args:
        packet (PacketCarDamageData): The car damage update packet
    """

    with _driver_data_lock:
        _driver_data.processCarDamageUpdate(packet)
        _driver_data.setRaceOngoing()

def processSessionHistoryUpdate(packet: PacketSessionHistoryData):
    """Update the data structures with session history information

    Args:
        packet (PacketSessionHistoryData): The session history update packet
    """

    with _driver_data_lock:
        _driver_data.processSessionHistoryUpdate(packet)
        _driver_data.setRaceOngoing()

def processTyreSetsUpdate(packet: PacketTyreSetsData) -> None:
    """Update the data structures with tyre history information

    Args:
        packet (PacketTyreSetsData): The tyre history update packet
    """

    with _driver_data_lock:
        _driver_data.processTyreSetsUpdate(packet)
        _driver_data.setRaceOngoing()

# -------------------------------------- WEB API HANDLERS --------------------------------------------------------------

def getGlobals(num_weather_forecast_samples=None) -> \
    Tuple[str, int, str, int, int, str, List[WeatherForecastSample], int, bool]:
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
    with _driver_data_lock: # we need this for current lap
        player_index = _driver_data.m_player_index
        curr_lap = _driver_data.m_driver_data[player_index].m_current_lap if player_index is not None else None
    with _globals_lock:
        if _globals.m_weather_forecast_samples is not None:
            if num_weather_forecast_samples is None:
                weather_forecast_samples = _globals.m_weather_forecast_samples[:num_weather_forecast_samples]
            else:
                weather_forecast_samples = _globals.m_weather_forecast_samples
        else:
            weather_forecast_samples = []
        return (_globals.m_circuit, _globals.m_track_temp, _globals.m_event_type,
                    _globals.m_total_laps, curr_lap, _globals.m_safety_car_status,
                        weather_forecast_samples, _globals.m_pit_speed_limit,
                            (True if _globals.m_packet_final_classification else False))

def getDriverData(num_adjacent_cars: Optional[int] = 2) -> Tuple[List[DataPerDriver], str]:
    """Get the driver data for the race. During race, it returns

    Arguments:
        num_adjacent_cars (int, optional): The number of cars adjacent to the driver(above and below, assuming driver
                                                is in the middle of the pack)

    Returns:
        Tuple[List[DataPerDriver], str]: The final list of driver info and the fastest lap time
    """

    with _globals_lock:
        is_spectator_mode = _globals.m_is_spectating
        track_length = _globals.m_packet_session.m_trackLength if _globals.m_packet_session else None

    with _driver_data_lock:
        final_list : List[DataPerDriver] = []
        fastest_lap_time = "---"

        # If the data is not yet available, return default values
        if (_driver_data.m_player_index is None) or (_driver_data.m_num_active_cars is None):
            return final_list, fastest_lap_time

        # Compute the list of positions to be displayed
        player_position = _driver_data.m_driver_data[_driver_data.m_player_index].m_position
        total_cars = _driver_data.m_num_active_cars + \
                (0 if _driver_data.m_num_dnf_cars is None else _driver_data.m_num_dnf_cars)
        if _driver_data.m_race_completed or is_spectator_mode or _driver_data.m_is_player_dnf:
            positions = [i for i in range(1, _driver_data.m_num_active_cars+1)]
        else:
            positions = _getAdjacentPositions(player_position, total_cars, num_adjacent_cars)

        # Update the list data
        if _driver_data.m_fastest_index is not None:
            fastest_lap_time = _driver_data.m_driver_data[_driver_data.m_fastest_index].m_best_lap_str
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

            if temp_data.m_packet_lap_data:
                temp_data.m_corner_cutting_warnings = temp_data.m_packet_lap_data.m_cornerCuttingWarnings
                temp_data.m_time_penalties = temp_data.m_packet_lap_data.m_penalties
                temp_data.m_num_dt = temp_data.m_packet_lap_data.m_numUnservedDriveThroughPens
                temp_data.m_num_sg = temp_data.m_packet_lap_data.m_numUnservedStopGoPens
                if track_length:
                    temp_data.m_lap_progress = (temp_data.m_packet_lap_data.m_lapDistance / track_length) * 100.0
                else:
                    temp_data.m_lap_progress = None
            else:
                temp_data.m_lap_progress = None
                temp_data.m_corner_cutting_warnings = None
                temp_data.m_time_penalties = None
                temp_data.m_num_dt = None
                temp_data.m_num_sg = None

            if temp_data.m_is_player:
                temp_data.m_ideal_pit_stop_window = _driver_data.m_ideal_pit_stop_window
            else:
                temp_data.m_ideal_pit_stop_window = None

            # Add this prepped record into the final list
            final_list.append(temp_data)

        if len(final_list) == 0:
            return final_list, fastest_lap_time

        else:
            return _recomputeDeltas(final_list, is_spectator_mode), fastest_lap_time

def getPlayerDriverData() -> Tuple[DataPerDriver, str]:
    """Same as getDriverData, but only returns one row
    Returns:
        Tuple[DataPerDriver, str]: _description_
    """
    with _globals_lock:
        track_length = _globals.m_packet_session.m_trackLength if _globals.m_packet_session else None
    with _driver_data_lock:
        fastest_lap_time = "---"

        # If the data is not yet available, return default values
        player_index = _driver_data.m_player_index
        if (player_index is None) or (_driver_data.m_num_active_cars is None):
            return None, fastest_lap_time

        milliseconds_to_seconds_str = lambda ms: ("+" if ms >= 0 else "") + "{:.3f}".format(ms / 1000)

        final_obj = copy.deepcopy(_driver_data.m_driver_data[player_index])
        final_obj.m_is_fastest = True if (player_index == _driver_data.m_fastest_index) else False
        if final_obj.m_ers_perc is not None:
            final_obj.m_ers_perc = F1Utils.floatToStr(final_obj.m_ers_perc) + "%"
        if final_obj.m_tyre_wear is not None:
            final_obj.m_tyre_wear = F1Utils.floatToStr(final_obj.m_tyre_wear) + "%"
        final_obj.m_index = player_index
        if final_obj.m_telemetry_restrictions is not None:
            final_obj.m_telemetry_restrictions = str(final_obj.m_telemetry_restrictions)
        else:
            final_obj.m_telemetry_restrictions = "N/A"
        if final_obj.m_packet_lap_data:
            final_obj.m_corner_cutting_warnings = final_obj.m_packet_lap_data.m_cornerCuttingWarnings
            final_obj.m_delta_to_car_in_front = milliseconds_to_seconds_str(final_obj.m_packet_lap_data.m_deltaToCarInFrontInMS)
            if track_length:
                final_obj.m_lap_progress = (final_obj.m_packet_lap_data.m_lapDistance / track_length) * 100.0
        else:
            final_obj.m_lap_progress = None
            final_obj.m_corner_cutting_warnings = None

        return final_obj, fastest_lap_time

def getDriverInfoJsonByIndex(index: int) -> Optional[Dict[str, Any]]:
    """Get the driver info JSON for the given index

    Args:
        index (int): Index of the driver

    Returns:
        Optional[Dict[str, Any]]: The driver info JSON
    """

    with _driver_data_lock:
        return _driver_data.getDriverInfoJsonByIndex(index)

def getRaceInfo() -> Dict[str, Any]:
    """
    Returns the race information as a dictionary with string keys and any values.
    """

    with _driver_data_lock:
        final_json = _driver_data.getRaceInfoJSON()
    if "records" not in final_json:
        final_json['records'] = {
            'fastest' : getFastestTimesJson(final_json),
            'tyre-stats' : getTyreStintRecordsDict(final_json)
        }
    return final_json


# -------------------------------------- UTILITIES ---------------------------------------------------------------------

def getEventInfoStr() -> Optional[str]:
    """Returns a string with the following format
            <event-type> _ <circuit> _

    Returns:
        Optional[str]: The event type string (ends with an underscore), or None if no data is available
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

def getOvertakeObj(overtaking_car_index: int, being_overtaken_index: int) -> Optional[OvertakeRecord]:
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
        if overtaking_car_obj.m_name is None or \
            overtaking_car_obj.m_current_lap is None or \
                being_overtaken_car_obj.m_name is None or \
                    being_overtaken_car_obj.m_current_lap is None:
            return None
        return OvertakeRecord(
            overtaking_driver_name=overtaking_car_obj.m_name,
            overtaking_driver_lap=overtaking_car_obj.m_current_lap,
            overtaken_driver_name=being_overtaken_car_obj.m_name,
            overtaken_driver_lap=being_overtaken_car_obj.m_current_lap,
        )

def getPlayerRecordedEventCsvStr(add_to_queue: bool = False) -> Optional[str]:
    """
    Retrieves the recorded event string for the player.

    Arguments:
        add_to_queue (bool) - Whether the data must be added to the event queue to be sent to the UI

    Returns:
        Optional[str]: The recorded event string for the player in CSV format , or None if no player data is available.
            (<track>,<event-type>,<lap-num>,<sector-num>,<curr-lap-time>,<curr-lap-percent>)
    """

    def _getPlayerRecordedEventCsvStr() -> Optional[str]:
        with _driver_data_lock:
            player_data = _driver_data.m_driver_data.get(_driver_data.m_player_index, None)
            if player_data:
                # CSV string - <track>,<event-type>,<lap-num>,<sector-num>
                lap_num = player_data.m_current_lap
                sector = player_data.m_packet_lap_data.m_sector
                curr_lap_time = F1Utils.millisecondsToMinutesSecondsMilliseconds(
                    player_data.m_packet_lap_data.m_currentLapTimeInMS)
                curr_lap_dist = player_data.m_packet_lap_data.m_lapDistance
            else:
                return None

        with _globals_lock:
            if _globals.m_circuit is not None and _globals.m_event_type is not None:
                curr_lap_percent = F1Utils.floatToStr(
                    float(curr_lap_dist)/float(_globals.m_packet_session.m_trackLength) * 100.0) + "%"
                return \
                    f"{_globals.m_circuit}, " \
                    f"{_globals.m_event_type}, " \
                    f"{str(lap_num)}, " \
                    f"{str(sector)}, " \
                    f"{curr_lap_time}, " \
                    f"{curr_lap_percent}"
            else:
                return None

    return _getPlayerRecordedEventCsvStr()

def getCustomMarkerEntryObj(add_to_queue: bool = False) -> Optional[CustomMarkerEntry]:
    """
    Retrieves the custom marker entry object for the player.

    Arguments:
        add_to_queue (bool) - Whether the data must be added to the event queue to be sent to the UI

    Returns:
        CustomMarkerEntry: The custom marker entry object for the player. None if any data points is not available
    """

    with _driver_data_lock:
        player_data = _driver_data.m_driver_data.get(_driver_data.m_player_index, None)
        if player_data:
            # CSV string - <track>,<event-type>,<lap-num>,<sector-num>
            lap_num = player_data.m_current_lap
            sector = player_data.m_packet_lap_data.m_sector
            curr_lap_time = F1Utils.millisecondsToMinutesSecondsMilliseconds(
                player_data.m_packet_lap_data.m_currentLapTimeInMS)
            curr_lap_dist = player_data.m_packet_lap_data.m_lapDistance
        else:
            lap_num = None
            sector = None
            curr_lap_time = None
            curr_lap_dist = None

    with _globals_lock:
        if _globals.m_circuit is not None and _globals.m_event_type is not None:
            track = _globals.m_circuit
            event_type = _globals.m_event_type
            if curr_lap_dist is not None:
                curr_lap_percent = F1Utils.floatToStr(
                    float(curr_lap_dist)/float(_globals.m_packet_session.m_trackLength) * 100.0) + "%"
            else:
                curr_lap_percent = None
        else:
            track = None
            event_type = None
            curr_lap_percent = None

    mandatory_vars = [track, event_type, lap_num, sector, curr_lap_time, curr_lap_percent]
    if any(var is None for var in mandatory_vars):
        return None
    else:
        return CustomMarkerEntry(
            track=track,
            event_type=event_type,
            lap=lap_num,
            sector=sector,
            curr_lap_time=curr_lap_time,
            curr_lap_perc=curr_lap_percent
        )


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

def _recomputeDeltas(driver_list : List[DataPerDriver], is_spectator_mode : bool) -> List[DataPerDriver]:
    """Recompute the deltas for the list of driver data relative to the player

    Args:
        driver_list (List[DataPerDriver]): The list of driver data
        is_spectator_mode (bool) : True if the game is in spectator mode

    Returns:
        List[DataPerDriver]: The list of driver data with deltas
    """

    driver_list[0].m_delta_to_car_in_front = "---"
    milliseconds_to_seconds_str = lambda ms: ("+" if ms >= 0 else "") + "{:.3f}".format(ms / 1000)
    if is_spectator_mode:
        # just convert the deltas to str
        for data in driver_list:
            data.m_delta_to_car_in_front = milliseconds_to_seconds_str(data.m_delta_to_car_in_front)
    else:
        # recompute the deltas if not spectator mode
        condition = lambda x: x.m_is_player == True
        player_index = next((index for index, item in enumerate(driver_list) if condition(item)), None)

        # case 1: player is in the absolute front of this pack
        if player_index == 0:
            driver_list[0].m_delta_to_car_in_front = "---"
            delta_so_far = 0
            for data in driver_list[1:]:
                delta_so_far += data.m_delta_to_car_in_front
                data.m_delta_to_car_in_front = milliseconds_to_seconds_str(delta_so_far)

        # case 2: player is in the back of the pack
        # Iterate from back to front using reversed need to look at previous car's data for distance ahead
        elif player_index == len(driver_list) - 1:
            delta_so_far = 0
            one_car_behind_index = len(driver_list)-1
            one_car_behind_delta = driver_list[one_car_behind_index].m_delta_to_car_in_front
            for data in reversed(driver_list[:len(driver_list)-1]):
                delta_so_far -= one_car_behind_delta
                one_car_behind_delta = data.m_delta_to_car_in_front
                data.m_delta_to_car_in_front = milliseconds_to_seconds_str(delta_so_far)
            driver_list[len(driver_list)-1].m_delta_to_car_in_front = "---"

        # case 3: player is somewhere in the middle of the pack
        else:

            # First, set the deltas for the cars ahead
            delta_so_far = 0
            one_car_behind_index = player_index
            one_car_behind_delta = driver_list[one_car_behind_index].m_delta_to_car_in_front
            for data in reversed(driver_list[:player_index]):
                delta_so_far -= one_car_behind_delta
                one_car_behind_delta = data.m_delta_to_car_in_front
                data.m_delta_to_car_in_front = milliseconds_to_seconds_str(delta_so_far)

            # Finally, set the deltas for the cars ahead
            delta_so_far = 0
            for data in driver_list[player_index+1:]:
                delta_so_far += data.m_delta_to_car_in_front
                data.m_delta_to_car_in_front = milliseconds_to_seconds_str(delta_so_far)

            # finally set the delta for the player
            driver_list[player_index].m_delta_to_car_in_front = "---"

        # Update the race leader's delta to car in front
        if driver_list[0].m_position == 1:
            driver_list[0].m_delta_to_car_in_front = "---"

    return driver_list

