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

## NOTE: Please refer to the F1 23 UDP specification document to understand fully how the telemetry data works.
## All classes in supported in this library are documented with the members, but it is still recommended to read the
## official document. https://answers.ea.com/t5/General-Discussion/F1-23-UDP-Specification/m-p/12633159

from .common import *
from .common import _split_list, _extract_sublist

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
            else:
                min_value = min(member.value for member in MarshalZone.MarshalZoneFlagType)
                max_value = max(member.value for member in MarshalZone.MarshalZoneFlagType)
                return min_value <= flag_type <= max_value

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
        return f"MarshalZone(Start: {self.m_zoneStart}, Flag: {self.m_zoneFlag})"

    def toJSON(self) -> Dict[str, Any]:
        """Converts the MarshalZone object to a dictionary suitable for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """

        return {
            "zone-start": self.m_zoneStart,
            "zone-flag": str(self.m_zoneFlag)
        }

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

            Note:
                Each attribute represents a unique weather condition identified by an integer value.
        """
        CLEAR = 0
        LIGHT_CLOUD = 1
        OVERCAST = 2
        LIGHT_RAIN = 3
        HEAVY_RAIN = 4
        STORM = 5

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
            }[self]

        @staticmethod
        def isValid(weather_type_code: int):
            """Check if the given weather type code is valid.

            Args:
                flag_type (int): The weather type code to be validated.
                    Also supports type WeatherCondition. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(weather_type_code, WeatherForecastSample.WeatherCondition):
                return True  # It's already an instance of WeatherForecastSample.WeatherCondition
            else:
                min_value = min(member.value for member in WeatherForecastSample.WeatherCondition)
                max_value = max(member.value for member in WeatherForecastSample.WeatherCondition)
                return min_value <= weather_type_code <= max_value

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
                flag_type (int): The temperature change code to be validated.
                    Also supports type TrackTemperatureChange. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(temp_change_code, WeatherForecastSample.TrackTemperatureChange):
                return True  # It's already an instance of WeatherForecastSample.TrackTemperatureChange
            else:
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
                flag_type (int): The air temperature change to be validated.
                    Also supports type AirTemperatureChange. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(air_temp_change_code, WeatherForecastSample.AirTemperatureChange):
                return True  # It's already an instance of WeatherForecastSample.AirTemperatureChange
            else:
                min_value = min(member.value for member in WeatherForecastSample.AirTemperatureChange)
                max_value = max(member.value for member in WeatherForecastSample.AirTemperatureChange)
                return min_value <= air_temp_change_code <= max_value

        def __str__(self):
            return {
                WeatherForecastSample.AirTemperatureChange.UP: "Temperature Up",
                WeatherForecastSample.AirTemperatureChange.DOWN: "Temperature Down",
                WeatherForecastSample.AirTemperatureChange.NO_CHANGE: "No Temperature Change",
            }[self]

    def __init__(self, data: bytes) -> None:
        """Unpack the given raw bytes into this object

        Args:
            data (bytes): List of raw bytes received as part of this
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
        if SessionType.isValid(self.m_sessionType):
            self.m_sessionType = SessionType(self.m_sessionType)

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

class PacketSessionData:
    """
    Represents an incoming packet containing session data.

    Attributes:
        - m_header (PacketHeader): Header information for the packet.
        - m_weather (uint8): Weather condition (0 = clear, 1 = light cloud, 2 = overcast, 3 = light rain,
                                                4 = heavy rain, 5 = storm).
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
        - m_gearboxAssist (uint8): Gearbox assist status (1 = manual, 2 = manual & suggested gear, 3 = auto).
        - m_pitAssist (uint8): Pit assist status (0 = off, 1 = on).
        - m_pitReleaseAssist (uint8): Pit release assist status (0 = off, 1 = on).
        - m_ERSAssist (uint8): ERS assist status (0 = off, 1 = on).
        - m_DRSAssist (uint8): DRS assist status (0 = off, 1 = on).
        - m_dynamicRacingLine (uint8): Dynamic racing line status (0 = off, 1 = corners only, 2 = full).
        - m_dynamicRacingLineType (uint8): Dynamic racing line type (0 = 2D, 1 = 3D).
        - m_gameMode (uint8): Game mode ID.
        - m_ruleSet (uint8): Ruleset ID.
        - m_timeOfDay (uint32): Local time of day in minutes since midnight.
        - m_sessionLength (uint8): Session length.
        - m_speedUnitsLeadPlayer (uint8): Speed units for the lead player (0 = MPH, 1 = KPH).
        - m_temperatureUnitsLeadPlayer (uint8): Temperature units for the lead player (0 = Celsius, 1 = Fahrenheit).
        - m_speedUnitsSecondaryPlayer (uint8): Speed units for the secondary player (0 = MPH, 1 = KPH).
        - m_temperatureUnitsSecondaryPlayer (uint8): Temperature units for the secondary player
                                                    (0 = Celsius, 1 = Fahrenheit).
        - m_numSafetyCarPeriods (uint8): Number of safety car periods called during the session.
        - m_numVirtualSafetyCarPeriods (uint8): Number of virtual safety car periods called.
        - m_numRedFlagPeriods (uint8): Number of red flags called during the session.
    """

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
        "B" # uint8   - 0 = Perfect, 1 = Approximate
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

    class SafetyCarStatus(Enum):
        """
        Enumeration representing different safety car statuses.

        Attributes:
            NO_SAFETY_CAR (int): No safety car on the track.
            FULL_SAFETY_CAR (int): Full safety car deployed.
            VIRTUAL_SAFETY_CAR (int): Virtual safety car deployed.
            FORMATION_LAP (int): Formation lap in progress.

            Note:
                Each attribute represents a unique safety car status identified by an integer value.
        """

        NO_SAFETY_CAR = 0
        FULL_SAFETY_CAR = 1
        VIRTUAL_SAFETY_CAR = 2
        FORMATION_LAP = 3

        @staticmethod
        def isValid(safety_car_status_code: int):
            """Check if the given safety car status is valid.

            Args:
                flag_type (int): The safety car status to be validated.
                    Also supports type SafetyCarStatus. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(safety_car_status_code, PacketSessionData.SafetyCarStatus):
                return True  # It's already an instance of SafetyCarStatus
            else:
                min_value = min(member.value for member in PacketSessionData.SafetyCarStatus)
                max_value = max(member.value for member in PacketSessionData.SafetyCarStatus)
                return min_value <= safety_car_status_code <= max_value

        def __str__(self):
            """
            Returns a human-readable string representation of the safety car status.

            Returns:
                str: String representation of the safety car status.
            """

            return self.name

    class TrackID(Enum):
        """
        Enum class representing F1 track IDs and their corresponding names.
        """
        Melbourne = 0
        Paul_Ricard = 1
        Shanghai = 2
        Sakhir_Bahrain = 3
        Catalunya = 4
        Monaco = 5
        Montreal = 6
        Silverstone = 7
        Hockenheim = 8
        Hungaroring = 9
        Spa = 10
        Monza = 11
        Singapore = 12
        Suzuka = 13
        Abu_Dhabi = 14
        Texas = 15
        Brazil = 16
        Austria = 17
        Sochi = 18
        Mexico = 19
        Baku_Azerbaijan = 20
        Sakhir_Short = 21
        Silverstone_Short = 22
        Texas_Short = 23
        Suzuka_Short = 24
        Hanoi = 25
        Zandvoort = 26
        Imola = 27
        Portimao = 28
        Jeddah = 29
        Miami = 30
        Las_Vegas = 31
        Losail = 32

        def __str__(self):
            """
            Returns a string representation of the track.
            """
            return {
                "Paul_Ricard": "Paul Ricard",
                "Sakhir_Bahrain": "Sakhir (Bahrain)",
                "Abu_Dhabi": "Abu Dhabi",
                "Baku_Azerbaijan": "Baku (Azerbaijan)",
                "Portimao": "Portimão"
            }.get(self.name, self.name.replace("_", " "))

        @staticmethod
        def isValid(track: int):
            """Check if the given circuit code is valid.

            Args:
                flag_type (int): The circuit code to be validated.
                    Also supports type TrackID. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(track, PacketSessionData.TrackID):
                return True  # It's already an instance of TrackID
            else:
                min_value = min(member.value for member in PacketSessionData.TrackID)
                max_value = max(member.value for member in PacketSessionData.TrackID)
                return min_value <= track <= max_value

    def __init__(self, header, data) -> None:
        """Construct a PacketSessionData object

        Args:
            header (PacketHeader): The parsed header object
            data (bytes): The list of raw bytes representing this packet
        """
        self.m_header: PacketHeader = header          # Header

        # Declare the type hints
        self.m_weather: int
        self.m_trackTemperature: int
        self.m_airTemperature: int
        self.m_totalLaps: int
        self.m_trackLength: float
        self.m_sessionType: int
        self.m_trackId: PacketSessionData.TrackID
        self.m_formula: int
        self.m_sessionTimeLeft: float
        self.m_sessionDuration: float
        self.m_pitSpeedLimit: float
        self.m_gamePaused: bool
        self.m_isSpectating: bool
        self.m_spectatorCarIndex: int
        self.m_sliProNativeSupport: int
        self.m_numMarshalZones: int
        self.m_marshalZones: List[MarshalZone]
        self.m_safetyCarStatus : PacketSessionData.SafetyCarStatus
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
        self.m_gearboxAssist: int
        self.m_pitAssist: int
        self.m_pitReleaseAssist: int
        self.m_ERSAssist: int
        self.m_DRSAssist: int
        self.m_dynamicRacingLine: int
        self.m_dynamicRacingLineType: int
        self.m_gameMode: int
        self.m_ruleSet: int
        self.m_timeOfDay: int
        self.m_sessionLength: int # TODO: make enum
        self.m_speedUnitsLeadPlayer: int
        self.m_temperatureUnitsLeadPlayer: int
        self.m_speedUnitsSecondaryPlayer: int
        self.m_temperatureUnitsSecondaryPlayer: int
        self.m_numSafetyCarPeriods: int
        self.m_numVirtualSafetyCarPeriods: int
        self.m_numRedFlagPeriods: int

        self.m_maxMarshalZones = 21
        self.m_maxWeatherForecastSamples = 56
        # First, section 0
        section_0_raw_data = _extract_sublist(data, 0, self.PACKET_LEN_SECTION_0)
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
        if PacketSessionData.TrackID.isValid(self.m_trackId):
            self.m_trackId = PacketSessionData.TrackID(self.m_trackId)
        if SessionType.isValid(self.m_sessionType):
            self.m_sessionType = SessionType(self.m_sessionType)

        # Next section 1, marshalZones
        section_1_size = MarshalZone.PACKET_LEN * self.m_maxMarshalZones
        section_1_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far+section_1_size)
        byte_index_so_far += section_1_size
        self.m_marshalZones: List[MarshalZone] = []         # List of marshal zones – max 21
        for per_marshal_zone_raw_data in _split_list(section_1_raw_data, MarshalZone.PACKET_LEN):
            self.m_marshalZones.append(MarshalZone(per_marshal_zone_raw_data))
        # Trim the unnecessary marshalZones
        self.m_marshalZones = self.m_marshalZones[:self.m_numMarshalZones]
        section_1_raw_data = None

        # Section 2, till numWeatherForecastSamples
        section_2_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far + self.PACKET_LEN_SECTION_2)
        byte_index_so_far += self.PACKET_LEN_SECTION_2
        unpacked_data = struct.unpack(self.PACKET_FORMAT_SECTION_2, section_2_raw_data)
        (
            self.m_safetyCarStatus, #           // 0 = no safety car, 1 = full 2 = virtual, 3 = formation lap
            self.m_networkGame, #               // 0 = offline, 1 = online
            self.m_numWeatherForecastSamples # // Number of weather samples to follow
        ) = unpacked_data
        if PacketSessionData.SafetyCarStatus.isValid(self.m_safetyCarStatus):
            self.m_safetyCarStatus = PacketSessionData.SafetyCarStatus(self.m_safetyCarStatus)
        section_2_raw_data = None

        # Section 3 - weather forecast samples
        section_3_size = WeatherForecastSample.PACKET_LEN * self.m_maxWeatherForecastSamples
        section_3_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far+section_3_size)
        byte_index_so_far += section_3_size
        self.m_weatherForecastSamples: List[WeatherForecastSample] = []  # Array of weather forecast samples
        for per_weather_sample_raw_data in _split_list(section_3_raw_data, WeatherForecastSample.PACKET_LEN):
            self.m_weatherForecastSamples.append(WeatherForecastSample(per_weather_sample_raw_data))
        # Trim the unnecessary weatherForecastSamples
        self.m_weatherForecastSamples = self.m_weatherForecastSamples[:self.m_numWeatherForecastSamples]
        section_3_raw_data = None

        # Section 4 - rest of the packet
        section_4_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far+self.PACKET_LEN_SECTION_4)
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
            f"Track ID: {self.m_trackId}, "
            f"Formula: {self.m_formula}, "
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
            f"Game Mode: {self.m_gameMode}, "
            f"Rule Set: {self.m_ruleSet}, "
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
            "weather": self.m_weather,
            "track-temperature": self.m_trackTemperature,
            "air-temperature": self.m_airTemperature,
            "total-laps": self.m_totalLaps,
            "track-length": self.m_trackLength,
            "session-type": str(self.m_sessionType),
            "track-id": str(self.m_trackId),
            "formula": self.m_formula,
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
            "gearbox-assist": self.m_gearboxAssist,
            "pit-assist": self.m_pitAssist,
            "pit-release-assist": self.m_pitReleaseAssist,
            "ers-assist": self.m_ERSAssist,
            "drs-assist": self.m_DRSAssist,
            "dynamic-racing-line": self.m_dynamicRacingLine,
            "dynamic-racing-line-type": self.m_dynamicRacingLineType,
            "game-mode": self.m_gameMode,
            "rule-set": self.m_ruleSet,
            "time-of-day": self.m_timeOfDay,
            "session-length": self.m_sessionLength,
            "speed-units-lead-player": self.m_speedUnitsLeadPlayer,
            "temp-units-lead-player": self.m_temperatureUnitsLeadPlayer,
            "speed-units-secondary-player": self.m_speedUnitsSecondaryPlayer,
            "temp-units-secondary-player": self.m_temperatureUnitsSecondaryPlayer,
            "num-safety-car-periods": self.m_numSafetyCarPeriods,
            "num-virtual-safety-car-periods": self.m_numVirtualSafetyCarPeriods,
            "num-red-flag-periods": self.m_numRedFlagPeriods
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data
