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


import struct
from typing import Any, Dict, List, Union

from .base_pkt import F1BaseEnum, F1PacketBase, F1SubPacketBase
from .common import (GameMode, GearboxAssistMode, RuleSet, SafetyCarType,
                     SessionLength, SessionType23, SessionType24, TrackID)
from .header import PacketHeader

# --------------------- CLASS DEFINITIONS --------------------------------------

class MarshalZone(F1SubPacketBase):
    """
    A class for parsing the Marshal Zone data within a telemetry packet in a racing game.

    The Marshal Zone structure is as follows:

    Attributes:
        - m_zone_start (float): Fraction (0..1) of the way through the lap the marshal zone starts.
        - m_zone_flag (MarshalZone.MarshalZoneFlagType): Refer to the enum type for various options
    """

    COMPILED_PACKET_STRUCT = struct.Struct("<"
        "f" # float - Fraction (0..1) of way through the lap the marshal zone starts
        "b" # int8  - -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
    )
    PACKET_LEN = COMPILED_PACKET_STRUCT.size

    __slots__ = (
        "m_zoneStart",
        "m_zoneFlag",
    )

    class MarshalZoneFlagType(F1BaseEnum):
        """
        ENUM class for the marshal zone flag status
        """

        INVALID_UNKNOWN = -1
        NONE = 0
        GREEN_FLAG = 1
        BLUE_FLAG = 2
        YELLOW_FLAG = 3

    def __init__(self, data: bytes) -> None:
        """Unpack the given raw bytes into this object

        Args:
            data (bytes): List of raw bytes received as part of this
        """

        # Declare the data type hints
        self.m_zoneStart: float
        self.m_zoneFlag: MarshalZone.MarshalZoneFlagType

        # Parse the packet into the fields
        (
            self.m_zoneStart,   # float - Fraction (0..1) of way through the lap the marshal zone starts
            self.m_zoneFlag     # int8 - -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
        ) = self.COMPILED_PACKET_STRUCT.unpack(data)

        self.m_zoneFlag = MarshalZone.MarshalZoneFlagType.safeCast(self.m_zoneFlag)

    def __str__(self) -> str:
        """Return the string representation of this object

        Returns:
            str: string representation
        """
        return f"MarshalZone(Start: {self.m_zoneStart}, Flag: {self.m_zoneFlag})"

    def __eq__(self, other: "MarshalZone") -> bool:
        """Checks if two MarshalZone objects are equal.

        Args:
            other (MarshalZone): The other MarshalZone object to compare with.

        Returns:
            bool: True if the two objects are equal, False otherwise.
        """
        if not isinstance(other, MarshalZone):
            return False
        return self.m_zoneStart == other.m_zoneStart and self.m_zoneFlag == other.m_zoneFlag

    def __ne__(self, other: "MarshalZone") -> bool:
        """Checks if two MarshalZone objects are not equal.

        Args:
            other (MarshalZone): The other MarshalZone object to compare with.

        Returns:
            bool: True if the two objects are not equal, False otherwise.
        """
        return not self.__eq__(other)

    def toJSON(self) -> Dict[str, Any]:
        """Converts the MarshalZone object to a dictionary suitable for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """

        return {
            "zone-start": self.m_zoneStart,
            "zone-flag": str(self.m_zoneFlag)
        }

    def to_bytes(self) -> bytes:
        """Converts the MarshalZone object to raw bytes.

        Returns:
            bytes: A list of bytes representing the raw data.
        """

        return self.COMPILED_PACKET_STRUCT.pack(self.m_zoneStart, self.m_zoneFlag)

    @classmethod
    def from_values(cls, zone_start: float, zone_flag: MarshalZoneFlagType) -> "MarshalZone":
        """Creates a new MarshalZone object from the given values.

        Args:
            zone_start (float): Fraction (0..1) of the way through the lap the marshal zone starts.
            zone_flag (MarshalZone.MarshalZoneFlagType): Refer to the enum type for various options

        Returns:
            MarshalZone: A new MarshalZone object
        """

        return cls(cls.COMPILED_PACKET_STRUCT.pack(zone_start, zone_flag))

class WeatherForecastSample(F1SubPacketBase):
    """
    Represents a weather forecast sample for a specific session type.

    The Weather Forecast Sample structure is as follows:

    Attributes:
        - m_session_type (SessionType): Type of session (this is converted to enum from int)
        - m_time_offset (int): Time in minutes the forecast is for.
        - m_weather (WeatherCondition): Weather condition
        - m_track_temperature (int): Track temperature in degrees Celsius.
        - m_track_temperature_change (TrackTemperatureChange): Track temperature change
        - m_air_temperature (int): Air temperature in degrees Celsius.
        - m_air_temperature_change (AirTemperatureChange): Air temperature change
        - m_rain_percentage (int): Rain percentage (0-100).
    """

    COMPILED_PACKET_STRUCT = struct.Struct("<"
        "B" # uint8  -    0 = unknown, 1 = P1, 2 = P2, 3 = P3, 4 = Short P, 5 = Q1
                        # 6 = Q2, 7 = Q3, 8 = Short Q, 9 = OSQ, 10 = R, 11 = R2
                        # 12 = R3, 13 = Time Trial
        "B" # uint8  - Time in minutes the forecast is for
        "B" # uint8  - Weather - 0 = clear, 1 = light cloud, 2 = overcast
                                #3 = light rain, 4 = heavy rain, 5 = storm
        "b" # int8   - Track temp. in degrees Celsius
        "b" # int8   - Track temp. change - 0 = up, 1 = down, 2 = no change
        "b" # int8   - Air temp. in degrees celsius
        "b" # int8   - Air temp. change - 0 = up, 1 = down, 2 = no change
        "B" # uint8  - Rain percentage (0-100)
    )
    PACKET_LEN = COMPILED_PACKET_STRUCT.size

    __slots__ = (
        "m_session_type",
        "m_time_offset",
        "m_weather",
        "m_track_temperature",
        "m_track_temperature_change",
        "m_air_temperature",
        "m_air_temperature_change",
        "m_rain_percentage",
    )

    class WeatherCondition(F1BaseEnum):
        """
        Enumeration representing different weather conditions.

        Attributes:
            CLEAR (int): Clear weather condition.
            LIGHT_CLOUD (int): Light cloud cover weather condition.
            OVERCAST (int): Overcast weather condition.
            LIGHT_RAIN (int): Light rain weather condition.
            HEAVY_RAIN (int): Heavy rain weather condition.
            STORM (int): Stormy weather condition.
            THUNDERSTORM (int) : Thunderstormy weather condition. (this is not documented,
                but there is a value of 6 that may be sent. I'm just guessing here)

            Note:
                Each attribute represents a unique weather condition identified by an integer value.
        """
        CLEAR = 0
        LIGHT_CLOUD = 1
        OVERCAST = 2
        LIGHT_RAIN = 3
        HEAVY_RAIN = 4
        STORM = 5
        THUNDERSTORM = 6

        def isDry(self) -> bool:
            """Return True if this weather condition is considered dry."""
            return self in (
                WeatherForecastSample.WeatherCondition.CLEAR,
                WeatherForecastSample.WeatherCondition.LIGHT_CLOUD,
                WeatherForecastSample.WeatherCondition.OVERCAST,
            )

        def isWet(self) -> bool:
            """Return True if this weather condition is considered wet."""
            return not self.isDry()

        def __str__(self):
            """
            Returns a human-readable string representation of the weather condition.

            Returns:
                str: String representation of the weather condition.
            """
            return self.name.replace('_', ' ').title()

    class TrackTemperatureChange(F1BaseEnum):
        """
        Enumeration representing changes in track temperature.

        Attributes:
            UP (int): Track temperature is increasing.
            DOWN (int): Track temperature is decreasing.
            NO_CHANGE (int): No change in track temperature.

            Note:
                Each attribute represents a unique state of track temperature change identified by an integer value.
        """
        UP = 0
        DOWN = 1
        NO_CHANGE = 2

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the track temperature change.

            Returns:
                str: String representation of the track temperature change.
            """
            return {
                WeatherForecastSample.TrackTemperatureChange.UP: "Temperature Up",
                WeatherForecastSample.TrackTemperatureChange.DOWN: "Temperature Down",
                WeatherForecastSample.TrackTemperatureChange.NO_CHANGE: "No Temperature Change",
            }[self]

    class AirTemperatureChange(F1BaseEnum):
        """
        Enumeration representing changes in air temperature.

        Attributes:
            UP (int): Air temperature is increasing.
            DOWN (int): Air temperature is decreasing.
            NO_CHANGE (int): No change in air temperature.

            Note:
                Each attribute represents a unique state of air temperature change identified by an integer value.
        """
        UP = 0
        DOWN = 1
        NO_CHANGE = 2

        def __str__(self) -> str:
            return {
                WeatherForecastSample.AirTemperatureChange.UP: "Temperature Up",
                WeatherForecastSample.AirTemperatureChange.DOWN: "Temperature Down",
                WeatherForecastSample.AirTemperatureChange.NO_CHANGE: "No Temperature Change",
            }[self]

    def __init__(self, data: bytes, packet_format: int) -> None:
        """Unpack the given raw bytes into this object

        Args:
            data (bytes): List of raw bytes received as part of this
            packet_format (int): The format of the packet
        """

        # Declare the type hints
        self.m_sessionType : int
        self.m_timeOffset : int
        self.m_weather : WeatherForecastSample.WeatherCondition
        self.m_trackTemperature : int
        self.m_trackTemperatureChange : WeatherForecastSample.TrackTemperatureChange
        self.m_airTemperature : int
        self.m_airTemperatureChange : WeatherForecastSample.AirTemperatureChange
        self.m_rainPercentage : int

        # Parse the packet into the fields
        (
            self.m_sessionType,                   # uint8
            self.m_timeOffset,                    # uint8
            self.m_weather,                       # uint8
            self.m_trackTemperature,              # int8
            self.m_trackTemperatureChange,        # int8
            self.m_airTemperature,                # int8
            self.m_airTemperatureChange,          # int8
            self.m_rainPercentage                 # uint8
        ) = self.COMPILED_PACKET_STRUCT.unpack(data)

        # Convert to typed enums wherever applicable
        self.m_weather = WeatherForecastSample.WeatherCondition.safeCast(self.m_weather)
        self.m_airTemperatureChange = WeatherForecastSample.AirTemperatureChange.safeCast(self.m_airTemperatureChange)
        self.m_trackTemperatureChange = WeatherForecastSample.TrackTemperatureChange.safeCast(
                                        self.m_trackTemperatureChange)
        if packet_format == 2023:
            self.m_sessionType = SessionType23.safeCast(self.m_sessionType)
        else:
            self.m_sessionType = SessionType24.safeCast(self.m_sessionType)

    def __str__(self) -> str:
        """A description of the entire function, its parameters, and its return types.

        Returns:
            str : string dump of this object
        """
        return (
            f"WeatherForecastSample("
            f"Session Type: {str(self.m_sessionType)}, "
            f"Time Offset: {self.m_timeOffset}, "
            f"Weather: {self.m_weather}, "
            f"Track Temperature: {self.m_trackTemperature}, "
            f"Track Temp Change: {self.m_trackTemperatureChange}, "
            f"Air Temperature: {self.m_airTemperature}, "
            f"Air Temp Change: {self.m_airTemperatureChange}, "
            f"Rain Percentage: {self.m_rainPercentage})"
        )

    def __eq__(self, other: "WeatherForecastSample") -> bool:
        """Checks if two WeatherForecastSample objects are equal.

        Args:
            other (WeatherForecastSample): The other WeatherForecastSample object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """

        if not isinstance(other, WeatherForecastSample):
            return False

        return (
            self.m_sessionType == other.m_sessionType and
            self.m_timeOffset == other.m_timeOffset and
            self.m_weather == other.m_weather and
            self.m_trackTemperature == other.m_trackTemperature and
            self.m_trackTemperatureChange == other.m_trackTemperatureChange and
            self.m_airTemperature == other.m_airTemperature and
            self.m_airTemperatureChange == other.m_airTemperatureChange and
            self.m_rainPercentage == other.m_rainPercentage
        )

    def __ne__(self, other: "WeatherForecastSample") -> bool:
        """Checks if two WeatherForecastSample objects are not equal.

        Args:
            other (WeatherForecastSample): The other WeatherForecastSample object to compare with.

        Returns:
            bool: True if the objects are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def toJSON(self) -> Dict[str, Any]:
        """Converts the WeatherForecastSample object to a dictionary suitable for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """

        return {
            "session-type": str(self.m_sessionType),
            "time-offset": self.m_timeOffset,
            "weather": str(self.m_weather),
            "track-temperature": self.m_trackTemperature,
            "track-temperature-change": str(self.m_trackTemperatureChange),
            "air-temperature": self.m_airTemperature,
            "air-temperature-change": str(self.m_airTemperatureChange),
            "rain-percentage": self.m_rainPercentage
        }

    def to_bytes(self) -> bytes:
        """Converts the WeatherForecastSample object to raw bytes.

        Returns:
            bytes: A list of bytes representing the raw data.
        """

        return self.COMPILED_PACKET_STRUCT.pack(
            self.m_sessionType,
            self.m_timeOffset,
            self.m_weather.value,
            self.m_trackTemperature,
            self.m_trackTemperatureChange.value,
            self.m_airTemperature,
            self.m_airTemperatureChange.value,
            self.m_rainPercentage
        )

    @classmethod
    def from_values(cls,
                    game_year: int,
                    session_type: Union[SessionType23, SessionType24],
                    time_offset: int,
                    weather: WeatherCondition,
                    track_temp: int,
                    track_temp_change: TrackTemperatureChange,
                    air_temp: int,
                    air_temp_change: AirTemperatureChange,
                    rain_percentage: int) -> "WeatherForecastSample":
        """
        Creates a new WeatherForecastSample object from the given values

        Args:
            game_year (int): Game year
            session_type (Union[SessionType23, SessionType24]): Session type enum
            time_offset (int): Time offset in minutes
            weather (WeaetherCondition): Weather enum
            track_temp (int): Track temp in celsius
            track_temp_change (TrackTemperatureChange): Track temp change enum
            air_temp (int): Air temp in celsius
            air_temp_change (AirTemperatureChange): Air temp change enum
            rain_percentage (int): Probability percentage of rain

        Returns:
            WeatherForecastSample: _description_
        """

        return cls(
            WeatherForecastSample.COMPILED_PACKET_STRUCT.pack(
                session_type.value,
                time_offset,
                weather.value,
                track_temp,
                track_temp_change.value,
                air_temp,
                air_temp_change.value,
                rain_percentage
            ),
            game_year
        )

class ActiveAeroZone(F1SubPacketBase):
    """A zone on the track where active aero is available (F1 2026+)."""

    COMPILED_PACKET_STRUCT = struct.Struct("<ff")
    PACKET_LEN = COMPILED_PACKET_STRUCT.size

    __slots__ = ("m_zoneStart", "m_zoneEnd")

    def __init__(self, data: bytes) -> None:
        self.m_zoneStart: float
        self.m_zoneEnd: float
        self.m_zoneStart, self.m_zoneEnd = self.COMPILED_PACKET_STRUCT.unpack(data)

    def __str__(self) -> str:
        return f"ActiveAeroZone(Start: {self.m_zoneStart}, End: {self.m_zoneEnd})"

    def __eq__(self, other: "ActiveAeroZone") -> bool:
        if not isinstance(other, ActiveAeroZone):
            return False
        return self.m_zoneStart == other.m_zoneStart and self.m_zoneEnd == other.m_zoneEnd

    def __ne__(self, other: "ActiveAeroZone") -> bool:
        return not self.__eq__(other)

    def toJSON(self) -> Dict[str, Any]:
        return {"zone-start": self.m_zoneStart, "zone-end": self.m_zoneEnd}

    def to_bytes(self) -> bytes:
        return self.COMPILED_PACKET_STRUCT.pack(self.m_zoneStart, self.m_zoneEnd)


class DRSZone(F1SubPacketBase):
    """A DRS zone on the track (F1 2026+)."""

    COMPILED_PACKET_STRUCT = struct.Struct("<ff")
    PACKET_LEN = COMPILED_PACKET_STRUCT.size

    __slots__ = ("m_zoneStart", "m_zoneEnd")

    def __init__(self, data: bytes) -> None:
        self.m_zoneStart: float
        self.m_zoneEnd: float
        self.m_zoneStart, self.m_zoneEnd = self.COMPILED_PACKET_STRUCT.unpack(data)

    def __str__(self) -> str:
        return f"DRSZone(Start: {self.m_zoneStart}, End: {self.m_zoneEnd})"

    def __eq__(self, other: "DRSZone") -> bool:
        if not isinstance(other, DRSZone):
            return False
        return self.m_zoneStart == other.m_zoneStart and self.m_zoneEnd == other.m_zoneEnd

    def __ne__(self, other: "DRSZone") -> bool:
        return not self.__eq__(other)

    def toJSON(self) -> Dict[str, Any]:
        return {"zone-start": self.m_zoneStart, "zone-end": self.m_zoneEnd}

    def to_bytes(self) -> bytes:
        return self.COMPILED_PACKET_STRUCT.pack(self.m_zoneStart, self.m_zoneEnd)


class PacketSessionData(F1PacketBase):
    """
    Represents an incoming packet containing session data.

    Attributes:
        - m_header (PacketHeader): Header information for the packet.
        - m_weather (WeatherCondition): Refer to the mentioned enumeration.
        - m_trackTemperature (int8): Track temperature in degrees Celsius.
        - m_airTemperature (int8): Air temperature in degrees Celsius.
        - m_totalLaps (uint8): Total number of laps in the race.
        - m_trackLength (uint16): Track length in meters.
        - m_sessionType (SessionType): Type of session (Refer SessionType enumeration).
        - m_trackId (TrackID): Track identifier. (Refer TrackID enumeration)
        - m_formula (uint8): Formula type ( 0 = F1 Modern, 1 = F1 Classic, 2 = F2, 3 = F1 Generic,
                                            4 = Beta, 5 = Supercars, 6 = Esports, 7 = F2 2021).
        - m_sessionTimeLeft (uint16): Time left in session in seconds.
        - m_sessionDuration (uint16): Session duration in seconds.
        - m_pitSpeedLimit (uint8): Pit speed limit in kilometers per hour.
        - m_gamePaused (uint8): Whether the game is paused in a network game.
        - m_isSpectating (uint8): Whether the player is spectating.
        - m_spectatorCarIndex (uint8): Index of the car being spectated.
        - m_sliProNativeSupport (uint8): SLI Pro support status (0 = inactive, 1 = active).
        - m_numMarshalZones (uint8): Number of marshal zones to follow.
        - m_marshalZones (list[MarshalZone]): List of MarshalZone objects (max 21).
        - m_safetyCarStatus (SafetyCarStatus): Safety car status (Refer SafetyCarStatus enumeration).
        - m_networkGame (uint8): Network game status (0 = offline, 1 = online).
        - m_numWeatherForecastSamples (uint8): Number of weather samples to follow.
        - m_weatherForecastSamples (list[WeatherForecastSample]): List of WeatherForecastSample objects (max 56).
        - m_forecastAccuracy (uint8): Forecast accuracy (0 = Perfect, 1 = Approximate).
        - m_aiDifficulty (uint8): AI Difficulty rating (0-110).
        - m_seasonLinkIdentifier (uint32): Identifier for the season (persists across saves).
        - m_weekendLinkIdentifier (uint32): Identifier for the weekend (persists across saves).
        - m_sessionLinkIdentifier (uint32): Identifier for the session (persists across saves).
        - m_pitStopWindowIdealLap (uint8): Ideal lap to pit on for the current strategy (player).
        - m_pitStopWindowLatestLap (uint8): Latest lap to pit on for the current strategy (player).
        - m_pitStopRejoinPosition (uint8): Predicted position to rejoin at (player).
        - m_steeringAssist (uint8): Steering assist status (0 = off, 1 = on).
        - m_brakingAssist (uint8): Braking assist status (0 = off, 1 = low, 2 = medium, 3 = high).
        - m_gearboxAssist (GearboxAssistMode): Gearbox assist mode (Refer GearboxAssistMode enumeration).
        - m_pitAssist (uint8): Pit assist status (0 = off, 1 = on).
        - m_pitReleaseAssist (uint8): Pit release assist status (0 = off, 1 = on).
        - m_ERSAssist (uint8): ERS assist status (0 = off, 1 = on).
        - m_DRSAssist (uint8): DRS assist status (0 = off, 1 = on).
        - m_dynamicRacingLine (uint8): Dynamic racing line status (0 = off, 1 = corners only, 2 = full).
        - m_dynamicRacingLineType (uint8): Dynamic racing line type (0 = 2D, 1 = 3D).
        - m_gameMode (uint8): Game mode ID.
        - m_ruleSet (uint8): Ruleset ID.
        - m_timeOfDay (uint32): Local time of day in minutes since midnight.
        - m_sessionLength (SessionLength): Session length. (Refer SessionLength enumeration).
        - m_speedUnitsLeadPlayer (uint8): Speed units for the lead player (0 = MPH, 1 = KPH).
        - m_temperatureUnitsLeadPlayer (uint8): Temperature units for the lead player (0 = Celsius, 1 = Fahrenheit).
        - m_speedUnitsSecondaryPlayer (uint8): Speed units for the secondary player (0 = MPH, 1 = KPH).
        - m_temperatureUnitsSecondaryPlayer (uint8): Temperature units for the secondary player
                                                    (0 = Celsius, 1 = Fahrenheit).
        - m_numSafetyCarPeriods (uint8): Number of safety car periods called during the session.
        - m_numVirtualSafetyCarPeriods (uint8): Number of virtual safety car periods called.
        - m_numRedFlagPeriods (uint8): Number of red flags called during the session.
    """

    F1_23_MAX_NUM_WEATHER_FORECAST_SAMPLES = 56
    F1_23_MAX_NUM_MARSHAL_ZONES = 21
    F1_24_MAX_NUM_WEATHER_FORECAST_SAMPLES = 64
    F1_24_MAX_NUM_MARSHAL_ZONES = 21
    F1_26_MAX_NUM_ACTIVE_AERO_ZONES = 8
    F1_26_MAX_NUM_DRS_ZONES = 4

    COMPILED_PACKET_STRUCT_SECTION_0 = struct.Struct("<"
        "B" # uint8           m_weather;                  // Weather - 0 = clear, 1 = light cloud, 2 = overcast
            #                                         // 3 = light rain, 4 = heavy rain, 5 = storm
        "b" # int8                m_trackTemperature;        // Track temp. in degrees celsius
        "b" # int8                m_airTemperature;          // Air temp. in degrees celsius
        "b" # uint8           m_totalLaps;               // Total number of laps in this race
        "H" # uint16          m_trackLength;               // Track length in metres
        "B" # uint8           m_sessionType;             // 0 = unknown, 1 = P1, 2 = P2, 3 = P3, 4 = Short P
            #                                             // 5 = Q1, 6 = Q2, 7 = Q3, 8 = Short Q, 9 = OSQ
            #                                             // 10 = R, 11 = R2, 12 = R3, 13 = Time Trial
        "b" # int8            m_trackId;                 // -1 for unknown, see appendix
        "B" # uint8           m_formula;           // Formula, 0 = F1 Modern, 1 = F1 Classic, 2 = F2,
            #                                      // 3 = F1 Generic, 4 = Beta, 5 = Supercars, 6 = Esports, 7 = F2 2021
        "H" # uint16          m_sessionTimeLeft;        // Time left in session in seconds
        "H" # uint16          m_sessionDuration;         // Session duration in seconds
        "B" # uint8           m_pitSpeedLimit;          // Pit speed limit in kilometres per hour
        "B" # uint8           m_gamePaused;                // Whether the game is paused – network game only
        "B" # uint8           m_isSpectating;            // Whether the player is spectating
        "B" # uint8           m_spectatorCarIndex;      // Index of the car being spectated
        "B" # uint8           m_sliProNativeSupport;    // SLI Pro support, 0 = inactive, 1 = active
        "B" # uint8           m_numMarshalZones;             // Number of marshal zones to follow
    )
    PACKET_LEN_SECTION_0 = COMPILED_PACKET_STRUCT_SECTION_0.size

    COMPILED_PACKET_STRUCT_SECTION_2 = struct.Struct("<"
        "B" # uint8           m_safetyCarStatus; // 0 = no safety car, 1 = full // 2 = virtual, 3 = formation lap
        "B" # uint8           m_networkGame;               // 0 = offline, 1 = online
        "B" # uint8           m_numWeatherForecastSamples; // Number of weather samples to follow
    )
    PACKET_LEN_SECTION_2 = COMPILED_PACKET_STRUCT_SECTION_2.size

    COMPILED_PACKET_STRUCT_SECTION_4 = struct.Struct("<"
        "B" # uint8   - Weather prediction type. 0 = Perfect, 1 = Approximate
        "B" # uint8   - AI Difficulty rating - 0-110
        "I" # uint32  - Identifier for season - persists across saves
        "I" # uint32  - Identifier for weekend - persists across saves
        "I" # uint32  - Identifier for session - persists across saves
        "B" # uint8   - Ideal lap to pit on for current strategy (player)
        "B" # uint8   - Latest lap to pit on for current strategy (player)
        "B" # uint8   - Predicted position to rejoin at (player)
        "B" # uint8   -m_steeringAssist;            // 0 = off, 1 = on
        "B" # uint8   -       m_brakingAssist;             // 0 = off, 1 = low, 2 = medium, 3 = high
        "B" # uint8   -        m_gearboxAssist;             // 1 = manual, 2 = manual & suggested gear, 3 = auto
        "B" # uint8    -       m_pitAssist;                 // 0 = off, 1 = on
        "B" # uint8    -       m_pitReleaseAssist;          // 0 = off, 1 = on
        "B" # uint8    -       m_ERSAssist;                 // 0 = off, 1 = on
        "B" # uint8    -       m_DRSAssist;                 // 0 = off, 1 = on
        "B" # uint8    -       m_dynamicRacingLine;         // 0 = off, 1 = corners only, 2 = full
        "B" # uint8    -       m_dynamicRacingLineType;     // 0 = 2D, 1 = 3D
        "B" # uint8    -       m_gameMode;                  // Game mode id - see appendix
        "B" # uint8    -       m_ruleSet;                   // Ruleset - see appendix
        "I" # uint32   - Local time of day - minutes since midnight
        "B" # uint8    - m_sessionLength;             // 0 = None, 2 = Very Short, 3 = Short, 4 = Medium
                                                    # // 5 = Medium Long, 6 = Long, 7 = Full
        "B" # uint8    -       m_speedUnitsLeadPlayer;             // 0 = MPH, 1 = KPH
        "B" # uint8    -       m_temperatureUnitsLeadPlayer;       // 0 = Celsius, 1 = Fahrenheit
        "B" # uint8    -       m_speedUnitsSecondaryPlayer;        // 0 = MPH, 1 = KPH
        "B" # uint8    -       m_temperatureUnitsSecondaryPlayer;  // 0 = Celsius, 1 = Fahrenheit
        "B" # uint8    -       m_numSafetyCarPeriods;              // Number of safety cars called during session
        "B" # uint8    -       m_numVirtualSafetyCarPeriods;       // Number of virtual safety cars called
        "B" # uint8    -       m_numRedFlagPeriods;                // Number of red flags called during session
    )
    PACKET_LEN_SECTION_4 = COMPILED_PACKET_STRUCT_SECTION_4.size

    # This is only for F1 24
    COMPILED_PACKET_STRUCT_SECTION_5 = struct.Struct("<"
        "B" # uint8   - car equal performance. 0 = off, 1 = on
        "B" # uint8    m_recoveryMode;              	// 0 = None, 1 = Flashbacks, 2 = Auto-recovery
        "B" # uint8    m_flashbackLimit;            	// 0 = Low, 1 = Medium, 2 = High, 3 = Unlimited
        "B" # uint8    m_surfaceType;               	// 0 = Simplified, 1 = Realistic
        "B" # uint8    m_lowFuelMode;               	// 0 = Easy, 1 = Hard
        "B" # uint8    m_raceStarts;			// 0 = Manual, 1 = Assisted
        "B" # uint8    m_tyreTemperature;           	// 0 = Surface only, 1 = Surface & Carcass
        "B" # uint8    m_pitLaneTyreSim;            	// 0 = On, 1 = Off
        "B" # uint8    m_carDamage;                 	// 0 = Off, 1 = Reduced, 2 = Standard, 3 = Simulation
        "B" # uint8    m_carDamageRate;                    // 0 = Reduced, 1 = Standard, 2 = Simulation
        "B" # uint8    m_collisions;                       // 0 = Off, 1 = Player-to-Player Off, 2 = On
        "B" # uint8    m_collisionsOffForFirstLapOnly;     // 0 = Disabled, 1 = Enabled
        "B" # uint8    m_mpUnsafePitRelease;               // 0 = On, 1 = Off (Multiplayer)
        "B" # uint8    m_mpOffForGriefing;                 // 0 = Disabled, 1 = Enabled (Multiplayer)
        "B" # uint8    m_cornerCuttingStringency;          // 0 = Regular, 1 = Strict
        "B" # uint8    m_parcFermeRules;                   // 0 = Off, 1 = On
        "B" # uint8    m_pitStopExperience;                // 0 = Automatic, 1 = Broadcast, 2 = Immersive
        "B" # uint8    m_safetyCar;                        // 0 = Off, 1 = Reduced, 2 = Standard, 3 = Increased
        "B" # uint8    m_safetyCarExperience;              // 0 = Broadcast, 1 = Immersive
        "B" # uint8    m_formationLap;                     // 0 = Off, 1 = On
        "B" # uint8    m_formationLapExperience;           // 0 = Broadcast, 1 = Immersive
        "B" # uint8    m_redFlags;                         // 0 = Off, 1 = Reduced, 2 = Standard, 3 = Increased
        "B" # uint8    m_affectsLicenceLevelSolo;          // 0 = Off, 1 = On
        "B" # uint8    m_affectsLicenceLevelMP;            // 0 = Off, 1 = On
        "B" # uint8    m_numSessionsInWeekend;             // Number of session in following array
        "12B" # uint8    m_weekendStructure[12];             // List of session types to show weekend
                               # // structure - see appendix for types
        "f" # float    m_sector2LapDistanceStart;          // Distance in m around track where sector 2 starts
        "f" # float    m_sector3LapDistanceStart;          // Distance in m around track where sector 3 starts
    )
    PACKET_LEN_SECTION_5 = COMPILED_PACKET_STRUCT_SECTION_5.size

    # F1 2026 section 6 — interleaved with ActiveAeroZone[8], ActiveAeroZone[8], DRSZone[4] arrays
    COMPILED_PACKET_STRUCT_SECTION_6_A = struct.Struct("<BB")   # m_activeAeroTrackStatus, m_numActiveAeroZonesFull
    PACKET_LEN_SECTION_6_A = COMPILED_PACKET_STRUCT_SECTION_6_A.size
    COMPILED_PACKET_STRUCT_SECTION_6_B = struct.Struct("<B")    # m_numActiveAeroZonesPartial
    PACKET_LEN_SECTION_6_B = COMPILED_PACKET_STRUCT_SECTION_6_B.size
    COMPILED_PACKET_STRUCT_SECTION_6_C = struct.Struct("<B")    # m_numDRSZones
    PACKET_LEN_SECTION_6_C = COMPILED_PACKET_STRUCT_SECTION_6_C.size
    COMPILED_PACKET_STRUCT_SECTION_6_D = struct.Struct("<fBBBBB")  # m_startReactionTime + 5×uint8
    PACKET_LEN_SECTION_6_D = COMPILED_PACKET_STRUCT_SECTION_6_D.size

    __slots__ = (
        "m_weather",
        "m_trackTemperature",
        "m_airTemperature",
        "m_totalLaps",
        "m_trackLength",
        "m_sessionType",
        "m_trackId",
        "m_formula",
        "m_sessionTimeLeft",
        "m_sessionDuration",
        "m_pitSpeedLimit",
        "m_gamePaused",
        "m_isSpectating",
        "m_spectatorCarIndex",
        "m_sliProNativeSupport",
        "m_numMarshalZones",
        "m_marshalZones",
        "m_safetyCarStatus",
        "m_networkGame",
        "m_numWeatherForecastSamples",
        "m_weatherForecastSamples",
        "m_forecastAccuracy",
        "m_aiDifficulty",
        "m_seasonLinkIdentifier",
        "m_weekendLinkIdentifier",
        "m_sessionLinkIdentifier",
        "m_pitStopWindowIdealLap",
        "m_pitStopWindowLatestLap",
        "m_pitStopRejoinPosition",
        "m_steeringAssist",
        "m_brakingAssist",
        "m_gearboxAssist",
        "m_pitAssist",
        "m_pitReleaseAssist",
        "m_ERSAssist",
        "m_DRSAssist",
        "m_dynamicRacingLine",
        "m_dynamicRacingLineType",
        "m_gameMode",
        "m_ruleSet",
        "m_timeOfDay",
        "m_sessionLength",
        "m_speedUnitsLeadPlayer",
        "m_temperatureUnitsLeadPlayer",
        "m_speedUnitsSecondaryPlayer",
        "m_temperatureUnitsSecondaryPlayer",
        "m_numSafetyCarPeriods",
        "m_numVirtualSafetyCarPeriods",
        "m_numRedFlagPeriods",
        "m_equalCarPerformance",
        "m_recoveryMode",
        "m_flashbackLimit",
        "m_surfaceType",
        "m_lowFuelMode",
        "m_raceStarts",
        "m_tyreTemperatureMode",
        "m_pitLaneTyreSim",
        "m_carDamage",
        "m_carDamageRate",
        "m_collisions",
        "m_collisionsOffForFirstLapOnly",
        "m_mpUnsafePitRelease",
        "m_mpOffForGriefing",
        "m_cornerCuttingStringency",
        "m_parcFermeRules",
        "m_pitStopExperience",
        "m_safetyCar",
        "m_safetyCarExperience",
        "m_formationLap",
        "m_formationLapExperience",
        "m_redFlags",
        "m_affectsLicenceLevelSolo",
        "m_affectsLicenceLevelMP",
        "m_numSessionsInWeekend",
        "m_weekendStructure",
        "m_sector2LapDistanceStart",
        "m_sector3LapDistanceStart",
        # F1 2026 fields
        "m_activeAeroTrackStatus",
        "m_numActiveAeroZonesFull",
        "m_activeAeroZonesFull",
        "m_numActiveAeroZonesPartial",
        "m_activeAeroZonesPartial",
        "m_numDRSZones",
        "m_drsZones",
        "m_startReactionTime",
        "m_antiLockBrakesAssist",
        "m_tractionControlAssist",
        "m_dynamicRacingLineHiVis",
        "m_dynamicRacingLineColourBlind",
        "m_recurringRewindPrompt",
    )

    class FormulaType(F1BaseEnum):
        """An enumeration of formula types."""

        F1_MODERN: int = 0
        F1_CLASSIC: int = 1
        F2: int = 2
        F1_GENERIC: int = 3
        BETA: int = 4
        SUPERCARS: int = 5
        ESPORTS: int = 6
        F2_2021: int = 7
        F1_WORLD: int = 8
        F1_ELIMINATION: int = 9
        F1_26: int = 13

        def __str__(self) -> str:
            """Return a human-readable string representation of the formula type."""
            return {
                PacketSessionData.FormulaType.F1_MODERN: "F1 Modern",
                PacketSessionData.FormulaType.F1_CLASSIC: "F1 Classic",
                PacketSessionData.FormulaType.F2: "F2",
                PacketSessionData.FormulaType.F1_GENERIC: "F1 Generic",
                PacketSessionData.FormulaType.BETA: "Beta",
                PacketSessionData.FormulaType.SUPERCARS: "Supercars",
                PacketSessionData.FormulaType.ESPORTS: "Esports",
                PacketSessionData.FormulaType.F2_2021: "F2 2021",
                PacketSessionData.FormulaType.F1_WORLD: "F1 World",
                PacketSessionData.FormulaType.F1_ELIMINATION: "F1 Elimination",
                PacketSessionData.FormulaType.F1_26: "F1 26",
            }[self]

        def is_f1(self) -> bool:
            """Check if the formula type is F1."""
            return self in [
                PacketSessionData.FormulaType.F1_MODERN,
                PacketSessionData.FormulaType.F1_CLASSIC,
                PacketSessionData.FormulaType.F1_GENERIC,
                PacketSessionData.FormulaType.F1_WORLD,
                PacketSessionData.FormulaType.F1_ELIMINATION,
                PacketSessionData.FormulaType.F1_26,
            ]

        def is_f2(self) -> bool:
            """Check if the formula type is F2."""
            return self in [
                PacketSessionData.FormulaType.F2,
                PacketSessionData.FormulaType.F2_2021
            ]

    class RecoveryMode(F1BaseEnum):
        """
        ENUM class for the recovery type modes
        """
        NONE = 0
        FLASHBACKS = 1
        AUTO_RECOVERY = 2

    class FlashbackLimit(F1BaseEnum):
        """
        ENUM class for the flashback limit types
        """
        LOW = 0
        MEDIUM = 1
        HIGH = 2
        UNLIMITED = 3

    class SurfaceType(F1BaseEnum):
        """
        ENUM class for the surface types
        """
        SIMPLIFIED = 0
        REALISTIC = 1

    class LowFuelMode(F1BaseEnum):
        """
        ENUM class for the low fuel mode types
        """
        EASY = 0
        HARD = 1

    class RaceStartsMode(F1BaseEnum):
        """
        ENUM class for the race starts mode types
        """
        MANUAL = 0
        ASSISTED = 1

    class TyreTemperatureMode(F1BaseEnum):
        """
        ENUM class for the tyre temperature mode types
        """
        SURFACE_ONLY = 0
        SURFACE_AND_CARCASS = 1

    class CarDamageMode(F1BaseEnum):
        """
        ENUM class for the car damage mode types
        """
        OFF = 0
        REDUCED = 1
        STANDARD = 2
        SIMULATION = 3

    class CarDamageRate(F1BaseEnum):
        """
        ENUM class for the car damage rate types
        """
        REDUCED = 0
        STANDARD = 1
        SIMULATION = 2

    class CollisionsMode(F1BaseEnum):
        """
        ENUM class for the collisions mode types
        """
        OFF = 0
        PLAYER_TO_PLAYER_OFF = 1
        ON = 2

    class CornerCuttingStringency(F1BaseEnum):
        """
        ENUM class for the corner cutting stringency types
        """
        REGULAR = 0
        STRICT = 1

    class PitStopExperience(F1BaseEnum):
        """
        ENUM class for the pit stop experience types
        """
        AUTOMATIC = 0
        BROADCAST = 1
        IMMERSIVE = 2

    class SafetyCarSetting(F1BaseEnum):
        """
        ENUM class for the safety car setting types
        """
        OFF = 0
        REDUCED = 1
        STANDARD = 2
        INCREASED = 3

    class SafetyCarExperience(F1BaseEnum):
        """
        ENUM class for the safety car experience types
        """
        BROADCAST = 0
        IMMERSIVE = 1

    class FormationLapExperience(F1BaseEnum):
        """
        ENUM class for the formation lap experience types
        """
        BROADCAST = 0
        IMMERSIVE = 1

    class RedFlagsSetting(F1BaseEnum):
        """
        ENUM class for the red flags setting types
        """
        OFF = 0
        REDUCED = 1
        STANDARD = 2
        INCREASED = 3

    class ActiveAeroTrackStatus(F1BaseEnum):
        """Active aero track coverage mode (F1 2026+)."""
        FULL = 0
        PARTIAL = 1

    class TractionControlAssistMode(F1BaseEnum):
        """Traction control assist level (F1 2026+)."""
        OFF = 0
        MEDIUM = 1
        FULL = 2

    class DynamicRacingLineColourBlindMode(F1BaseEnum):
        """Colour-blind mode for the dynamic racing line (F1 2026+)."""
        OFF = 0
        PROTANOPIA = 1
        DEUTERANOPIA = 2
        TRITANOPIA = 3

    def __init__(self, header: PacketHeader, data: bytes) -> None:
        """Construct a PacketSessionData object

        Args:
            header (PacketHeader): The parsed header object
            data (bytes): The list of raw bytes representing this packet
        """
        super().__init__(header)

        # Declare the type hints
        self.m_weather: WeatherForecastSample.WeatherCondition
        self.m_trackTemperature: int
        self.m_airTemperature: int
        self.m_totalLaps: int
        self.m_trackLength: int
        self.m_sessionType: Union[SessionType23, SessionType24]
        self.m_trackId: TrackID
        self.m_formula: PacketSessionData.FormulaType
        self.m_sessionTimeLeft: int
        self.m_sessionDuration: int
        self.m_pitSpeedLimit: int
        self.m_gamePaused: bool
        self.m_isSpectating: bool
        self.m_spectatorCarIndex: int
        self.m_sliProNativeSupport: int
        self.m_numMarshalZones: int
        self.m_marshalZones: List[MarshalZone]
        self.m_safetyCarStatus : SafetyCarType
        self.m_networkGame: bool
        self.m_numWeatherForecastSamples: int
        self.m_weatherForecastSamples: List[WeatherForecastSample]
        self.m_forecastAccuracy : int
        self.m_aiDifficulty: int
        self.m_seasonLinkIdentifier: int
        self.m_weekendLinkIdentifier: int
        self.m_sessionLinkIdentifier: int
        self.m_pitStopWindowIdealLap: int
        self.m_pitStopWindowLatestLap: int
        self.m_pitStopRejoinPosition: int
        self.m_steeringAssist: int
        self.m_brakingAssist: int
        self.m_gearboxAssist: GearboxAssistMode
        self.m_pitAssist: int
        self.m_pitReleaseAssist: int
        self.m_ERSAssist: int
        self.m_DRSAssist: int
        self.m_dynamicRacingLine: int
        self.m_dynamicRacingLineType: int
        self.m_gameMode: GameMode
        self.m_ruleSet: RuleSet
        self.m_timeOfDay: int
        self.m_sessionLength: SessionLength
        self.m_speedUnitsLeadPlayer: int
        self.m_temperatureUnitsLeadPlayer: int
        self.m_speedUnitsSecondaryPlayer: int
        self.m_temperatureUnitsSecondaryPlayer: int
        self.m_numSafetyCarPeriods: int
        self.m_numVirtualSafetyCarPeriods: int
        self.m_numRedFlagPeriods: int

        # F1 24 specific stuff
        self.m_equalCarPerformance: bool
        self.m_recoveryMode: PacketSessionData.RecoveryMode
        self.m_flashbackLimit: PacketSessionData.FlashbackLimit
        self.m_surfaceType: PacketSessionData.SurfaceType
        self.m_lowFuelMode: PacketSessionData.LowFuelMode
        self.m_raceStarts: PacketSessionData.RaceStartsMode
        self.m_tyreTemperatureMode: PacketSessionData.TyreTemperatureMode
        self.m_pitLaneTyreSim:bool
        self.m_carDamage: PacketSessionData.CarDamageMode
        self.m_carDamageRate: PacketSessionData.CarDamageRate
        self.m_collisions: PacketSessionData.CollisionsMode
        self.m_collisionsOffForFirstLapOnly: bool
        self.m_mpUnsafePitRelease:bool
        self.m_mpOffForGriefing: bool
        self.m_cornerCuttingStringency: PacketSessionData.CornerCuttingStringency
        self.m_parcFermeRules: bool
        self.m_pitStopExperience: PacketSessionData.PitStopExperience
        self.m_safetyCar: PacketSessionData.SafetyCarSetting
        self.m_safetyCarExperience: PacketSessionData.SafetyCarExperience
        self.m_formationLap: bool
        self.m_formationLapExperience: PacketSessionData.FormationLapExperience
        self.m_redFlags: PacketSessionData.RedFlagsSetting
        self.m_affectsLicenceLevelSolo: bool
        self.m_affectsLicenceLevelMP: bool
        self.m_numSessionsInWeekend: int         # // Number of session in following array
        self.m_weekendStructure: List[SessionType24] # List of SessionType24 enums in this weekend
        self.m_sector2LapDistanceStart: float    # // Distance in m around track where sector 2 starts
        self.m_sector3LapDistanceStart: float    # // Distance in m around track where sector 3

        # F1 2026 fields
        self.m_activeAeroTrackStatus: PacketSessionData.ActiveAeroTrackStatus
        self.m_numActiveAeroZonesFull: int
        self.m_activeAeroZonesFull: List[ActiveAeroZone]
        self.m_numActiveAeroZonesPartial: int
        self.m_activeAeroZonesPartial: List[ActiveAeroZone]
        self.m_numDRSZones: int
        self.m_drsZones: List[DRSZone]
        self.m_startReactionTime: float
        self.m_antiLockBrakesAssist: bool
        self.m_tractionControlAssist: PacketSessionData.TractionControlAssistMode
        self.m_dynamicRacingLineHiVis: int
        self.m_dynamicRacingLineColourBlind: PacketSessionData.DynamicRacingLineColourBlindMode
        self.m_recurringRewindPrompt: int

        offset = self._parse_base(data, header.m_packetFormat)
        offset = self._parse_f24(data, offset, header.m_packetFormat)
        self._parse_f26(data, offset, header.m_packetFormat)
        self._cast_enums(header.m_packetFormat)

    def _parse_base(self, data: bytes, fmt: int) -> int:
        """Parse fields present in all packet formats. Returns byte offset after consumed data."""
        max_weather_forecast_samples = (
            self.F1_23_MAX_NUM_WEATHER_FORECAST_SAMPLES if fmt == 2023
            else self.F1_24_MAX_NUM_WEATHER_FORECAST_SAMPLES
        )

        # First, section 0
        byte_index_so_far = self.PACKET_LEN_SECTION_0
        (
            self.m_weather,
            self.m_trackTemperature,
            self.m_airTemperature,
            self.m_totalLaps,
            self.m_trackLength,
            self.m_sessionType,
            self.m_trackId,
            self.m_formula,
            self.m_sessionTimeLeft,
            self.m_sessionDuration,
            self.m_pitSpeedLimit,
            self.m_gamePaused,
            self.m_isSpectating,
            self.m_spectatorCarIndex,
            self.m_sliProNativeSupport,
            self.m_numMarshalZones,
        ) = self.COMPILED_PACKET_STRUCT_SECTION_0.unpack(data[:self.PACKET_LEN_SECTION_0])

        # Next section 1, marshalZones
        self.m_marshalZones, byte_index_so_far = MarshalZone.parse_array(
            data=data,
            offset=byte_index_so_far,
            item_len=MarshalZone.PACKET_LEN,
            count=self.m_numMarshalZones,
            max_count=self.F1_23_MAX_NUM_MARSHAL_ZONES,
        )

        # Section 2, till numWeatherForecastSamples
        (
            self.m_safetyCarStatus, #           // 0 = no safety car, 1 = full 2 = virtual, 3 = formation lap
            self.m_networkGame,     #           // 0 = offline, 1 = online
            self.m_numWeatherForecastSamples,   # // Number of weather samples to follow
        ) = self.COMPILED_PACKET_STRUCT_SECTION_2.unpack(
            data[byte_index_so_far:byte_index_so_far + self.PACKET_LEN_SECTION_2]
        )
        byte_index_so_far += self.PACKET_LEN_SECTION_2

        # Section 3 - weather forecast samples
        self.m_weatherForecastSamples, byte_index_so_far = WeatherForecastSample.parse_array(
            data=data,
            offset=byte_index_so_far,
            item_len=WeatherForecastSample.PACKET_LEN,
            count=self.m_numWeatherForecastSamples,
            max_count=max_weather_forecast_samples,
            packet_format=fmt,
        )

        # Section 4 - rest of the packet
        (
            self.m_forecastAccuracy,                   # uint8
            self.m_aiDifficulty,                       # uint8
            self.m_seasonLinkIdentifier,              # uint32
            self.m_weekendLinkIdentifier,             # uint32
            self.m_sessionLinkIdentifier,             # uint32
            self.m_pitStopWindowIdealLap,             # uint8
            self.m_pitStopWindowLatestLap,            # uint8
            self.m_pitStopRejoinPosition,             # uint8
            self.m_steeringAssist,                    # uint8
            self.m_brakingAssist,                     # uint8
            self.m_gearboxAssist,                     # uint8
            self.m_pitAssist,                         # uint8
            self.m_pitReleaseAssist,                  # uint8
            self.m_ERSAssist,                         # uint8
            self.m_DRSAssist,                         # uint8
            self.m_dynamicRacingLine,                # uint8
            self.m_dynamicRacingLineType,            # uint8
            self.m_gameMode,                          # uint8
            self.m_ruleSet,                           # uint8
            self.m_timeOfDay,                         # uint32
            self.m_sessionLength,                     # uint8
            self.m_speedUnitsLeadPlayer,             # uint8
            self.m_temperatureUnitsLeadPlayer,       # uint8
            self.m_speedUnitsSecondaryPlayer,        # uint8
            self.m_temperatureUnitsSecondaryPlayer,  # uint8
            self.m_numSafetyCarPeriods,              # uint8
            self.m_numVirtualSafetyCarPeriods,       # uint8
            self.m_numRedFlagPeriods,                # uint8
        ) = self.COMPILED_PACKET_STRUCT_SECTION_4.unpack(
            data[byte_index_so_far:byte_index_so_far + self.PACKET_LEN_SECTION_4]
        )
        byte_index_so_far += self.PACKET_LEN_SECTION_4

        return byte_index_so_far

    def _parse_f24(self, data: bytes, offset: int, fmt: int) -> int:
        """Parse F1 24/26 fields (section 5). Assigns zero defaults for other formats. Returns updated offset."""
        if fmt >= 2024:
            (
                self.m_equalCarPerformance,         # uint8 - car equal performance. 0 = off, 1 = on
                self.m_recoveryMode,                # uint8 - 0 = None, 1 = Flashbacks, 2 = Auto-recovery
                self.m_flashbackLimit,              # uint8 - 0 = Low, 1 = Medium, 2 = High, 3 = Unlimited
                self.m_surfaceType,                 # uint8 - 0 = Simplified, 1 = Realistic
                self.m_lowFuelMode,                 # uint8 - 0 = Easy, 1 = Hard
                self.m_raceStarts,                  # uint8 - 0 = Manual, 1 = Assisted
                self.m_tyreTemperatureMode,         # uint8 - 0 = Surface only, 1 = Surface & Carcass
                self.m_pitLaneTyreSim,              # uint8 - 0 = On, 1 = Off
                self.m_carDamage,                   # uint8 - 0 = Off, 1 = Reduced, 2 = Standard, 3 = Simulation
                self.m_carDamageRate,               # uint8 - 0 = Reduced, 1 = Standard, 2 = Simulation
                self.m_collisions,                  # uint8 - 0 = Off, 1 = Player-to-Player Off, 2 = On
                self.m_collisionsOffForFirstLapOnly, # uint8 - 0 = Disabled, 1 = Enabled
                self.m_mpUnsafePitRelease,          # uint8 - 0 = On, 1 = Off (Multiplayer)
                self.m_mpOffForGriefing,            # uint8 - 0 = Disabled, 1 = Enabled (Multiplayer)
                self.m_cornerCuttingStringency,     # uint8 - 0 = Regular, 1 = Strict
                self.m_parcFermeRules,              # uint8 - 0 = Off, 1 = On
                self.m_pitStopExperience,           # uint8 - 0 = Automatic, 1 = Broadcast, 2 = Immersive
                self.m_safetyCar,                   # uint8 - 0 = Off, 1 = Reduced, 2 = Standard, 3 = Increased
                self.m_safetyCarExperience,         # uint8 - 0 = Broadcast, 1 = Immersive
                self.m_formationLap,                # uint8 - 0 = Off, 1 = On
                self.m_formationLapExperience,      # uint8 - 0 = Broadcast, 1 = Immersive
                self.m_redFlags,                    # uint8 - 0 = Off, 1 = Reduced, 2 = Standard, 3 = Increased
                self.m_affectsLicenceLevelSolo,     # uint8 - 0 = Off, 1 = On
                self.m_affectsLicenceLevelMP,       # uint8 - 0 = Off, 1 = On
                self.m_numSessionsInWeekend,        # uint8 - Number of session in following array
                ws0, ws1, ws2, ws3, ws4, ws5, ws6, ws7, ws8, ws9, ws10, ws11,  # uint8[12] - weekend structure
                self.m_sector2LapDistanceStart,     # float - Distance in m around track where sector 2 starts
                self.m_sector3LapDistanceStart,     # float - Distance in m around track where sector 3 starts
            ) = self.COMPILED_PACKET_STRUCT_SECTION_5.unpack(
                data[offset:offset + self.PACKET_LEN_SECTION_5]
            )
            self.m_weekendStructure = [
                SessionType24(s) for s in
                (ws0, ws1, ws2, ws3, ws4, ws5, ws6, ws7, ws8, ws9, ws10, ws11)[:self.m_numSessionsInWeekend]
            ]
            return offset + self.PACKET_LEN_SECTION_5

        self.m_equalCarPerformance = 0
        self.m_recoveryMode = 0
        self.m_flashbackLimit = 0
        self.m_surfaceType = 0
        self.m_lowFuelMode = 0
        self.m_raceStarts = 0
        self.m_tyreTemperatureMode = 0
        self.m_pitLaneTyreSim = 0
        self.m_carDamage = 0
        self.m_carDamageRate = 0
        self.m_collisions = 0
        self.m_collisionsOffForFirstLapOnly = 0
        self.m_mpUnsafePitRelease = 0
        self.m_mpOffForGriefing = 0
        self.m_cornerCuttingStringency = 0
        self.m_parcFermeRules = 0
        self.m_pitStopExperience = 0
        self.m_safetyCar = 0
        self.m_safetyCarExperience = 0
        self.m_formationLap = 0
        self.m_formationLapExperience = 0
        self.m_redFlags = 0
        self.m_affectsLicenceLevelSolo = 0
        self.m_affectsLicenceLevelMP = 0
        self.m_numSessionsInWeekend = 0
        self.m_weekendStructure = [0] * 12
        self.m_sector2LapDistanceStart = 0.0
        self.m_sector3LapDistanceStart = 0.0
        return offset

    def _parse_f26(self, data: bytes, offset: int, fmt: int) -> int:
        """Parse F1 2026-only fields (section 6). Assigns zero/empty defaults for older formats."""
        if fmt == 2026:
            (
                self.m_activeAeroTrackStatus,
                self.m_numActiveAeroZonesFull,
            ) = self.COMPILED_PACKET_STRUCT_SECTION_6_A.unpack(
                data[offset:offset + self.PACKET_LEN_SECTION_6_A]
            )
            offset += self.PACKET_LEN_SECTION_6_A

            self.m_activeAeroZonesFull, offset = ActiveAeroZone.parse_array(
                data=data,
                offset=offset,
                item_len=ActiveAeroZone.PACKET_LEN,
                count=self.m_numActiveAeroZonesFull,
                max_count=self.F1_26_MAX_NUM_ACTIVE_AERO_ZONES,
            )

            (self.m_numActiveAeroZonesPartial,) = self.COMPILED_PACKET_STRUCT_SECTION_6_B.unpack(
                data[offset:offset + self.PACKET_LEN_SECTION_6_B]
            )
            offset += self.PACKET_LEN_SECTION_6_B

            self.m_activeAeroZonesPartial, offset = ActiveAeroZone.parse_array(
                data=data,
                offset=offset,
                item_len=ActiveAeroZone.PACKET_LEN,
                count=self.m_numActiveAeroZonesPartial,
                max_count=self.F1_26_MAX_NUM_ACTIVE_AERO_ZONES,
            )

            (self.m_numDRSZones,) = self.COMPILED_PACKET_STRUCT_SECTION_6_C.unpack(
                data[offset:offset + self.PACKET_LEN_SECTION_6_C]
            )
            offset += self.PACKET_LEN_SECTION_6_C

            self.m_drsZones, offset = DRSZone.parse_array(
                data=data,
                offset=offset,
                item_len=DRSZone.PACKET_LEN,
                count=self.m_numDRSZones,
                max_count=self.F1_26_MAX_NUM_DRS_ZONES,
            )

            (
                self.m_startReactionTime,
                self.m_antiLockBrakesAssist,
                self.m_tractionControlAssist,
                self.m_dynamicRacingLineHiVis,
                self.m_dynamicRacingLineColourBlind,
                self.m_recurringRewindPrompt,
            ) = self.COMPILED_PACKET_STRUCT_SECTION_6_D.unpack(
                data[offset:offset + self.PACKET_LEN_SECTION_6_D]
            )
            return offset + self.PACKET_LEN_SECTION_6_D

        self.m_activeAeroTrackStatus = 0
        self.m_numActiveAeroZonesFull = 0
        self.m_activeAeroZonesFull = []
        self.m_numActiveAeroZonesPartial = 0
        self.m_activeAeroZonesPartial = []
        self.m_numDRSZones = 0
        self.m_drsZones = []
        self.m_startReactionTime = 0.0
        self.m_antiLockBrakesAssist = 0
        self.m_tractionControlAssist = 0
        self.m_dynamicRacingLineHiVis = 0
        self.m_dynamicRacingLineColourBlind = 0
        self.m_recurringRewindPrompt = 0
        return offset

    def _cast_enums(self, fmt: int) -> None:
        """Apply enum casts to all parsed fields."""
        self.m_isSpectating = bool(self.m_isSpectating)
        self.m_weather = WeatherForecastSample.WeatherCondition.safeCast(self.m_weather)
        self.m_trackId = TrackID.safeCast(self.m_trackId)
        if fmt == 2023:
            self.m_sessionType = SessionType23.safeCast(self.m_sessionType)
        else:
            self.m_sessionType = SessionType24.safeCast(self.m_sessionType)
        self.m_formula = PacketSessionData.FormulaType.safeCast(self.m_formula)
        self.m_safetyCarStatus = SafetyCarType.safeCast(self.m_safetyCarStatus)
        self.m_gearboxAssist = GearboxAssistMode.safeCast(self.m_gearboxAssist)
        self.m_sessionLength = SessionLength.safeCast(self.m_sessionLength)
        self.m_gameMode = GameMode.safeCast(self.m_gameMode)
        self.m_ruleSet = RuleSet.safeCast(self.m_ruleSet)
        self.m_equalCarPerformance = bool(self.m_equalCarPerformance)
        self.m_recoveryMode = PacketSessionData.RecoveryMode.safeCast(self.m_recoveryMode)
        self.m_flashbackLimit = PacketSessionData.FlashbackLimit.safeCast(self.m_flashbackLimit)
        self.m_surfaceType = PacketSessionData.SurfaceType.safeCast(self.m_surfaceType)
        self.m_lowFuelMode = PacketSessionData.LowFuelMode.safeCast(self.m_lowFuelMode)
        self.m_raceStarts = PacketSessionData.RaceStartsMode.safeCast(self.m_raceStarts)
        self.m_tyreTemperatureMode = PacketSessionData.TyreTemperatureMode.safeCast(self.m_tyreTemperatureMode)
        self.m_carDamage = PacketSessionData.CarDamageMode.safeCast(self.m_carDamage)
        self.m_carDamageRate = PacketSessionData.CarDamageRate.safeCast(self.m_carDamageRate)
        self.m_collisions = PacketSessionData.CollisionsMode.safeCast(self.m_collisions)
        self.m_cornerCuttingStringency = PacketSessionData.CornerCuttingStringency.safeCast(
            self.m_cornerCuttingStringency)
        self.m_pitStopExperience = PacketSessionData.PitStopExperience.safeCast(self.m_pitStopExperience)
        self.m_safetyCar = PacketSessionData.SafetyCarSetting.safeCast(self.m_safetyCar)
        self.m_safetyCarExperience = PacketSessionData.SafetyCarExperience.safeCast(self.m_safetyCarExperience)
        self.m_formationLapExperience = PacketSessionData.FormationLapExperience.safeCast(self.m_formationLapExperience)
        self.m_redFlags = PacketSessionData.RedFlagsSetting.safeCast(self.m_redFlags)
        if fmt == 2026:
            self.m_activeAeroTrackStatus = PacketSessionData.ActiveAeroTrackStatus.safeCast(
                self.m_activeAeroTrackStatus)
            self.m_antiLockBrakesAssist = bool(self.m_antiLockBrakesAssist)
            self.m_tractionControlAssist = PacketSessionData.TractionControlAssistMode.safeCast(
                self.m_tractionControlAssist)
            self.m_dynamicRacingLineColourBlind = PacketSessionData.DynamicRacingLineColourBlindMode.safeCast(
                self.m_dynamicRacingLineColourBlind)

    def __str__(self) -> str:
        """
        Return a string representation of the PacketSessionData object.

        Returns:
            str - string representation of this object
        """
        marshal_zones_str = ", ".join(str(zone) for zone in self.m_marshalZones)
        weather_forecast_samples_str = ", ".join(str(sample) for sample in self.m_weatherForecastSamples)

        return (
            f"PacketSessionData("
            f"Header: {str(self.m_header)}, "
            f"Weather: {self.m_weather}, "
            f"Track Temperature: {self.m_trackTemperature}, "
            f"Air Temperature: {self.m_airTemperature}, "
            f"Total Laps: {self.m_totalLaps}, "
            f"Track Length: {self.m_trackLength}, "
            f"Session Type: {str(self.m_sessionType)}, "
            f"Track ID: {str(self.m_trackId)}, "
            f"Formula: {str(self.m_formula)}, "
            f"Session Time Left: {self.m_sessionTimeLeft}, "
            f"Session Duration: {self.m_sessionDuration}, "
            f"Pit Speed Limit: {self.m_pitSpeedLimit}, "
            f"Game Paused: {self.m_gamePaused}, "
            f"Spectating: {self.m_isSpectating}, "
            f"Spectator Car Index: {self.m_spectatorCarIndex}, "
            f"SLI Pro Support: {self.m_sliProNativeSupport}, "
            f"Num Marshal Zones: {self.m_numMarshalZones}, "
            f"Marshal Zones: [{marshal_zones_str}], "
            f"Safety Car Status: {self.m_safetyCarStatus}, "
            f"Network Game: {self.m_networkGame}, "
            f"Num Weather Forecast Samples: {self.m_numWeatherForecastSamples}, "
            f"Weather Forecast Samples: [{weather_forecast_samples_str}], "
            f"Forecast Accuracy: {self.m_forecastAccuracy}, "
            f"AI Difficulty: {self.m_aiDifficulty}, "
            f"Season Link ID: {self.m_seasonLinkIdentifier}, "
            f"Weekend Link ID: {self.m_weekendLinkIdentifier}, "
            f"Session Link ID: {self.m_sessionLinkIdentifier}, "
            f"Pit Stop Window Ideal Lap: {self.m_pitStopWindowIdealLap}, "
            f"Pit Stop Window Latest Lap: {self.m_pitStopWindowLatestLap}, "
            f"Pit Stop Rejoin Position: {self.m_pitStopRejoinPosition}, "
            f"Steering Assist: {self.m_steeringAssist}, "
            f"Braking Assist: {self.m_brakingAssist}, "
            f"Gearbox Assist: {self.m_gearboxAssist}, "
            f"Pit Assist: {self.m_pitAssist}, "
            f"Pit Release Assist: {self.m_pitReleaseAssist}, "
            f"ERS Assist: {self.m_ERSAssist}, "
            f"DRS Assist: {self.m_DRSAssist}, "
            f"Dynamic Racing Line: {self.m_dynamicRacingLine}, "
            f"Dynamic Racing Line Type: {self.m_dynamicRacingLineType}, "
            f"Game Mode: {str(self.m_gameMode)}, "
            f"Rule Set: {str(self.m_ruleSet)}, "
            f"Time of Day: {self.m_timeOfDay}, "
            f"Session Length: {self.m_sessionLength}, "
            f"Speed Units Lead Player: {self.m_speedUnitsLeadPlayer}, "
            f"Temp Units Lead Player: {self.m_temperatureUnitsLeadPlayer}, "
            f"Speed Units Secondary Player: {self.m_speedUnitsSecondaryPlayer}, "
            f"Temp Units Secondary Player: {self.m_temperatureUnitsSecondaryPlayer}, "
            f"Num Safety Car Periods: {self.m_numSafetyCarPeriods}, "
            f"Num Virtual Safety Car Periods: {self.m_numVirtualSafetyCarPeriods}, "
            f"Num Red Flag Periods: {self.m_numRedFlagPeriods}, "
            f"Active Aero Track Status: {self.m_activeAeroTrackStatus}, "
            f"Num Active Aero Zones Full: {self.m_numActiveAeroZonesFull}, "
            f"Active Aero Zones Full: {[str(z) for z in self.m_activeAeroZonesFull]}, "
            f"Num Active Aero Zones Partial: {self.m_numActiveAeroZonesPartial}, "
            f"Active Aero Zones Partial: {[str(z) for z in self.m_activeAeroZonesPartial]}, "
            f"Num DRS Zones: {self.m_numDRSZones}, "
            f"DRS Zones: {[str(z) for z in self.m_drsZones]}, "
            f"Start Reaction Time: {self.m_startReactionTime}, "
            f"Anti-Lock Brakes Assist: {self.m_antiLockBrakesAssist}, "
            f"Traction Control Assist: {self.m_tractionControlAssist}, "
            f"Dynamic Racing Line Hi-Vis: {self.m_dynamicRacingLineHiVis}, "
            f"Dynamic Racing Line Colour Blind: {self.m_dynamicRacingLineColourBlind}, "
            f"Recurring Rewind Prompt: {self.m_recurringRewindPrompt})"
        )

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """Converts the PacketSessionData object to a dictionary suitable for JSON serialization.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """
        json_data = self._base_json() | self._f24_json() | self._f26_json()
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

    def _base_json(self) -> Dict[str, Any]:
        """Return JSON dict for fields present in all packet formats."""
        return {
            "weather": str(self.m_weather),
            "track-temperature": self.m_trackTemperature,
            "air-temperature": self.m_airTemperature,
            "total-laps": self.m_totalLaps,
            "track-length": self.m_trackLength,
            "session-type": str(self.m_sessionType),
            "track-id": str(self.m_trackId),
            "formula": str(self.m_formula),
            "session-time-left": self.m_sessionTimeLeft,
            "session-duration": self.m_sessionDuration,
            "pit-speed-limit": self.m_pitSpeedLimit,
            "game-paused": self.m_gamePaused,
            "is-spectating": self.m_isSpectating,
            "spectator-car-index": self.m_spectatorCarIndex,
            "sli-pro-native-support": self.m_sliProNativeSupport,
            "num-marshal-zones": self.m_numMarshalZones,
            "marshal-zones": [zone.toJSON() for zone in self.m_marshalZones],
            "safety-car-status": str(self.m_safetyCarStatus),
            "network-game": self.m_networkGame,
            "num-weather-forecast-samples": self.m_numWeatherForecastSamples,
            "weather-forecast-samples": [sample.toJSON() for sample in self.m_weatherForecastSamples],
            "forecast-accuracy": self.m_forecastAccuracy,
            "ai-difficulty": self.m_aiDifficulty,
            "season-link-identifier": self.m_seasonLinkIdentifier,
            "weekend-link-identifier": self.m_weekendLinkIdentifier,
            "session-link-identifier": self.m_sessionLinkIdentifier,
            "pit-stop-window-ideal-lap": self.m_pitStopWindowIdealLap,
            "pit-stop-window-latest-lap": self.m_pitStopWindowLatestLap,
            "pit-stop-rejoin-position": self.m_pitStopRejoinPosition,
            "steering-assist": self.m_steeringAssist,
            "braking-assist": self.m_brakingAssist,
            "gearbox-assist": str(self.m_gearboxAssist),
            "pit-assist": self.m_pitAssist,
            "pit-release-assist": self.m_pitReleaseAssist,
            "ers-assist": self.m_ERSAssist,
            "drs-assist": self.m_DRSAssist,
            "dynamic-racing-line": self.m_dynamicRacingLine,
            "dynamic-racing-line-type": self.m_dynamicRacingLineType,
            "game-mode": str(self.m_gameMode),
            "rule-set": str(self.m_ruleSet),
            "time-of-day": self.m_timeOfDay,
            "session-length": str(self.m_sessionLength),
            "speed-units-lead-player": self.m_speedUnitsLeadPlayer,
            "temp-units-lead-player": self.m_temperatureUnitsLeadPlayer,
            "speed-units-secondary-player": self.m_speedUnitsSecondaryPlayer,
            "temp-units-secondary-player": self.m_temperatureUnitsSecondaryPlayer,
            "num-safety-car-periods": self.m_numSafetyCarPeriods,
            "num-virtual-safety-car-periods": self.m_numVirtualSafetyCarPeriods,
            "num-red-flag-periods": self.m_numRedFlagPeriods,
        }

    def _f24_json(self) -> Dict[str, Any]:
        """Return JSON dict for F1 24+ fields."""
        return {
            "equal-car-performance" : bool(self.m_equalCarPerformance),
            "recovery-mode" : str(self.m_recoveryMode),
            "flashback-limit" : str(self.m_flashbackLimit),
            "surface-type" : str(self.m_surfaceType),
            "low-fuel-mode" : str(self.m_lowFuelMode),
            "race-starts" : str(self.m_raceStarts),
            "tyre-temperature-mode" : str(self.m_tyreTemperatureMode),
            "pit-lane-tyre-sim" : str(self.m_pitLaneTyreSim),
            "car-damage" : str(self.m_carDamage),
            "car-damage-rate" : str(self.m_carDamageRate),
            "collisions" : str(self.m_collisions),
            "collisions-off-for-first-lap-only": self.m_collisionsOffForFirstLapOnly,
            "mp-unsafe-pit-release" : self.m_mpUnsafePitRelease,
            "mp-off-for-griefing" : self.m_mpOffForGriefing,
            "corner-cutting-stringency" : str(self.m_cornerCuttingStringency),
            "parc-ferme-rules" : self.m_parcFermeRules,
            "pit-stop-experience" : str(self.m_pitStopExperience),
            "safety-car-setting" : str(self.m_safetyCar),
            "safety-car-experience" : str(self.m_safetyCarExperience),
            "formation-lap" : self.m_formationLap,
            "formation-lap-experience" : str(self.m_formationLapExperience),
            "red-flags-setting" : str(self.m_redFlags),
            "affects-license-level-solo" : self.m_affectsLicenceLevelSolo,
            "affects-license-level-mp" : self.m_affectsLicenceLevelMP,
            "num-sessions-in-weekend" : str(self.m_numSessionsInWeekend),
            "weekend-structure" : [str(weekend) for weekend in self.m_weekendStructure],
            "sector-2-lap-distance-start" : str(self.m_sector2LapDistanceStart),
            "sector-3-lap-distance-start" : str(self.m_sector3LapDistanceStart),
        }

    def _f26_json(self) -> Dict[str, Any]:
        """Return JSON dict for F1 2026-only fields."""
        return {
            "active-aero-track-status": str(self.m_activeAeroTrackStatus),
            "num-active-aero-zones-full": self.m_numActiveAeroZonesFull,
            "active-aero-zones-full": [z.toJSON() for z in self.m_activeAeroZonesFull],
            "num-active-aero-zones-partial": self.m_numActiveAeroZonesPartial,
            "active-aero-zones-partial": [z.toJSON() for z in self.m_activeAeroZonesPartial],
            "num-drs-zones": self.m_numDRSZones,
            "drs-zones": [z.toJSON() for z in self.m_drsZones],
            "start-reaction-time": self.m_startReactionTime,
            "anti-lock-brakes-assist": self.m_antiLockBrakesAssist,
            "traction-control-assist": str(self.m_tractionControlAssist),
            "dynamic-racing-line-hi-vis": self.m_dynamicRacingLineHiVis,
            "dynamic-racing-line-colour-blind": str(self.m_dynamicRacingLineColourBlind),
            "recurring-rewind-prompt": self.m_recurringRewindPrompt,
        }

    def __eq__(self, other: "PacketSessionData") -> bool:
        """
        Check for equality between two PacketSessionData objects.

        Args:
            other (object): The other object to compare against.

        Returns:
            bool: True if both PacketSessionData objects are equal, False otherwise.
        """
        if not isinstance(other, PacketSessionData):
            return NotImplemented

        if self.m_header != other.m_header:
            return False

        if not self._eq_base(other):
            return False

        if self.m_header.m_packetFormat >= 2024:
            if not self._eq_f24(other):
                return False

        if self.m_header.m_packetFormat >= 2026:
            return self._eq_f26(other)

        return True

    def _eq_base(self, other: "PacketSessionData") -> bool:
        """
        Check the fields present in all packet formats.

        Args:
            other (object): The other object to compare against.

        Returns:
            bool: True if both PacketSessionData objects are equal, False otherwise.
        """
        return (
            self.m_weather == other.m_weather and
            self.m_trackTemperature == other.m_trackTemperature and
            self.m_airTemperature == other.m_airTemperature and
            self.m_totalLaps == other.m_totalLaps and
            self.m_trackLength == other.m_trackLength and
            self.m_sessionType == other.m_sessionType and
            self.m_trackId == other.m_trackId and
            self.m_formula == other.m_formula and
            self.m_sessionTimeLeft == other.m_sessionTimeLeft and
            self.m_sessionDuration  == other.m_sessionDuration and
            self.m_pitSpeedLimit == other.m_pitSpeedLimit and
            self.m_gamePaused == other.m_gamePaused and
            self.m_isSpectating == other.m_isSpectating and
            self.m_spectatorCarIndex == other.m_spectatorCarIndex and
            self.m_sliProNativeSupport == other.m_sliProNativeSupport and
            self.m_numMarshalZones == other.m_numMarshalZones and
            self.m_marshalZones == other.m_marshalZones and
            self.m_safetyCarStatus == other.m_safetyCarStatus and
            self.m_networkGame == other.m_networkGame and
            self.m_numWeatherForecastSamples == other.m_numWeatherForecastSamples and
            self.m_weatherForecastSamples == other.m_weatherForecastSamples and
            self.m_forecastAccuracy == other.m_forecastAccuracy and
            self.m_aiDifficulty == other.m_aiDifficulty and
            self.m_seasonLinkIdentifier == other.m_seasonLinkIdentifier and
            self.m_weekendLinkIdentifier == other.m_weekendLinkIdentifier and
            self.m_sessionLinkIdentifier == other.m_sessionLinkIdentifier and
            self.m_pitStopWindowIdealLap == other.m_pitStopWindowIdealLap and
            self.m_pitStopWindowLatestLap == other.m_pitStopWindowLatestLap and
            self.m_pitStopRejoinPosition == other.m_pitStopRejoinPosition and
            self.m_steeringAssist == other.m_steeringAssist and
            self.m_brakingAssist == other.m_brakingAssist and
            self.m_gearboxAssist == other.m_gearboxAssist and
            self.m_pitAssist == other.m_pitAssist and
            self.m_pitReleaseAssist == other.m_pitReleaseAssist and
            self.m_ERSAssist == other.m_ERSAssist and
            self.m_DRSAssist == other.m_DRSAssist and
            self.m_dynamicRacingLine == other.m_dynamicRacingLine and
            self.m_dynamicRacingLineType == other.m_dynamicRacingLineType and
            self.m_gameMode == other.m_gameMode and
            self.m_ruleSet == other.m_ruleSet and
            self.m_timeOfDay == other.m_timeOfDay and
            self.m_sessionLength == other.m_sessionLength and
            self.m_speedUnitsLeadPlayer == other.m_speedUnitsLeadPlayer and
            self.m_temperatureUnitsLeadPlayer == other.m_temperatureUnitsLeadPlayer and
            self.m_speedUnitsSecondaryPlayer == other.m_speedUnitsSecondaryPlayer and
            self.m_temperatureUnitsSecondaryPlayer == other.m_temperatureUnitsSecondaryPlayer and
            self.m_numSafetyCarPeriods == other.m_numSafetyCarPeriods and
            self.m_numVirtualSafetyCarPeriods == other.m_numVirtualSafetyCarPeriods and
            self.m_numRedFlagPeriods == other.m_numRedFlagPeriods
        )

    def _eq_f24(self, other: "PacketSessionData") -> bool:
        """
        Check the F1 24+ specific fields.

        Args:
            other (object): The other object to compare against.

        Returns:
            bool: True if both PacketSessionData objects are equal, False otherwise.
        """
        return (
                self.m_equalCarPerformance == other.m_equalCarPerformance and
                self.m_recoveryMode == other.m_recoveryMode and
                self.m_flashbackLimit == other.m_flashbackLimit and
                self.m_surfaceType == other.m_surfaceType and
                self.m_lowFuelMode == other.m_lowFuelMode and
                self.m_raceStarts == other.m_raceStarts and
                self.m_tyreTemperatureMode == other.m_tyreTemperatureMode and
                self.m_pitLaneTyreSim == other.m_pitLaneTyreSim and
                self.m_carDamage == other.m_carDamage and
                self.m_carDamageRate == other.m_carDamageRate and
                self.m_collisions == other.m_collisions and
                self.m_collisionsOffForFirstLapOnly == other.m_collisionsOffForFirstLapOnly and
                self.m_mpUnsafePitRelease == other.m_mpUnsafePitRelease and
                self.m_mpOffForGriefing == other.m_mpOffForGriefing and
                self.m_cornerCuttingStringency == other.m_cornerCuttingStringency and
                self.m_parcFermeRules == other.m_parcFermeRules and
                self.m_pitStopExperience == other.m_pitStopExperience and
                self.m_safetyCar == other.m_safetyCar and
                self.m_safetyCarExperience == other.m_safetyCarExperience and
                self.m_formationLap == other.m_formationLap and
                self.m_formationLapExperience == other.m_formationLapExperience and
                self.m_redFlags == other.m_redFlags and
                self.m_affectsLicenceLevelSolo == other.m_affectsLicenceLevelSolo and
                self.m_affectsLicenceLevelMP == other.m_affectsLicenceLevelMP and
                self.m_numSessionsInWeekend == other.m_numSessionsInWeekend and
                self.m_weekendStructure == other.m_weekendStructure and
                self.m_sector2LapDistanceStart == other.m_sector2LapDistanceStart and
                self.m_sector3LapDistanceStart == other.m_sector3LapDistanceStart
            )

    def _eq_f26(self, other: "PacketSessionData") -> bool:
        """Check F1 2026-only fields for equality."""
        return (
            self.m_activeAeroTrackStatus == other.m_activeAeroTrackStatus and
            self.m_numActiveAeroZonesFull == other.m_numActiveAeroZonesFull and
            self.m_activeAeroZonesFull == other.m_activeAeroZonesFull and
            self.m_numActiveAeroZonesPartial == other.m_numActiveAeroZonesPartial and
            self.m_activeAeroZonesPartial == other.m_activeAeroZonesPartial and
            self.m_numDRSZones == other.m_numDRSZones and
            self.m_drsZones == other.m_drsZones and
            self.m_startReactionTime == other.m_startReactionTime and
            self.m_antiLockBrakesAssist == other.m_antiLockBrakesAssist and
            self.m_tractionControlAssist == other.m_tractionControlAssist and
            self.m_dynamicRacingLineHiVis == other.m_dynamicRacingLineHiVis and
            self.m_dynamicRacingLineColourBlind == other.m_dynamicRacingLineColourBlind and
            self.m_recurringRewindPrompt == other.m_recurringRewindPrompt
        )
