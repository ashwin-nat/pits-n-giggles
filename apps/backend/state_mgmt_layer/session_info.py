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

from typing import Dict, List, Optional

from lib.config import PngSettings
from lib.f1_types import (GameMode, PacketFinalClassificationData,
                          PacketSessionData, SafetyCarType, SessionType,
                          TrackID, WeatherForecastSample)
from lib.logger import PngLogger
from lib.openf1 import MostRecentPoleLap

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def _buildPitTimeLossDict(model_dump: Dict[str, Optional[float]],
                           track_name_to_enum: Dict[str, TrackID]) -> Dict[TrackID, Optional[float]]:
    """Build a track -> pit time loss dict from a settings model's dumped fields.

    Args:
        model_dump (Dict[str, Optional[float]]): settings.TimeLossInPitsF1/F2.model_dump()
        track_name_to_enum (Dict[str, TrackID]): Track name (as it appears in settings) -> TrackID

    Returns:
        Dict[TrackID, Optional[float]]: Pit time loss in seconds, keyed by track
    """
    return {
        track_name_to_enum[field if field.endswith("_Reverse") else field.replace("_", " ")]: value
        for field, value in model_dump.items()
    }

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
        "m_chequered_flag",
    )

    def __init__(self, settings: PngSettings, logger: PngLogger) -> None:
        """
        Init the SessionInfo object fields to None

        Args:
            settings (PngSettings): App Settings
            logger (PngLogger): Logger
        """

        self.m_logger: PngLogger = logger
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
        self.m_chequered_flag : Optional[bool] = False

        # Initialize the pit time loss dicts
        track_name_to_enum = {str(member): member for member in TrackID}
        self.m_pit_time_loss_f1_dict: Dict[TrackID, Optional[float]] = _buildPitTimeLossDict(
            settings.TimeLossInPitsF1.model_dump(), track_name_to_enum)
        self.m_pit_time_loss_f2_dict: Dict[TrackID, Optional[float]] = _buildPitTimeLossDict(
            settings.TimeLossInPitsF2.model_dump(), track_name_to_enum)

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
        self.m_chequered_flag = False
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

    @property
    def curr_weather(self) -> Optional[WeatherForecastSample.WeatherCondition]:
        """Get the current weather if available."""
        return self.m_weather_forecast_samples[0].m_weather if self.m_weather_forecast_samples else None

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
