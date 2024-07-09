
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
from lib.f1_types import PacketSessionData, PacketLapData, LapData, CarTelemetryData, ParticipantData, \
    PacketEventData, PacketParticipantsData, PacketCarTelemetryData, PacketCarStatusData, FinalClassificationData, \
    PacketFinalClassificationData, PacketCarDamageData, PacketSessionHistoryData, ResultStatus, PacketTyreSetsData, \
    F1Utils, WeatherForecastSample, CarDamageData, CarStatusData, TrackID, ActualTyreCompound, VisualTyreCompound, \
    SafetyCarType, TelemetrySetting
from lib.race_analyzer import getFastestTimesJson, getTyreStintRecordsDict
from lib.overtake_analyzer import OvertakeRecord
from lib.collisions_analyzer import CollisionRecord, CollisionAnayzer, CollisionAnalyzerMode
from lib.tyre_wear_extrapolator import TyreWearExtrapolator, TyreWearPerLap
from src.png_logger import getLogger

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class GlobalData:
    """
    Class that stores global race data.

    Attributes:
         - m_circuit (str): The current circuit name
         - m_event_type (str): The current event type
         - m_track_temp (int): The current track temperature
         - m_air_temp (int): The current air temperature
         - m_total_laps (int): The total number of laps in the current event
         - m_safety_car_status (SafetyCarStatus): Current safety car status enum
         - m_is_spectating (bool): Whether the user is currently spectating
         - m_spectator_car_index (int): Which car the user is spectating
         - m_weather_forecast_samples (List[WeatherForecastSample]): The list of weather forecast samples
         - m_pit_speed_limit (int): The Pit Lane speed limit (in kmph)
         - m_packet_final_classification (PacketFinalClassificationData): The final classification packet
         - m_packet_session (PacketSessionData): Copy of the last saved session packet
         - m_game_year (int): The current game year
    """

    def __init__(self):
        """
        Init the GlobalData object fields to None
        """

        self.m_circuit : Optional[str] = None
        self.m_event_type : Optional[str] = None
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
        """Dump the GlobalData object to a readable string

        Returns:
            str: Readable string
        """
        return (
            f"GlobalData(m_circuit={self.m_circuit}, "
            f"m_event_type={self.m_event_type}, "
            f"m_track_temp={self.m_track_temp}, "
            f"m_air_temp={self.m_air_temp}, "
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

        ret_status = False
        if self.m_packet_session and (packet.m_header.m_sessionUID != self.m_packet_session.m_header.m_sessionUID):
            ret_status = True

        self.m_circuit = str(packet.m_trackId)
        self.m_track_temp = packet.m_trackTemperature
        self.m_air_temp = packet.m_airTemperature
        self.m_event_type = str(packet.m_sessionType)
        self.m_event_type = str(packet.m_sessionType)
        self.m_weather_forecast_samples = packet.m_weatherForecastSamples
        self.m_weather_forecast_samples = packet.m_weatherForecastSamples
        self.m_pit_speed_limit = packet.m_pitSpeedLimit
        self.m_pit_speed_limit = packet.m_pitSpeedLimit
        self.m_total_laps = packet.m_totalLaps
        self.m_packet_session = packet
        self.m_is_spectating = packet.m_isSpectating
        self.m_game_year = packet.m_header.m_gameYear
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
        m_telemetry_restrictions (Optional[TelemetrySetting]):
            Telemetry settings indicating the level of data available for the driver.
        m_tyre_set_history (List[DataPerDriver.TyreSetHistoryEntry]):
            List of TyreSetHistoryEntry objects, representing the driver's tire set history.
        m_tyre_wear_extrapolator (TyreWearExtrapolator): Predicts the tyre wear for upcoming laps
        m_curr_lap_sc_status (SafetyCarStatus): The current lap's safety car status
        m_fuel_load_kg (float): The current fuel load (in kg)
        m_fuel_laps_remaining (float): Number of laps remaining with current fuel load
        m_fl_wing_damage (int): Left front wing damage
        m_fr_wing_damage (int): Right front wing damage
        m_rear_wing_damage (int): Rear wing damage
        m_collision_records (List[CollisionRecord]): List of CollisionRecord objects for the driver.

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

    class TyreSetInfo:
        """
        Class that models the data describing a tyre set.

        Attributes:
            m_actual_tyre_compound (ActualTyreCompound): The actual compound of the tyre.
            m_visual_tyre_compound (VisualTyreCompound): The visual compound of the tyre.
            m_tyre_set_id (int): The ID of the tyre set.
            m_tyre_age_laps (int): The age of the tyre in laps.
        """
        def __init__(self,
                     actual_tyre_compound: ActualTyreCompound,
                     visual_tyre_compound: VisualTyreCompound,
                     tyre_set_id: int,
                     tyre_age_laps: int):

            self.m_actual_tyre_compound = actual_tyre_compound
            self.m_visual_tyre_compound = visual_tyre_compound
            self.m_tyre_set_id = tyre_set_id
            self.m_tyre_age_laps = tyre_age_laps

        def toJSON(self) -> Dict[str, Any]:
            """Get the JSON representation of this object

            Returns:
                Dict[str, Any]: The JSON representation
            """
            return {
                'actual-tyre-compound': str(self.m_actual_tyre_compound),
                'visual-tyre-compound': str(self.m_visual_tyre_compound),
                'tyre-set-id': self.m_tyre_set_id,
                'tyre-age-laps': self.m_tyre_age_laps
            }

        def __repr__(self) -> str:
            """
            Returns a string representation of the object suitable for debugging.
            """
            return f"TyreSetInfo(actual_tyre_compound={str(self.m_actual_tyre_compound)}, " \
                f"visual_tyre_compound={str(self.m_visual_tyre_compound)}, " \
                f"tyre_set_id={self.m_tyre_set_id}, " \
                f"tyre_age_laps={self.m_tyre_age_laps})"

        def __str__(self) -> str:
            """
            Returns a string representation of the object suitable for end-users.
            """
            return f"Tyre Set ID: {self.m_tyre_set_id}, " \
                f"Actual Compound: {str(self.m_actual_tyre_compound)}, " \
                f"Visual Compound: {str(self.m_visual_tyre_compound)}, " \
                f"Tyre Age (laps): {self.m_tyre_age_laps}"

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
            m_tyre_sets_packet (Optional[PacketTyreSetsData]): The Tyre Sets packet
            m_sc_status (PacketSessionData.SafetyCarStatus): The lap's safety car status
        """

        def __init__(self,
                     car_damage : CarDamageData,
                     car_status : CarStatusData,
                     sc_status  : SafetyCarType,
                     tyre_sets  : PacketTyreSetsData):
            """Init the backup entry object

            Args:
                car_damage (CarDamageData): The Car damage packet
                car_status (CarStatusData): The Car Status packet
                sc_status (PacketSessionData.SafetyCarStatus): The lap's safety car status
                tyre_sets (PacketTyreSetsData): The Tyre Sets packet
            """

            self.m_car_damage_packet: Optional[CarDamageData] = car_damage
            self.m_car_status_packet: Optional[CarStatusData] = car_status
            self.m_sc_status: Optional[PacketSessionData.SafetyCarStatus] = sc_status
            self.m_tyre_sets_packet: Optional[PacketTyreSetsData] = tyre_sets

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
                "safety-car-status" : self.m_sc_status if self.m_sc_status else None,
                "tyre-sets-data" : self.m_tyre_sets_packet.toJSON() if self.m_tyre_sets_packet else None
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
        self.m_telemetry_restrictions: Optional[TelemetrySetting] = None
        self.m_tyre_set_history: List[DataPerDriver.TyreSetHistoryEntry] = []
        self.m_tyre_wear_extrapolator: TyreWearExtrapolator = TyreWearExtrapolator([], total_laps=total_laps)
        self.m_curr_lap_sc_status: Optional[SafetyCarType] = None
        self.m_fuel_load_kg: Optional[float] = None
        self.m_fuel_laps_remaining: Optional[float] = None
        self.m_fl_wing_damage: Optional[int] = None
        self.m_fr_wing_damage: Optional[int] = None
        self.m_rear_wing_damage: Optional[int] = None
        self.m_collision_records: List[CollisionRecord] = []

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
               include_tyre_wear_prediction : Optional[bool] = False,
               selected_pit_stop_lap : Optional[int] = None) -> Dict[str, Any]:
        """Get a JSON representation of this DataPerDriver object

        Args:
            index (int): The index number. Defaults to None.
            include_tyre_wear_prediction (Optional[bool]): Whether to include the tyre wear prediction
            selected_pit_stop_lap (Optional[int]): The lap number of the selected pit stop

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
            if self.m_tyre_wear_extrapolator.isDataSufficient():
                final_json["tyre-wear-predictions"] = {
                    "status" : True,
                    "desc" : "Data is sufficient for extrapolation",
                    "predictions": [item.toJSON() for item in self.m_tyre_wear_extrapolator.predicted_tyre_wear],
                    "selected-pit-stop-lap": selected_pit_stop_lap
                }
            else:
                final_json["tyre-wear-predictions"] = {
                    "status" : False,
                    "desc" : "Insufficient data for extrapolation"
                }

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

        if self.m_tyre_wear_extrapolator.isDataSufficient() and (self.m_tyre_wear_extrapolator.remaining_laps > 0):
            predictions_list = []

            # Input sanitization
            if next_pit_window is None or (next_pit_window == 0) or (next_pit_window < self.m_current_lap):
                # Lets return the lap midway between current lap and final lap
                next_pit_window = (self.m_current_lap + self.m_tyre_wear_extrapolator.total_laps) // 2

            # NOTE: Flashbacks or delayed telemetry starts can cause the prediction to not be available.
            # This happens in the last lap
            if next_pit_window == self.m_tyre_wear_extrapolator.total_laps:
                # We are already in the final lap, so return the final prediction
                predicted_tyre_wear = self.m_tyre_wear_extrapolator.getTyreWearPrediction()
                if predicted_tyre_wear:
                    predictions_list.append(predicted_tyre_wear.toJSON())
            else:

                # Add prediction for next window if available
                pit_lap_prediction = self.m_tyre_wear_extrapolator.getTyreWearPrediction(next_pit_window)
                if pit_lap_prediction and next_pit_window:
                    predictions_list.append(pit_lap_prediction.toJSON())

                # Add final lap prediction if available
                final_lap_prediction = self.m_tyre_wear_extrapolator.getTyreWearPrediction()
                if final_lap_prediction:
                    predictions_list.append(final_lap_prediction.toJSON())
            return predictions_list
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
            # Overwrite the tyre sets wear to actual recent float value
            if (len(tyre_set_history[-1]['tyre-wear-history']) > 0) and (tyre_set_history[-1]['tyre-set-data']):
                tyre_set_history[-1]['tyre-set-data']['wear'] = tyre_set_history[-1]['tyre-wear-history'][-1]['average']

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
                    png_logger.debug('car damage data not available for lap %d driver %s', lap_number, self.m_name)
            else:
                png_logger.debug('per lap backup not available for lap %d driver %s', lap_number, self.m_name)
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
            sc_status=self.m_curr_lap_sc_status,
            tyre_sets=self.m_packet_tyre_sets
        )

        # Add the tyre wear data into the tyre stint history
        if (old_lap_number > 0) and (len(self.m_tyre_set_history) > 0):
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
        tyre_set_id = self._getCurrentTyreSetKey()
        if tyre_set_id:
            self.m_tyre_wear_extrapolator.updateDataLap(TyreWearPerLap(
                lap_number=old_lap_number,
                fl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                fr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                rl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                rr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                is_racing_lap=True,
                desc=tyre_set_id
            ))

    def isZerothLapBackupDataAvailable(self) -> bool:
        """
        Checks if zeroth lap backup data is available.

        Returns:
            bool - True if zeroth lap backup data is available
        """

        return bool(
            self.m_packet_car_damage and
            self.m_packet_car_status and
            self.m_packet_tyre_sets
        )


    def updateTyreSetData(self, fitted_index: int) -> None:
        """Update the current tyre set in the history list, if required.
               NOTE: The tyre history is ignored if the player has disabled telemetry

        Args:
            fitted_index (int): The fitted tyre set index
        """

        # fuck those anti telemetry cunts
        if self.m_telemetry_restrictions != TelemetrySetting.PUBLIC:
            return

        # This can happen if tyre sets packets arrives before lap data packet
        if self.m_current_lap is not None:
            fitted_tyre_set_key = self._getCurrentTyreSetKey()
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
                                                tyre_set_key=fitted_tyre_set_key,
                                                initial_tyre_wear=initial_tyre_wear,
                    ))
            elif fitted_index != self.m_tyre_set_history[-1].m_fitted_index:
                lap_number = self.m_current_lap - 1
                # create a new tyre set entry with initial data.
                initial_tyre_wear = TyreWearPerLap(
                    lap_number=lap_number,
                    fl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_LEFT],
                    fr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_FRONT_RIGHT],
                    rl_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_LEFT],
                    rr_tyre_wear=self.m_packet_car_damage.m_tyresWear[F1Utils.INDEX_REAR_RIGHT],
                    is_racing_lap=True,
                    desc="tyre set change detected. key=" + str(fitted_tyre_set_key)
                )
                self.m_tyre_set_history.append(DataPerDriver.TyreSetHistoryEntry(
                                            start_lap=lap_number,
                                            index=fitted_index,
                                            tyre_set_key=fitted_tyre_set_key,
                                            initial_tyre_wear=initial_tyre_wear,
                ))

                # Tyre set change detected. clear the extrapolation data
                self.m_tyre_wear_extrapolator.clear()
                self.m_tyre_wear_extrapolator.updateDataLap(initial_tyre_wear)

    def _getCurrentTyreSetKey(self) -> Optional[str]:
        """Get the unique ID key for the currently equipped tyre set

        Returns:
            Optional[str]: The tyre set key
        """

        return self.m_packet_tyre_sets.getFittedTyreSetKey() if self.m_packet_tyre_sets else None

    def _getCurrentTyreSetID(self) -> Optional[int]:
        """Get the ID/index for the currently equipped tyre set

        Returns:
            Optional[int]: The tyre set ID
        """

        return self.m_packet_tyre_sets.m_fittedIdx if self.m_packet_tyre_sets else None

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

    def getTyreSetInfoAtLap(self, lap_num: Optional[int] = None) -> Optional[TyreSetInfo]:
        """Get the tyre set info at the specified lap number

        Args:
            lap_num (Optional[int]): The lap number. If None, uses current lap number

        Returns:
            Optional[TyreSetInfo]: The tyre set info. None if data not found or invalid lap num
        """

        if lap_num is None:
            lap_num = self.m_current_lap

        if lap_num == self.m_current_lap and self.m_packet_car_status:
            return DataPerDriver.TyreSetInfo(
                actual_tyre_compound=self.m_packet_car_status.m_actualTyreCompound,
                visual_tyre_compound=self.m_packet_car_status.m_visualTyreCompound,
                tyre_set_id=self._getCurrentTyreSetID(),
                tyre_age_laps=self.m_packet_car_status.m_tyresAgeLaps
            )
        if (lap_num < self.m_current_lap) and (lap_num in self.m_per_lap_backups):
            backup_at_lap       = self.m_per_lap_backups[lap_num]
            backup_car_status   = backup_at_lap.m_car_status_packet
            backup_tyre_sets    = backup_at_lap.m_tyre_sets_packet
            if not backup_car_status or not backup_tyre_sets:
                return None
            return DataPerDriver.TyreSetInfo(
                actual_tyre_compound=backup_car_status.m_actualTyreCompound,
                visual_tyre_compound=backup_car_status.m_visualTyreCompound,
                tyre_set_id=backup_tyre_sets.m_fittedIdx,
                tyre_age_laps=backup_car_status.m_tyresAgeLaps
            )

        return None


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
        m_track_id (TrackID): The track ID of the event
        m_game_year (int): The game year
        m_collision_records (List[CollisionRecord]): List of collision records
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
        self.m_track_id : Optional[TrackID] = None
        self.m_game_year : Optional[int] = None
        self.m_collision_records : List[CollisionRecord] = []

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
        self.m_track_id = None
        self.m_game_year = None
        self.m_collision_records.clear()

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

    def getIndexByTrackPosition(self, track_position: int) -> Tuple[Optional[int], Optional[DataPerDriver]]:
        """
        Get the driver index and data based on the provided track position.

        Args:
            track_position(int): The track position to search for.

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
                    driver_best_lap_ms = \
                        driver_data.m_packet_session_history.m_lapHistoryData[best_lap_index].m_lapTimeInMS
        if driver_best_lap_ms is None:
            # Second option, from the object itself
            driver_best_lap_ms = driver_data.m_best_lap_ms

        # False if this guy does not have a valid best lap
        if driver_data.m_best_lap_ms is None:
            return False

        # Check if this guy's lap is faster than the best lap
        return self.m_driver_data[self.m_fastest_index].m_best_lap_ms > driver_best_lap_ms

    def processSessionUpdate(self, packet: PacketSessionData) -> None:
        """Process the Session Update packet. Update the total laps and ideal pit window for the player

        Args:
            packet (PacketSessionData): The incoming parsed packet object
        """

        self.m_ideal_pit_stop_window = packet.m_pitStopWindowIdealLap
        self.m_track_id = packet.m_trackId
        self.m_game_year = packet.m_header.m_gameYear

        # First time total laps notification has arrived after driver info (out of order)
        if (self.m_total_laps is None) and (packet.m_totalLaps > 0):

            # First update the total laps
            self.m_total_laps = packet.m_totalLaps

            # Next, update in all extrapolator objects
            for driver_data in self.m_driver_data.values():
                driver_data.m_tyre_wear_extrapolator.total_laps = self.m_total_laps

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
            obj_to_be_updated.m_is_pitting = lap_data.m_pitStatus in \
                [LapData.PitStatus.PITTING, LapData.PitStatus.IN_PIT_AREA]
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
        obj_to_be_updated.m_dnf_status_code = 'DNF'

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
            obj_to_be_updated.m_fuel_load_kg = car_status_data.m_fuelInTank
            obj_to_be_updated.m_fuel_laps_remaining = car_status_data.m_fuelRemainingLaps

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
        final_json['game-year'] = self.m_game_year
        self.m_final_json = final_json
        return final_json

    def processCarDamageUpdate(self, packet: PacketCarDamageData) -> None:
        """Process the car damage update packet and update the necessary fields

        Args:
            packet (PacketCarDamageData): The car damage update packet
        """
        for index, car_damage in enumerate(packet.m_carDamageData):
            obj_to_be_updated = self._getObjectByIndexCreate(index)
            obj_to_be_updated.m_packet_car_damage = car_damage
            obj_to_be_updated.m_tyre_wear = sum(car_damage.m_tyresWear)/len(car_damage.m_tyresWear)
            obj_to_be_updated.m_fl_wing_damage = car_damage.m_frontLeftWingDamage
            obj_to_be_updated.m_fr_wing_damage = car_damage.m_frontRightWingDamage
            obj_to_be_updated.m_rear_wing_damage = car_damage.m_rearWingDamage

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
        if self.m_race_completed:
            include_wear_prediction = False
            selected_pit_stop_lap = None
        else:
            include_wear_prediction = True
            if obj_to_be_updated.m_is_player:
                if self.m_ideal_pit_stop_window < obj_to_be_updated.m_current_lap:
                    selected_pit_stop_lap = None
                else:
                    selected_pit_stop_lap = self.m_ideal_pit_stop_window
            else:
                selected_pit_stop_lap = None
        if not obj_to_be_updated:
            return None
        final_json = obj_to_be_updated.toJSON(index, include_wear_prediction, selected_pit_stop_lap)
        final_json["circuit"] = str(self.m_track_id)
        final_json["is-finish-line-after-pit-garage"] = F1Utils.isFinishLineAfterPitGarage(self.m_track_id) \
            if self.m_track_id is not None else None

        # Collisions stats
        final_json["collisions"] = self._getCollisionStatsJSON()
        return final_json

    def getRaceInfoJSON(self) -> Dict[str, Any]:
        """Get the race info JSON.

        Returns:
            Dict[str, Any]: Race info JSON
        """

        if self.m_race_completed and self.m_final_json:
            return self.m_final_json
        return {"classification-data" : self._getClassificationDataListJSON()}

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
        driver_1_obj = self.m_driver_data.get(driver_1_index, None)
        driver_2_obj = self.m_driver_data.get(driver_2_index, None)
        if driver_1_obj is None or driver_2_obj is None:
            return None

        if driver_1_obj.m_name is None or \
            driver_1_obj.m_current_lap is None or \
                driver_2_obj.m_name is None or \
                    driver_2_obj.m_current_lap is None:
            return None

        return CollisionRecord(
            driver_1_name=driver_1_obj.m_name,
            driver_1_lap=driver_1_obj.m_current_lap,
            driver_1_index=driver_1_index,
            driver_2_name=driver_2_obj.m_name,
            driver_2_lap=driver_2_obj.m_current_lap,
            driver_2_index=driver_2_index
        )

    def _getClassificationDataListJSON(self):
        """
        Return a list of dictionaries containing index, driver name, position, and participant data.
        """

        return [driver_data.toJSON(index) for index, driver_data in self.m_driver_data.items()]

    def _getCollisionStatsJSON(self) -> Dict[str, Any]:
        """Get the collision stats JSON.

        Returns:
            Dict[str, Any]: Collision stats JSON
        """

        collision_analyzer = CollisionAnayzer(
            input_mode=CollisionAnalyzerMode.INPUT_MODE_LIST_COLLISION_RECORDS,
            input_data=self.m_collision_records)
        return collision_analyzer.toJSON()

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
png_logger = getLogger()

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

def processCollisionsEvent(packet: PacketEventData.Collision)-> None:
    """Update the data structures with collisions event udpate.

    Args:
        packet (PacketEventData.Collision): The collision update packet
    """

    with _driver_data_lock:
        _driver_data.processCollisionEvent(packet)

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

def getGlobals() -> GlobalData:
    """
    Returns a copy of the GlobalData object

    Returns:
        GlobalData: A copy of the GlobalData object
    """
    with _globals_lock:
        return copy.deepcopy(_globals)

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

def isDriverIndexValid(index: int) -> bool:
    """Check if the given index is a valid driver index

    Args:
        index (int): Index of the driver

    Returns:
        bool: True if valid
    """

    with _driver_data_lock:
        return index in _driver_data.m_driver_data

def getEventInfoStr() -> Optional[str]:
    """Returns a string with the following format
            <event-type> _ <circuit> _

    Returns:
        Optional[str]: The event type string (ends with an underscore), or None if no data is available
    """
    with _globals_lock:
        if _globals.m_event_type and _globals.m_circuit:
            return (_globals.m_event_type + "_" + _globals.m_circuit).replace(' ', '_') + '_'
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

def getCollisionObj(driver_1_index: int, driver_2_index: int) -> Optional[CollisionRecord]:
    """Returns a collision object containing collision information

    Args:
        driver_1_index (int): The index of the first driver
        driver_2_index (int): The index of the second driver

    Returns:
        Optional[CollisionRecord]: A collision object containing collision information
    """
    with _driver_data_lock:
        if not _driver_data.m_driver_data:
            return None
        driver_1_obj = _driver_data.m_driver_data.get(driver_1_index, None)
        driver_2_obj = _driver_data.m_driver_data.get(driver_2_index, None)
        if driver_1_obj is None or driver_2_obj is None:
            return None

        if driver_1_obj.m_name is None or \
            driver_1_obj.m_current_lap is None or \
                driver_2_obj.m_name is None or \
                    driver_2_obj.m_current_lap is None:
            return None

        return CollisionRecord(
            driver_1_name=driver_1_obj.m_name,
            driver_1_lap=driver_1_obj.m_current_lap,
            driver_1_index=driver_1_index,
            driver_2_name=driver_2_obj.m_name,
            driver_2_lap=driver_2_obj.m_current_lap,
            driver_2_index=driver_2_index
        )

def getCustomMarkerEntryObj() -> Optional[CustomMarkerEntry]:
    """
    Retrieves the custom marker entry object for the player.

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
    return CustomMarkerEntry(
        track=track,
        event_type=event_type,
        lap=lap_num,
        sector=sector,
        curr_lap_time=curr_lap_time,
        curr_lap_perc=curr_lap_percent
    )
