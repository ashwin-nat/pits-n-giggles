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
from enum import Enum
from typing import Any, Dict, List

from .common import (GameMode, GearboxAssistMode, PacketHeader, RuleSet,
                     SafetyCarType, SessionLength, SessionType, SessionType23,
                     SessionType24, TrackID)

# --------------------- CLASS DEFINITIONS --------------------------------------

class MarshalZone:
    """
    A class for parsing the Marshal Zone data within a telemetry packet in a racing game.

    The Marshal Zone structure is as follows:

    Attributes:
        - m_zone_start (float): Fraction (0..1) of the way through the lap the marshal zone starts.
        - m_zone_flag (MarshalZone.MarshalZoneFlagType): Refer to the enum type for various options
    """

    PACKET_FORMAT = ("<"
        "f" # float - Fraction (0..1) of way through the lap the marshal zone starts
        "b" # int8  - -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    class MarshalZoneFlagType(Enum):
        """
        ENUM class for the marshal zone flag status
        """

        INVALID_UNKNOWN = -1
        NONE = 0
        GREEN_FLAG = 1
        BLUE_FLAG = 2
        YELLOW_FLAG = 3

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given packet type is valid.

            Args:
                flag_type (int): The flag code to be validated. Also supports type MarshalZoneFlagType.
                    Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, MarshalZone.MarshalZoneFlagType):
                return True  # It's already an instance of MarshalZone.MarshalZoneFlagType
            return any(flag_type == member.value for member in MarshalZone.MarshalZoneFlagType)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

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
        ) = struct.unpack(self.PACKET_FORMAT, data)

        if MarshalZone.MarshalZoneFlagType.isValid(self.m_zoneFlag):
            self.m_zoneFlag = MarshalZone.MarshalZoneFlagType(self.m_zoneFlag)

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

        return struct.pack(self.PACKET_FORMAT, self.m_zoneStart, self.m_zoneFlag)

    @classmethod
    def from_values(cls, zone_start: float, zone_flag: MarshalZoneFlagType) -> "MarshalZone":
        """Creates a new MarshalZone object from the given values.

        Args:
            zone_start (float): Fraction (0..1) of the way through the lap the marshal zone starts.
            zone_flag (MarshalZone.MarshalZoneFlagType): Refer to the enum type for various options

        Returns:
            MarshalZone: A new MarshalZone object
        """

        return cls(struct.pack(cls.PACKET_FORMAT, zone_start, zone_flag))

class WeatherForecastSample:
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

    PACKET_FORMAT = ("<"
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
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    class WeatherCondition(Enum):
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

        def __str__(self):
            """
            Returns a human-readable string representation of the weather condition.

            Returns:
                str: String representation of the weather condition.
            """
            return {
                WeatherForecastSample.WeatherCondition.CLEAR: "Clear",
                WeatherForecastSample.WeatherCondition.LIGHT_CLOUD: "Light Cloud",
                WeatherForecastSample.WeatherCondition.OVERCAST: "Overcast",
                WeatherForecastSample.WeatherCondition.LIGHT_RAIN: "Light Rain",
                WeatherForecastSample.WeatherCondition.HEAVY_RAIN: "Heavy Rain",
                WeatherForecastSample.WeatherCondition.STORM: "Storm",
                WeatherForecastSample.WeatherCondition.THUNDERSTORM: "Thunderstorm",
            }[self]

        @staticmethod
        def isValid(weather_type_code: int):
            """Check if the given weather type code is valid.

            Args:
                weather_type_code (int): The weather type code to be validated.
                    Also supports type WeatherCondition. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(weather_type_code, WeatherForecastSample.WeatherCondition):
                return True  # It's already an instance of WeatherForecastSample.WeatherCondition
            return any(weather_type_code == member.value for member in  WeatherForecastSample.WeatherCondition)

    class TrackTemperatureChange(Enum):
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

        @staticmethod
        def isValid(temp_change_code: int):
            """Check if the given temperature change code is valid.

            Args:
                temp_change_code (int): The temperature change code to be validated.
                    Also supports type TrackTemperatureChange. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(temp_change_code, WeatherForecastSample.TrackTemperatureChange):
                return True  # It's already an instance of WeatherForecastSample.TrackTemperatureChange
            min_value = min(member.value for member in WeatherForecastSample.TrackTemperatureChange)
            max_value = max(member.value for member in WeatherForecastSample.TrackTemperatureChange)
            return min_value <= temp_change_code <= max_value

    class AirTemperatureChange(Enum):
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

        @staticmethod
        def isValid(air_temp_change_code: int):
            """Check if the given air temperature change code is valid.

            Args:
                air_temp_change_code (int): The air temperature change to be validated.
                    Also supports type AirTemperatureChange. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(air_temp_change_code, WeatherForecastSample.AirTemperatureChange):
                return True  # It's already an instance of WeatherForecastSample.AirTemperatureChange
            min_value = min(member.value for member in WeatherForecastSample.AirTemperatureChange)
            max_value = max(member.value for member in WeatherForecastSample.AirTemperatureChange)
            return min_value <= air_temp_change_code <= max_value

        def __str__(self):
            return {
                WeatherForecastSample.AirTemperatureChange.UP: "Temperature Up",
                WeatherForecastSample.AirTemperatureChange.DOWN: "Temperature Down",
                WeatherForecastSample.AirTemperatureChange.NO_CHANGE: "No Temperature Change",
            }[self]

    def __init__(self, data: bytes, game_year: int) -> None:
        """Unpack the given raw bytes into this object

        Args:
            data (bytes): List of raw bytes received as part of this
            game_year (int): The year of the game
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
        ) = struct.unpack(self.PACKET_FORMAT, data)

        # Convert to typed enums wherever applicable
        if WeatherForecastSample.WeatherCondition.isValid(self.m_weather):
            self.m_weather = WeatherForecastSample.WeatherCondition(self.m_weather)
        if WeatherForecastSample.AirTemperatureChange.isValid(self.m_airTemperatureChange):
            self.m_airTemperatureChange = WeatherForecastSample.AirTemperatureChange(self.m_airTemperatureChange)
        if WeatherForecastSample.TrackTemperatureChange.isValid(self.m_trackTemperatureChange):
            self.m_trackTemperatureChange = WeatherForecastSample.TrackTemperatureChange(self.m_trackTemperatureChange)
        if game_year == 23 and SessionType23.isValid(self.m_sessionType):
            self.m_sessionType = SessionType23(self.m_sessionType)
        elif game_year == 24 and SessionType24.isValid(self.m_sessionType):
            self.m_sessionType = SessionType24(self.m_sessionType)

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

        return struct.pack(self.PACKET_FORMAT,
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
                    session_type: SessionType,
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
            session_type (SessionType): Session type enum
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
            struct.pack(WeatherForecastSample.PACKET_FORMAT,
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

class PacketSessionData:
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

    PACKET_FORMAT_SECTION_0 = ("<"
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
    PACKET_LEN_SECTION_0 = struct.calcsize(PACKET_FORMAT_SECTION_0)

    PACKET_FORMAT_SECTION_2 = ("<"
        "B" # uint8           m_safetyCarStatus; // 0 = no safety car, 1 = full // 2 = virtual, 3 = formation lap
        "B" # uint8           m_networkGame;               // 0 = offline, 1 = online
        "B" # uint8           m_numWeatherForecastSamples; // Number of weather samples to follow
    )
    PACKET_LEN_SECTION_2 = struct.calcsize(PACKET_FORMAT_SECTION_2)

    PACKET_FORMAT_SECTION_4 = ("<"
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
    PACKET_LEN_SECTION_4 = struct.calcsize(PACKET_FORMAT_SECTION_4)

    # This is only for F1 24
    PACKET_FORMAT_SECTION_5 = ("<"
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
    PACKET_LEN_SECTION_5 = struct.calcsize(PACKET_FORMAT_SECTION_5)

    class FormulaType(Enum):
        """An enumeration of formula types."""

        F1_MODERN: int = 0
        F1_CLASSIC: int = 1
        F2: int = 2
        F1_GENERIC: int = 3
        BETA: int = 4
        SUPERCARS: int = 5
        ESPORTS: int = 6
        F2_2021: int = 7

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
                PacketSessionData.FormulaType.F2_2021: "F2 2021"
            }[self]

        @staticmethod
        def isValid(formula_type_code: int):
            """Check if the given formula type is valid.

            Args:
                formula_type_code (int): The safety car status to be validated.
                    Also supports type FormulaType. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(formula_type_code, PacketSessionData.FormulaType):
                return True  # It's already an instance of FormulaType
            return any(formula_type_code == member.value for member in \
                PacketSessionData.FormulaType)

    class RecoveryMode(Enum):
        """
        ENUM class for the recovery type modes
        """
        NONE = 0
        FLASHBACKS = 1
        AUTO_RECOVERY = 2

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given recovery mode is valid.

            Args:
                flag_type (int): The flag code to be validated. Also supports type RecoveryMode.
                    Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.RecoveryMode):
                return True  # It's already an instance of PacketSessionData.RecoveryMode
            return any(flag_type == member.value for member in PacketSessionData.RecoveryMode)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class FlashbackLimit(Enum):
        """
        ENUM class for the flashback limit types
        """
        LOW = 0
        MEDIUM = 1
        HIGH = 2
        UNLIMITED = 3

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given flashback limit type is valid.

            Args:
                flag_type (int): The flag code to be validated. Also supports type FlashbackLimit.
                    Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.FlashbackLimit):
                return True  # It's already an instance of PacketSessionData.FlashbackLimit
            return any(flag_type == member.value for member in PacketSessionData.FlashbackLimit)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class SurfaceType(Enum):
        """
        ENUM class for the surface types
        """
        SIMPLIFIED = 0
        REALISTIC = 1

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given surface type is valid.

            Args:
                flag_type (int): The flag code to be validated. Also supports type SurfaceType.
                    Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.SurfaceType):
                return True  # It's already an instance of PacketSessionData.SurfaceType
            return any(flag_type == member.value for member in PacketSessionData.SurfaceType)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class LowFuelMode(Enum):
        """
        ENUM class for the low fuel mode types
        """
        EASY = 0
        HARD = 1

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given low fuel mode is valid.

            Args:
                flag_type (int): The low fuel mode to be validated. Also supports type LowFuelMode.
                    Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.LowFuelMode):
                return True  # It's already an instance of PacketSessionData.LowFuelMode
            return any(flag_type == member.value for member in PacketSessionData.LowFuelMode)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class RaceStartsMode(Enum):
        """
        ENUM class for the race starts mode types
        """
        MANUAL = 0
        ASSISTED = 1

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given race starts mode is valid.

            Args:
                flag_type (int): The race starts mode to be validated. Also supports type
                    RaceStartsMode. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.RaceStartsMode):
                return True  # It's already an instance of PacketSessionData.RaceStartsMode
            return any(flag_type == member.value for member in PacketSessionData.RaceStartsMode)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class TyreTemperatureMode(Enum):
        """
        ENUM class for the tyre temperature mode types
        """
        SURFACE_ONLY = 0
        SURFACE_AND_CARCASS = 1

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given tyre temperature mode is valid.

            Args:
                flag_type (int): The tyre temperature mode to be validated. Also supports type
                    TyreTemperatureMode. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.TyreTemperatureMode):
                return True  # It's already an instance of PacketSessionData.TyreTemperatureMode
            return any(flag_type == member.value for member in PacketSessionData.TyreTemperatureMode)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class CarDamageMode(Enum):
        """
        ENUM class for the car damage mode types
        """
        OFF = 0
        REDUCED = 1
        STANDARD = 2
        SIMULATION = 3

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given car damage mode is valid.

            Args:
                flag_type (int): The car damage mode to be validated. Also supports type
                    CarDamageMode. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.CarDamageMode):
                return True  # It's already an instance of PacketSessionData.CarDamageMode
            return any(flag_type == member.value for member in PacketSessionData.CarDamageMode)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class CarDamageRate(Enum):
        """
        ENUM class for the car damage rate types
        """
        REDUCED = 0
        STANDARD = 1
        SIMULATION = 2

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given car damage rate is valid.

            Args:
                flag_type (int): The car damage rate to be validated. Also supports type
                    CarDamageRate. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.CarDamageRate):
                return True  # It's already an instance of PacketSessionData.CarDamageRate
            return any(flag_type == member.value for member in PacketSessionData.CarDamageRate)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class CollisionsMode(Enum):
        """
        ENUM class for the collisions mode types
        """
        OFF = 0
        PLAYER_TO_PLAYER_OFF = 1
        ON = 2

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given collisions mode is valid.

            Args:
                flag_type (int): The collisions mode to be validated. Also supports type
                    CollisionsMode. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.CollisionsMode):
                return True  # It's already an instance of PacketSessionData.CollisionsMode
            return any(flag_type == member.value for member in PacketSessionData.CollisionsMode)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class CornerCuttingStringency(Enum):
        """
        ENUM class for the corner cutting stringency types
        """
        REGULAR = 0
        STRICT = 1

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given corner cutting stringency is valid.

            Args:
                flag_type (int): The corner cutting stringency to be validated. Also supports type
                    CornerCuttingStringency. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.CornerCuttingStringency):
                return True  # It's already an instance of PacketSessionData.CornerCuttingStringency
            return any(flag_type == member.value for member in
                       PacketSessionData.CornerCuttingStringency)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class PitStopExperience(Enum):
        """
        ENUM class for the pit stop experience types
        """
        AUTOMATIC = 0
        BROADCAST = 1
        IMMERSIVE = 2

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given pit stop experience is valid.

            Args:
                flag_type (int): The pit stop experience to be validated. Also supports type
                    PitStopExperience. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.PitStopExperience):
                return True  # It's already an instance of PacketSessionData.PitStopExperience
            return any(flag_type == member.value for member in
                       PacketSessionData.PitStopExperience)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class SafetyCarSetting(Enum):
        """
        ENUM class for the safety car setting types
        """
        OFF = 0
        REDUCED = 1
        STANDARD = 2
        INCREASED = 3

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given safety car setting is valid.

            Args:
                flag_type (int): The safety car setting to be validated. Also supports type
                    SafetyCarSetting. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.SafetyCarSetting):
                return True  # It's already an instance of PacketSessionData.SafetyCarSetting
            return any(flag_type == member.value for member in
                       PacketSessionData.SafetyCarSetting)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class SafetyCarExperience(Enum):
        """
        ENUM class for the safety car experience types
        """
        BROADCAST = 0
        IMMERSIVE = 1

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given safety car experience is valid.

            Args:
                flag_type (int): The safety car experience to be validated. Also supports type
                    SafetyCarExperience. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.SafetyCarExperience):
                return True  # It's already an instance of PacketSessionData.SafetyCarExperience
            return any(flag_type == member.value for member in
                       PacketSessionData.SafetyCarExperience)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class FormationLapExperience(Enum):
        """
        ENUM class for the formation lap experience types
        """
        BROADCAST = 0
        IMMERSIVE = 1

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given formation lap experience is valid.

            Args:
                flag_type (int): The formation lap experience to be validated. Also supports type
                    FormationLapExperience. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.FormationLapExperience):
                return True  # It's already an instance of PacketSessionData.FormationLapExperience
            return any(flag_type == member.value for member in
                       PacketSessionData.FormationLapExperience)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    class RedFlagsSetting(Enum):
        """
        ENUM class for the red flags setting types
        """
        OFF = 0
        REDUCED = 1
        STANDARD = 2
        INCREASED = 3

        @staticmethod
        def isValid(flag_type: int):
            """Check if the given red flags setting is valid.

            Args:
                flag_type (int): The red flags setting to be validated. Also supports type
                    RedFlagsSetting. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(flag_type, PacketSessionData.RedFlagsSetting):
                return True  # It's already an instance of PacketSessionData.RedFlagsSetting
            return any(flag_type == member.value for member in
                       PacketSessionData.RedFlagsSetting)

        def __str__(self):
            """Return the string representation of this object

            Returns:
                str: string representation
            """

            return self.name

    def __init__(self, header: PacketHeader, data: bytes) -> None:
        # sourcery skip: low-code-quality
        """Construct a PacketSessionData object

        Args:
            header (PacketHeader): The parsed header object
            data (bytes): The list of raw bytes representing this packet
        """
        self.m_header: PacketHeader = header          # Header

        # Declare the type hints
        self.m_weather: WeatherForecastSample.WeatherCondition
        self.m_trackTemperature: int
        self.m_airTemperature: int
        self.m_totalLaps: int
        self.m_trackLength: int
        self.m_sessionType: SessionType
        self.m_trackId: TrackID
        self.m_formula: int
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

        self.m_maxMarshalZones = self.F1_23_MAX_NUM_MARSHAL_ZONES
        if header.m_gameYear == 23:
            self.m_maxWeatherForecastSamples = self.F1_23_MAX_NUM_WEATHER_FORECAST_SAMPLES
        else:
            self.m_maxWeatherForecastSamples = self.F1_24_MAX_NUM_WEATHER_FORECAST_SAMPLES
        # First, section 0
        section_0_raw_data = data[0:self.PACKET_LEN_SECTION_0]
        byte_index_so_far = self.PACKET_LEN_SECTION_0
        unpacked_data = struct.unpack(self.PACKET_FORMAT_SECTION_0, section_0_raw_data)
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
        ) = unpacked_data
        if WeatherForecastSample.WeatherCondition.isValid(self.m_weather):
            self.m_weather = WeatherForecastSample.WeatherCondition(self.m_weather)
        if TrackID.isValid(self.m_trackId):
            self.m_trackId = TrackID(self.m_trackId)

        if header.m_gameYear == 23 and SessionType23.isValid(self.m_sessionType):
            self.m_sessionType = SessionType23(self.m_sessionType)
        elif header.m_gameYear == 24 and SessionType24.isValid(self.m_sessionType):
            self.m_sessionType = SessionType24(self.m_sessionType)

        if PacketSessionData.FormulaType.isValid(self.m_formula):
            self.m_formula = PacketSessionData.FormulaType(self.m_formula)

        # Next section 1, marshalZones
        section_1_size = MarshalZone.PACKET_LEN * self.m_maxMarshalZones
        section_1_raw_data = data[byte_index_so_far:byte_index_so_far + section_1_size]
        byte_index_so_far += section_1_size

        # Iterate over section_1_raw_data in steps of MarshalZone.PACKET_LEN,
        # creating MarshalZone objects for each segment.
        self.m_marshalZones = [
            MarshalZone(section_1_raw_data[i:i + MarshalZone.PACKET_LEN])
            for i in range(0, len(section_1_raw_data), MarshalZone.PACKET_LEN)
        ]
        # Trim the unnecessary marshalZones
        self.m_marshalZones = self.m_marshalZones[:self.m_numMarshalZones]
        section_1_raw_data = None

        # Section 2, till numWeatherForecastSamples
        section_2_raw_data = data[byte_index_so_far:byte_index_so_far + self.PACKET_LEN_SECTION_2]
        byte_index_so_far += self.PACKET_LEN_SECTION_2
        unpacked_data = struct.unpack(self.PACKET_FORMAT_SECTION_2, section_2_raw_data)
        (
            self.m_safetyCarStatus, #           // 0 = no safety car, 1 = full 2 = virtual, 3 = formation lap
            self.m_networkGame, #               // 0 = offline, 1 = online
            self.m_numWeatherForecastSamples # // Number of weather samples to follow
        ) = unpacked_data
        if SafetyCarType.isValid(self.m_safetyCarStatus):
            self.m_safetyCarStatus = SafetyCarType(self.m_safetyCarStatus)
        section_2_raw_data = None

        # Section 3 - weather forecast samples
        section_3_size = WeatherForecastSample.PACKET_LEN * self.m_maxWeatherForecastSamples
        section_3_raw_data = data[byte_index_so_far:byte_index_so_far + section_3_size]
        byte_index_so_far += section_3_size
        # Iterate over section_3_raw_data in steps of WeatherForecastSample.PACKET_LEN,
        # creating WeatherForecastSample objects for each segment and passing the game year.

        self.m_weatherForecastSamples = [
            WeatherForecastSample(section_3_raw_data[i:i + WeatherForecastSample.PACKET_LEN], header.m_gameYear)
            for i in range(0, len(section_3_raw_data), WeatherForecastSample.PACKET_LEN)
        ]
        # Trim the unnecessary weatherForecastSamples
        self.m_weatherForecastSamples = self.m_weatherForecastSamples[:self.m_numWeatherForecastSamples]
        section_3_raw_data = None

        # Section 4 - rest of the packet
        section_4_raw_data = data[byte_index_so_far:byte_index_so_far + self.PACKET_LEN_SECTION_4]
        byte_index_so_far += self.PACKET_LEN_SECTION_4
        unpacked_data = struct.unpack(self.PACKET_FORMAT_SECTION_4, section_4_raw_data)
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
        ) = unpacked_data
        section_4_raw_data = None
        if GearboxAssistMode.isValid(self.m_gearboxAssist):
            self.m_gearboxAssist = GearboxAssistMode(self.m_gearboxAssist)
        if SessionLength.isValid(self.m_sessionLength):
            self.m_sessionLength = SessionLength(self.m_sessionLength)
        if GameMode.isValid(self.m_gameMode):
            self.m_gameMode = GameMode(self.m_gameMode)
        if RuleSet.isValid(self.m_ruleSet):
            self.m_ruleSet = RuleSet(self.m_ruleSet)

        # Section 5 - F1 24 specific stuff
        if header.m_gameYear == 24:
            self.m_weekendStructure = [0] * 12
            section_5_raw_data = data[byte_index_so_far:byte_index_so_far + self.PACKET_LEN_SECTION_5]
            unpacked_data = struct.unpack(self.PACKET_FORMAT_SECTION_5, section_5_raw_data)
            (
                self.m_equalCarPerformance,
                self.m_recoveryMode,
                self.m_flashbackLimit,
                self.m_surfaceType,
                self.m_lowFuelMode,
                self.m_raceStarts,
                self.m_tyreTemperatureMode,
                self.m_pitLaneTyreSim,
                self.m_carDamage,
                self.m_carDamageRate,
                self.m_collisions,
                self.m_collisionsOffForFirstLapOnly,
                self.m_mpUnsafePitRelease,
                self.m_mpOffForGriefing,
                self.m_cornerCuttingStringency,
                self.m_parcFermeRules,
                self.m_pitStopExperience,
                self.m_safetyCar,
                self.m_safetyCarExperience,
                self.m_formationLap,
                self.m_formationLapExperience,
                self.m_redFlags,
                self.m_affectsLicenceLevelSolo,
                self.m_affectsLicenceLevelMP,
                self.m_numSessionsInWeekend,
                self.m_weekendStructure[0],
                self.m_weekendStructure[1],
                self.m_weekendStructure[2],
                self.m_weekendStructure[3],
                self.m_weekendStructure[4],
                self.m_weekendStructure[5],
                self.m_weekendStructure[6],
                self.m_weekendStructure[7],
                self.m_weekendStructure[8],
                self.m_weekendStructure[9],
                self.m_weekendStructure[10],
                self.m_weekendStructure[11],
                self.m_sector2LapDistanceStart,
                self.m_sector3LapDistanceStart,
            ) = unpacked_data

            self.m_weekendStructure = self.m_weekendStructure[:self.m_numSessionsInWeekend]
            for session_id in self.m_weekendStructure:
                session_id = SessionType24(session_id)
        else:
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

        # Convert into enum types if supported
        if PacketSessionData.RecoveryMode.isValid(self.m_recoveryMode):
            self.m_recoveryMode = PacketSessionData.RecoveryMode(self.m_recoveryMode)
        if PacketSessionData.FlashbackLimit.isValid(self.m_flashbackLimit):
            self.m_flashbackLimit = PacketSessionData.FlashbackLimit(self.m_flashbackLimit)
        if PacketSessionData.SurfaceType.isValid(self.m_surfaceType):
            self.m_surfaceType = PacketSessionData.SurfaceType(self.m_surfaceType)
        if PacketSessionData.LowFuelMode.isValid(self.m_lowFuelMode):
            self.m_lowFuelMode = PacketSessionData.LowFuelMode(self.m_lowFuelMode)
        if PacketSessionData.RaceStartsMode.isValid(self.m_raceStarts):
            self.m_raceStarts = PacketSessionData.RaceStartsMode(self.m_raceStarts)
        if PacketSessionData.TyreTemperatureMode(self.m_tyreTemperatureMode):
            self.m_tyreTemperatureMode = PacketSessionData.TyreTemperatureMode(
                self.m_tyreTemperatureMode)
        if PacketSessionData.CarDamageMode.isValid(self.m_carDamage):
            self.m_carDamage = PacketSessionData.CarDamageMode(self.m_carDamage)
        if PacketSessionData.CarDamageRate.isValid(self.m_carDamageRate):
            self.m_carDamageRate = PacketSessionData.CarDamageRate(self.m_carDamageRate)
        if PacketSessionData.CollisionsMode.isValid(self.m_collisions):
            self.m_collisions = PacketSessionData.CollisionsMode(self.m_collisions)
        if PacketSessionData.CornerCuttingStringency.isValid(self.m_cornerCuttingStringency):
            self.m_cornerCuttingStringency = PacketSessionData.CornerCuttingStringency(
                self.m_cornerCuttingStringency)
        if PacketSessionData.PitStopExperience.isValid(self.m_pitStopExperience):
            self.m_pitStopExperience = PacketSessionData.PitStopExperience(self.m_pitStopExperience)
        if PacketSessionData.SafetyCarSetting.isValid(self.m_safetyCar):
            self.m_safetyCar = PacketSessionData.SafetyCarSetting(self.m_safetyCar)
        if PacketSessionData.SafetyCarExperience.isValid(self.m_safetyCarExperience):
            self.m_safetyCarExperience = PacketSessionData.SafetyCarExperience(
                self.m_safetyCarExperience)
        if PacketSessionData.FormationLapExperience.isValid(self.m_formationLapExperience):
            self.m_formationLapExperience = PacketSessionData.FormationLapExperience(
                self.m_formationLapExperience)
        if PacketSessionData.RedFlagsSetting.isValid(self.m_redFlags):
            self.m_redFlags = PacketSessionData.RedFlagsSetting(self.m_redFlags)

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
            f"Num Red Flag Periods: {self.m_numRedFlagPeriods})"
        )

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """Converts the PacketSessionData object to a dictionary suitable for JSON serialization.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """

        json_data = {
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

            "equal-car-performance" : str(self.m_equalCarPerformance),
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
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

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

        if not self.__eq_f1_23(other):
            return False

        if self.m_header.m_gameYear == 24:
            return self.__eq_f1_24(other)

        return True

    def __eq_f1_23(self, other: "PacketSessionData") -> bool:
        """
        Check the F1 23 specific stuff

        Args:
            other (object): The other object to compare against.

        Returns:
            bool: True if both PacketSessionData objects are equal, False otherwise.
        """
        if not isinstance(other, PacketSessionData):
            return NotImplemented

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

    def __eq_f1_24(self, other: "PacketSessionData") -> bool:
        """
        Check the F1 24 specific stuff

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
