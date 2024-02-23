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

from enum import Enum, auto
from typing import List, Any
from f1_packet_info import *
import struct

# ------------------------- PRIVATE FUNCTIONS ----------------------------------

def _split_list(original_list: List[Any], sublist_length: int) -> List[List[Any]]:
    """
    Splits the given list into sublists of a specified length.

    Args:
        original_list (List[Any]): The original list to be split.
        sublist_length (int): The desired length of each sublist.

    Returns:
        List[List[Any]]: A list containing sublists of the specified length.
    """
    return [original_list[i:i + sublist_length] for i in range(0, len(original_list), sublist_length)]

def _extract_sublist(data: bytes, lower_index: int, upper_index: int) -> bytes:
    # Ensure the indices are within bounds
    if lower_index < 0 or upper_index > len(data) or lower_index > upper_index:
        # Return an empty bytes object to indicate an error
        return b''

    # Extract the sub-list
    sub_list: bytes = data[lower_index:upper_index]
    return sub_list

# ------------------------- ERROR CLASSES --------------------------------------

class InvalidPacketLengthError(Exception):
    """
    This exception type is used to indicate to the telemetry manager that there has
    been a parsing error due to receving a packet of unexpected length (possibly
    incomplete or corrupt. or more realistically a bug)
    """
    def __init__(self, message):
        super().__init__("Invalid packet length. " + message)

# -------------------- COMMON ENUMS --------------------------------------------

class F1PacketType(Enum):
    """Class of enum representing the different packet types emitted by the game
    """
    MOTION = 0
    SESSION = 1
    LAP_DATA = 2
    EVENT = 3
    PARTICIPANTS = 4
    CAR_SETUPS = 5
    CAR_TELEMETRY = 6
    CAR_STATUS = 7
    FINAL_CLASSIFICATION = 8
    LOBBY_INFO = 9
    CAR_DAMAGE = 10
    SESSION_HISTORY = 11
    TYRE_SETS = 12
    MOTION_EX = 13

    @staticmethod
    def isValid(packet_type) -> bool:
        """Check if the given packet type ID is valid

        Args:
            packet_type (int or F1PacketType): The packet type to be validated

        Returns:
            bool: True if valid, else False
        """

        if isinstance(packet_type, F1PacketType):
            return True  # It's already an instance of F1PacketType
        else:
            # check if the integer value falls in range
            min_value = min(member.value for member in F1PacketType)
            max_value = max(member.value for member in F1PacketType)
            return min_value <= packet_type <= max_value

    def __str__(self) -> str:
        """to_string method

        Returns:
            str: string representation of this enum
        """
        if F1PacketType.isValid(self.value):
            return self.name
        else:
            return 'packet type ' + str(self.value)

class ResultStatus(Enum):
    """
    Enumeration representing the result status of a driver after a racing session.
    """

    INVALID = 0
    INACTIVE = 1
    ACTIVE = 2
    FINISHED = 3
    DID_NOT_FINISH = 4
    DISQUALIFIED = 5
    NOT_CLASSIFIED = 6
    RETIRED = 7

    @staticmethod
    def isValid(result_status: int) -> bool:
        """Check if the given result status is valid.

        Args:
            result_status (int): The result status to be validated.

        Returns:
            bool: True if valid.
        """
        if isinstance(result_status, ResultStatus):
            return True  # It's already an instance of ResultStatus
        else:
            min_value = min(member.value for member in ResultStatus)
            max_value = max(member.value for member in ResultStatus)
            return min_value <= result_status <= max_value

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the result status.

        Returns:
            str: String representation of the result status.
        """
        status_mapping = {
            0: "INVALID",
            1: "INACTIVE",
            2: "ACTIVE",
            3: "FINISHED",
            4: "DID_NOT_FINISH",
            5: "DISQUALIFIED",
            6: "NOT_CLASSIFIED",
            7: "RETIRED",
        }
        return status_mapping.get(self.value, "---")

class SessionType(Enum):
    """
    Enum class representing F1 session types.
    """
    UNKNOWN = 0
    PRACTICE_1 = 1
    PRACTICE_2 = 2
    PRACTICE_3 = 3
    SHORT_PRACTICE = 4
    QUALIFYING_1 = 5
    QUALIFYING_2 = 6
    QUALIFYING_3 = 7
    SHORT_QUALIFYING = 8
    ONE_SHOT_QUALIFYING = 9
    RACE = 10
    RACE_2 = 11
    RACE_3 = 12
    TIME_TRIAL = 13

    @staticmethod
    def isValid(session_type: int):
        """
        Check if the given session type is valid.

        Args:
            session_type (int): The session type to be validated.

        Returns:
            bool: True if valid
        """
        if isinstance(session_type, SessionType):
            return True  # It's already an instance of SessionType
        else:
            min_value = min(member.value for member in SessionType)
            max_value = max(member.value for member in SessionType)
            return min_value <= session_type <= max_value

    def __str__(self):
        """
        Return a string representation of the SessionType with spaces.

        Returns:
            str: String representation of the SessionType.
        """
        return {
            SessionType.UNKNOWN : "N/A",
            SessionType.PRACTICE_1 : "Practice 1",
            SessionType.PRACTICE_2 : "Practice 2",
            SessionType.PRACTICE_3 : "Practice 3",
            SessionType.SHORT_PRACTICE : "Short Practice",
            SessionType.QUALIFYING_1 : "Qualifying 1",
            SessionType.QUALIFYING_2 : "Qualifying 2",
            SessionType.QUALIFYING_3 : "Qualifying 3",
            SessionType.SHORT_QUALIFYING : "Short Qualifying",
            SessionType.ONE_SHOT_QUALIFYING : "One Shot Qualifying",
            SessionType.RACE  : "Race",
            SessionType.RACE_2  : "Race 2",
            SessionType.RACE_3  : "Race 3",
            SessionType.TIME_TRIAL  : "Time Trial",
        }.get(self, " ")

# -------------------- HEADER PARSING ------------------------------------------

class PacketHeader:
    """
    A class for parsing the Packet Header of a telemetry packet in a racing game.

    The packet header structure is as follows:

    Attributes:
        - m_packet_format (int): The format of the telemetry packet (2023).
        - m_game_year (int): The game year, represented by the last two digits (e.g., 23).
        - m_game_major_version (int): The game's major version (X.00).
        - m_game_minor_version (int): The game's minor version (1.XX).
        - m_packet_version (int): The version of this packet type, starting from 1.
        - m_packet_id (int): Identifier for the packet type.
        - m_session_uid (int): Unique identifier for the session.
        - m_session_time (float): Timestamp of the session.
        - m_frame_identifier (int): Identifier for the frame the data was retrieved on.
        - m_overall_frame_identifier (int): Overall identifier for the frame, not going back after flashbacks.
        - m_player_car_index (int): Index of the player's car in the array.
        - m_secondary_player_car_index (int): Index of the secondary player's car in the array (255 if no second player).
    """
    def __init__(self, data: bytes) -> None:
        """
        Initializes the PacketHeaderParser with the raw packet data.

        Args:
            data (bytes): Raw binary data representing the packet header.
        """

        # Unpack the data
        unpacked_data = struct.unpack(header_format_string, data)

        # Assign values to individual variables
        self.m_packetFormat, self.m_gameYear, self.m_gameMajorVersion, self.m_gameMinorVersion, \
        self.m_packetVersion, self.m_packetId, self.m_sessionUID, self.m_sessionTime, \
        self.m_frameIdentifier, self.m_overallFrameIdentifier, self.m_playerCarIndex, \
        self.m_secondaryPlayerCarIndex = unpacked_data

        # Set packet ID as enum type
        if F1PacketType.isValid(self.m_packetId):
            self.m_packetId = F1PacketType(self.m_packetId)
            self.is_supported_packet_type = True
        else:
            self.is_supported_packet_type = False

    def __str__(self) -> str:
        return (
            f"PacketHeader("
            f"Format: {self.m_packetFormat}, "
            f"Year: {self.m_gameYear}, "
            f"Major Version: {self.m_gameMajorVersion}, "
            f"Minor Version: {self.m_gameMinorVersion}, "
            f"Packet Version: {self.m_packetVersion}, "
            f"Packet ID: {self.m_packetId}, "
            f"Session UID: {self.m_sessionUID}, "
            f"Session Time: {self.m_sessionTime}, "
            f"Frame Identifier: {self.m_frameIdentifier}, "
            f"Overall Frame Identifier: {self.m_overallFrameIdentifier}, "
            f"Player Car Index: {self.m_playerCarIndex}, "
            f"Secondary Player Car Index: {self.m_secondaryPlayerCarIndex})"
        )

    def isPacketTypeSupported(self) -> bool:
        """Check if this packet type is supported

        Returns:
            bool: self explanatory
        """
        return self.is_supported_packet_type

# ------------------------- PACKET TYPE 0 - MOTION -----------------------------

class CarMotionData:
    """
    A class for parsing the Car Motion Data of a telemetry packet in a racing game.

    The car motion data structure is as follows:


    """
    def __init__(self, data: bytes) -> None:
        """A class for parsing the data related to the motion of the F1 car

        Args:
            data (List[bytes]): list containing the raw bytes for this packet

        Attributes:
        - m_world_position_x (float): World space X position - meters.
        - m_world_position_y (float): World space Y position.
        - m_world_position_z (float): World space Z position.
        - m_world_velocity_x (float): Velocity in world space X – meters/s.
        - m_world_velocity_y (float): Velocity in world space Y.
        - m_world_velocity_z (float): Velocity in world space Z.
        - m_world_forward_dir_x (int): World space forward X direction (normalised).
        - m_world_forward_dir_y (int): World space forward Y direction (normalised).
        - m_world_forward_dir_z (int): World space forward Z direction (normalised).
        - m_world_right_dir_x (int): World space right X direction (normalised).
        - m_world_right_dir_y (int): World space right Y direction (normalised).
        - m_world_right_dir_z (int): World space right Z direction (normalised).
        - m_g_force_lateral (float): Lateral G-Force component.
        - m_g_force_longitudinal (float): Longitudinal G-Force component.
        - m_g_force_vertical (float): Vertical G-Force component.
        - m_yaw (float): Yaw angle in radians.
        - m_pitch (float): Pitch angle in radians.
        - m_roll (float): Roll angle in radians.
        """
        unpacked_data = struct.unpack(motion_format_string, data)

        self.m_worldPositionX, self.m_worldPositionY, self.m_worldPositionZ, \
        self.m_worldVelocityX, self.m_worldVelocityY, self.m_worldVelocityZ, \
        self.m_worldForwardDirX, self.m_worldForwardDirY, self.m_worldForwardDirZ, \
        self.m_worldRightDirX, self.m_worldRightDirY, self.m_worldRightDirZ, \
        self.m_gForceLateral, self.m_gForceLongitudinal, self.m_gForceVertical, \
        self.m_yaw, self.m_pitch, self.m_roll = unpacked_data

    def __str__(self) -> str:
        return (
            f"CarMotionData("
            f"World Position: ({self.m_worldPositionX}, {self.m_worldPositionY}, {self.m_worldPositionZ}), "
            f"World Velocity: ({self.m_worldVelocityX}, {self.m_worldVelocityY}, {self.m_worldVelocityZ}), "
            f"World Forward Dir: ({self.m_worldForwardDirX}, {self.m_worldForwardDirY}, {self.m_worldForwardDirZ}), "
            f"World Right Dir: ({self.m_worldRightDirX}, {self.m_worldRightDirY}, {self.m_worldRightDirZ}), "
            f"G-Force Lateral: {self.m_gForceLateral}, "
            f"G-Force Longitudinal: {self.m_gForceLongitudinal}, "
            f"G-Force Vertical: {self.m_gForceVertical}, "
            f"Yaw: {self.m_yaw}, "
            f"Pitch: {self.m_pitch}, "
            f"Roll: {self.m_roll})"
        )

class PacketMotionData:

    def __init__(self, header:PacketHeader, packet: bytes) -> None:
        """A class for parsing the Motion Data Packet of a telemetry packet in a racing game.

        Args:
            header (PacketHeader): Incoming packet header
            packet (List[bytes]): list containing the raw bytes for this packet

        Attributes:
        - m_header (PacketHeader): The header of the telemetry packet.
        - m_car_motion_data (list): List of CarMotionData objects containing data for all cars on track.

        Raises:
            InvalidPacketLengthError: If received length is not as per expectation
        """

        self.m_header: PacketHeader = header       # PacketHeader
        if ((len(packet) % F1_23_MOTION_PACKET_PER_CAR_LEN) != 0):
            raise InvalidPacketLengthError("Received packet length " + str(len(packet)) + " is not a multiple of " +
                                            str(F1_23_MOTION_PACKET_PER_CAR_LEN))
        self.m_carMotionData: List[CarMotionData] = []
        motion_data_packet_per_car = _split_list(packet, F1_23_MOTION_PACKET_PER_CAR_LEN)
        for motion_data_packet in motion_data_packet_per_car:
            self.m_carMotionData.append(CarMotionData(motion_data_packet))

    def __str__(self) -> str:
        """
        Return a string representation of the PacketMotionData instance.

        Returns:
        - str: String representation of PacketMotionData.
        """
        car_motion_data_str = ", ".join(str(car) for car in self.m_carMotionData)
        return f"PacketMotionData(Header: {str(self.m_header)}, CarMotionData: [{car_motion_data_str}])"


# ------------------------- PACKET TYPE 1 - SESSION ----------------------------

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
            flag_type (int): The flag code to be validated. Also supports type MarshalZoneFlagType. Returns true in this
                case

        Returns:
            bool: true if valid
        """
        if isinstance(flag_type, MarshalZoneFlagType):
            return True  # It's already an instance of MarshalZoneFlagType
        else:
            min_value = min(member.value for member in MarshalZoneFlagType)
            max_value = max(member.value for member in MarshalZoneFlagType)
            return min_value <= flag_type <= max_value

    def __str__(self):
        if F1PacketType.isValid(self.value):
            return self.name
        else:
            return 'Marshal Zone Flag type ' + str(self.value)

class MarshalZone:
    """
    A class for parsing the Marshal Zone data within a telemetry packet in a racing game.

    The Marshal Zone structure is as follows:

    Attributes:
        - m_zone_start (float): Fraction (0..1) of the way through the lap the marshal zone starts.
        - m_zone_flag (MarshalZoneFlagType): Refer to the enum type for various options
    """
    def __init__(self, data: bytes) -> None:
        """Unpack the given raw bytes into this object

        Args:
            data (bytes): List of raw bytes received as part of this
        """

        unpacked_data = struct.unpack(marshal_zone_format_str, data)
        (
            self.m_zoneStart,   # float - Fraction (0..1) of way through the lap the marshal zone starts
            self.m_zoneFlag     # int8 - -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
        ) = unpacked_data

        if MarshalZoneFlagType.isValid(self.m_zoneFlag):
            self.m_zoneFlag = MarshalZoneFlagType(self.m_zoneFlag)

    def __str__(self) -> str:
        return f"MarshalZone(Start: {self.m_zoneStart}, Flag: {self.m_zoneFlag})"

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
                return True  # It's already an instance of SafetyCarStatus
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
                return True  # It's already an instance of SafetyCarStatus
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
                return True  # It's already an instance of SafetyCarStatus
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

        unpacked_data = struct.unpack(weather_forecast_sample_format_str, data)
        (
            self.m_sessionType,                   # uint8
            self.m_timeOffset,                    # uint8
            self.m_weather,                       # uint8
            self.m_trackTemperature,              # int8
            self.m_trackTemperatureChange,        # int8
            self.m_airTemperature,                # int8
            self.m_airTemperatureChange,          # int8
            self.m_rainPercentage                 # uint8
        ) = unpacked_data

        if WeatherForecastSample.WeatherCondition.isValid(self.m_weather):
            self.m_weather = WeatherForecastSample.WeatherCondition(self.m_weather)
        if WeatherForecastSample.AirTemperatureChange.isValid(self.m_airTemperatureChange):
            self.m_airTemperatureChange = WeatherForecastSample.AirTemperatureChange(self.m_airTemperatureChange)
        if WeatherForecastSample.TrackTemperatureChange.isValid(self.m_trackTemperatureChange):
            self.m_trackTemperatureChange = WeatherForecastSample.TrackTemperatureChange(self.m_trackTemperatureChange)
        if SessionType.isValid(self.m_sessionType):
            self.m_sessionType = SessionType(self.m_sessionType)

    def __str__(self) -> str:
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
        if isinstance(safety_car_status_code, SafetyCarStatus):
            return True  # It's already an instance of SafetyCarStatus
        else:
            min_value = min(member.value for member in SafetyCarStatus)
            max_value = max(member.value for member in SafetyCarStatus)
            return min_value <= safety_car_status_code <= max_value

    def __str__(self):
        """
        Returns a human-readable string representation of the safety car status.

        Returns:
            str: String representation of the safety car status.
        """

        if self == SafetyCarStatus.NO_SAFETY_CAR:
            return str()
        elif self == SafetyCarStatus.FULL_SAFETY_CAR:
            return "Full Safety Car"
        elif self == SafetyCarStatus.VIRTUAL_SAFETY_CAR:
            return "Virtual Safety Car"
        elif self == SafetyCarStatus.FORMATION_LAP:
            return "Formation Lap"
        else:
            return "Unknown Safety Car Status"

class PacketSessionData:
    """
    A class for parsing the Session Data Packet of a telemetry packet in a racing game.

    The session data packet structure is defined in the F1 23 UDP Specification Appendix.

    Attributes:
        - m_header (PacketHeader): The header of the telemetry packet.
        - m_weather (int): Weather condition - see F1 23 UDP Specification Appendix.
        - m_track_temperature (int): Track temperature in degrees Celsius.
        - m_air_temperature (int): Air temperature in degrees Celsius.
        - m_total_laps (int): Total number of laps in this race.
        - m_track_length (int): Track length in meters.
        - m_session_type (SessionType): See SessionType enum for more info
        - m_track_id (TrackID): See the TrackID enumeration inside this class for more info
        - m_formula (int): Formula type - see F1 23 UDP Specification Appendix.
        - m_session_time_left (int): Time left in session in seconds.
        - m_session_duration (int): Session duration in seconds.
        - m_pit_speed_limit (int): Pit speed limit in kilometers per hour.
        - m_game_paused (int): Whether the game is paused – network game only.
        - m_is_spectating (int): Whether the player is spectating.
        - m_spectator_car_index (int): Index of the car being spectated.
        - m_sli_pro_native_support (int): SLI Pro support - 0 = inactive, 1 = active.
        - m_num_marshal_zones (int): Number of marshal zones to follow.
        - m_marshal_zones (list): List of MarshalZone objects - see F1 23 UDP Specification Appendix.
        - m_safety_car_status (int): Safety car status - see F1 23 UDP Specification Appendix.
        - m_network_game (int): Network game status - 0 = offline, 1 = online.
        - m_num_weather_forecast_samples (int): Number of weather samples to follow.
        - m_weather_forecast_samples (list): List of WeatherForecastSample objects - see F1 23 UDP Specification Appendix.
        - m_forecast_accuracy (int): Forecast accuracy - 0 = Perfect, 1 = Approximate.
        - ... (Other attributes documented in the F1 23 UDP Specification Appendix)
    """

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

        self.m_maxMarshalZones = 21
        self.m_maxWeatherForecastSamples = 56
        # First, section 0
        section_0_raw_data = _extract_sublist(data, 0, F1_23_SESSION_SECTION_0_PACKET_LEN)
        byte_index_so_far = F1_23_SESSION_SECTION_0_PACKET_LEN
        unpacked_data = struct.unpack(packet_session_section_0_format_str, section_0_raw_data)
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
        section_1_size = marshal_zone_packet_len * self.m_maxMarshalZones
        section_1_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far+section_1_size)
        byte_index_so_far += section_1_size
        self.m_marshalZones: List[MarshalZone] = []         # List of marshal zones – max 21
        for per_marshal_zone_raw_data in _split_list(section_1_raw_data, marshal_zone_packet_len):
            self.m_marshalZones.append(MarshalZone(per_marshal_zone_raw_data))
        # Trim the unnecessary marshalZones
        self.m_marshalZones = self.m_marshalZones[:self.m_numMarshalZones]
        section_1_raw_data = None

        # Section 2, till numWeatherForecastSamples
        section_2_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far + F1_23_SESSION_SECTION_2_PACKET_LEN)
        byte_index_so_far += F1_23_SESSION_SECTION_2_PACKET_LEN
        unpacked_data = struct.unpack(packet_session_section_2_format_str, section_2_raw_data)
        (
            self.m_safetyCarStatus, #           // 0 = no safety car, 1 = full 2 = virtual, 3 = formation lap
            self.m_networkGame, #               // 0 = offline, 1 = online
            self.m_numWeatherForecastSamples # // Number of weather samples to follow
        ) = unpacked_data
        if SafetyCarStatus.isValid(self.m_safetyCarStatus):
            self.m_safetyCarStatus = SafetyCarStatus(self.m_safetyCarStatus)
        section_2_raw_data = None

        # Section 3 - weather forecast samples
        section_3_size = weather_forecast_sample_packet_len * self.m_maxWeatherForecastSamples
        section_3_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far+section_3_size)
        byte_index_so_far += section_3_size
        self.m_weatherForecastSamples: List[WeatherForecastSample] = []  # Array of weather forecast samples
        for per_weather_sample_raw_data in _split_list(section_3_raw_data, weather_forecast_sample_packet_len):
            self.m_weatherForecastSamples.append(WeatherForecastSample(per_weather_sample_raw_data))
        # Trim the unnecessary weatherForecastSamples
        self.m_weatherForecastSamples = self.m_weatherForecastSamples[:self.m_numWeatherForecastSamples]
        section_3_raw_data = None

        # Section 4 - rest of the packet
        section_4_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far+F1_23_SESSION_SECTION_4_PACKET_LEN)
        unpacked_data = struct.unpack(packet_session_section_4_format_str, section_4_raw_data)
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

# ------------------------- PACKET TYPE 2 - LAP DATA----------------------------

class LapData:
    """
    Class representing lap data.
    Attributes:
        m_lastLapTimeInMS (uint32): Last lap time in milliseconds.
        m_currentLapTimeInMS (uint32): Current time around the lap in milliseconds.
        m_sector1TimeInMS (uint16): Sector 1 time in milliseconds.
        m_sector1TimeMinutes (uint8): Sector 1 whole minute part.
        m_sector2TimeInMS (uint16): Sector 2 time in milliseconds.
        m_sector2TimeMinutes (uint8): Sector 2 whole minute part.
        m_deltaToCarInFrontInMS (uint16): Time delta to the car in front in milliseconds.
        m_deltaToRaceLeaderInMS (uint16): Time delta to the race leader in milliseconds.
        m_lapDistance (float): Distance vehicle is around the current lap in meters.
        m_totalDistance (float): Total distance traveled in the session in meters.
        m_safetyCarDelta (float): Delta in seconds for the safety car.
        m_carPosition (uint8): Car race position.
        m_currentLapNum (uint8): Current lap number.
        m_pitStatus (PitStatus): See the PitStatus enumeration
        m_numPitStops (uint8): Number of pit stops taken in this race.
        m_sector (Sector): See the sector enumeration
        m_currentLapInvalid (bool): Current lap validity (False = valid, True = invalid).
        m_penalties (uint8): Accumulated time penalties in seconds to be added.
        m_totalWarnings (uint8): Accumulated number of warnings issued.
        m_cornerCuttingWarnings (uint8): Accumulated number of corner cutting warnings issued.
        m_numUnservedDriveThroughPens (uint8): Number of drive-through penalties left to serve.
        m_numUnservedStopGoPens (uint8): Number of stop-go penalties left to serve.
        m_gridPosition (uint8): Grid position the vehicle started the race in.
        m_driverStatus (DriverStatus): Status of the driver.
        m_resultStatus (ResultStatus): Result status of the driver.
        m_pitLaneTimerActive (bool): Pit lane timing (False = inactive, True = active).
        m_pitLaneTimeInLaneInMS (uint16): If active, the current time spent in the pit lane in ms.
        m_pitStopTimerInMS (uint16): Time of the actual pit stop in ms.
        m_pitStopShouldServePen (uint8): Whether the car should serve a penalty at this stop.
    """
    class DriverStatus(Enum):
        """
        Enumeration representing the status of a driver during a racing session.

        Note:
            Each attribute represents a unique driver status identified by an integer value.
        """

        IN_GARAGE = 0
        FLYING_LAP = 1
        IN_LAP = 2
        OUT_LAP = 3
        ON_TRACK = 4

        @staticmethod
        def isValid(driver_status: int) -> bool:
            """Check if the given driver status is valid.

            Args:
                driver_status (int): The driver status to be validated.

            Returns:
                bool: True if valid.
            """
            if isinstance(driver_status, LapData.DriverStatus):
                return True  # It's already an instance of DriverStatus
            else:
                min_value = min(member.value for member in LapData.DriverStatus)
                max_value = max(member.value for member in LapData.DriverStatus)
                return min_value <= driver_status <= max_value

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the driver status.

            Returns:
                str: String representation of the driver status.
            """
            status_mapping = {
                0: "IN_GARAGE",
                1: "FLYING_LAP",
                2: "IN_LAP",
                3: "OUT_LAP",
                4: "ON_TRACK",
            }
            return status_mapping.get(self.value, "---")
    class PitStatus(Enum):
        """
        Enumeration representing the pit status of a driver during a racing session.
        """

        NONE = 0
        PITTING = 1
        IN_PIT_AREA = 2

        @staticmethod
        def isValid(pit_status: int) -> bool:
            """Check if the given pit status is valid.

            Args:
                pit_status (int): The pit status to be validated.

            Returns:
                bool: True if valid.
            """
            if isinstance(pit_status, LapData.PitStatus):
                return True  # It's already an instance of PitStatus
            else:
                min_value = min(member.value for member in LapData.PitStatus)
                max_value = max(member.value for member in LapData.PitStatus)
                return min_value <= pit_status <= max_value

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the pit status.

            Returns:
                str: String representation of the pit status.
            """
            status_mapping = {
                0: "NONE",
                1: "PITTING",
                2: "IN_PIT_AREA",
            }
            return status_mapping.get(self.value, "---")

    class Sector(Enum):
        """
        Enumeration representing the sector of a racing track.
        """

        SECTOR1 = 0
        SECTOR2 = 1
        SECTOR3 = 2

        @staticmethod
        def isValid(sector: int) -> bool:
            """Check if the given sector is valid.

            Args:
                sector (int): The sector to be validated.

            Returns:
                bool: True if valid.
            """
            if isinstance(sector, LapData.Sector):
                return True  # It's already an instance of Sector
            else:
                min_value = min(member.value for member in LapData.Sector)
                max_value = max(member.value for member in LapData.Sector)
                return min_value <= sector <= max_value

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the sector.

            Returns:
                str: String representation of the sector.
            """
            sector_mapping = {
                0: "SECTOR1",
                1: "SECTOR2",
                2: "SECTOR3",
            }
            return sector_mapping.get(self.value, "---")

    def __init__(self, data) -> None:
        """
        Initialize LapData instance by unpacking binary data.

        Args:
        - data (bytes): Binary data containing lap information.

        Raises:
        - struct.error: If the binary data does not match the expected format.
        """
        unpacked_data = struct.unpack(lap_time_packet_format_str, data)

        # Assign the members from unpacked_data
        (
            self.m_lastLapTimeInMS,
            self.m_currentLapTimeInMS,
            self.m_sector1TimeInMS,
            self.m_sector1TimeMinutes,
            self.m_sector2TimeInMS,
            self.m_sector2TimeMinutes,
            self.m_deltaToCarInFrontInMS,
            self.m_deltaToRaceLeaderInMS,
            self.m_lapDistance,
            self.m_totalDistance,
            self.m_safetyCarDelta,
            self.m_carPosition,
            self.m_currentLapNum,
            self.m_pitStatus,
            self.m_numPitStops,
            self.m_sector,
            self.m_currentLapInvalid,
            self.m_penalties,
            self.m_totalWarnings,
            self.m_cornerCuttingWarnings,
            self.m_numUnservedDriveThroughPens,
            self.m_numUnservedStopGoPens,
            self.m_gridPosition,
            self.m_driverStatus,
            self.m_resultStatus,
            self.m_pitLaneTimerActive,
            self.m_pitLaneTimeInLaneInMS,
            self.m_pitStopTimerInMS,
            self.m_pitStopShouldServePen,
        ) = unpacked_data

        if LapData.DriverStatus.isValid(self.m_driverStatus):
            self.m_driverStatus = LapData.DriverStatus(self.m_driverStatus)
        if ResultStatus.isValid(self.m_resultStatus):
            self.m_resultStatus = ResultStatus(self.m_resultStatus)
        if LapData.PitStatus.isValid(self.m_pitStatus):
            self.m_pitStatus = LapData.PitStatus(self.m_pitStatus)
        if LapData.Sector.isValid(self.m_sector):
            self.m_sector = LapData.Sector(self.m_sector)
        self.m_currentLapInvalid = bool(self.m_currentLapInvalid)
        self.m_pitLaneTimerActive = bool(self.m_pitLaneTimerActive)

    def __str__(self) -> str:
        """
        Return a string representation of the LapData instance.

        Returns:
        - str: String representation of LapData.
        """
        return (
            f"LapData("
            f"Last Lap Time: {self.m_lastLapTimeInMS} ms, "
            f"Current Lap Time: {self.m_currentLapTimeInMS} ms, "
            f"Sector 1 Time: {self.m_sector1TimeInMS} ms, "
            f"Sector 1 Time (Minutes): {self.m_sector1TimeMinutes}, "
            f"Sector 2 Time: {self.m_sector2TimeInMS} ms, "
            f"Sector 2 Time (Minutes): {self.m_sector2TimeMinutes}, "
            f"Delta To Car In Front: {self.m_deltaToCarInFrontInMS} ms, "
            f"Delta To Race Leader: {self.m_deltaToRaceLeaderInMS} ms, "
            f"Lap Distance: {self.m_lapDistance} meters, "
            f"Total Distance: {self.m_totalDistance} meters, "
            f"Safety Car Delta: {self.m_safetyCarDelta} seconds, "
            f"Car Position: {self.m_carPosition}, "
            f"Current Lap Number: {self.m_currentLapNum}, "
            f"Pit Status: {self.m_pitStatus}, "
            f"Number of Pit Stops: {self.m_numPitStops}, "
            f"Sector: {self.m_sector}, "
            f"Current Lap Invalid: {self.m_currentLapInvalid}, "
            f"Penalties: {self.m_penalties}, "
            f"Total Warnings: {self.m_totalWarnings}, "
            f"Corner Cutting Warnings: {self.m_cornerCuttingWarnings}, "
            f"Unserved Drive Through Pens: {self.m_numUnservedDriveThroughPens}, "
            f"Unserved Stop Go Pens: {self.m_numUnservedStopGoPens}, "
            f"Grid Position: {self.m_gridPosition}, "
            f"Driver Status: {self.m_driverStatus}, "
            f"Result Status: {self.m_resultStatus}, "
            f"Pit Lane Timer Active: {self.m_pitLaneTimerActive}, "
            f"Pit Lane Time in Lane: {self.m_pitLaneTimeInLaneInMS} ms, "
            f"Pit Stop Timer: {self.m_pitStopTimerInMS} ms, "
            f"Pit Stop Should Serve Penalty: {self.m_pitStopShouldServePen})"
        )

class PacketLapData:
    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """
        Initialize PacketLapData instance by unpacking binary data.

        Args:
        - header (PacketHeader): Packet header information.
        - packet (bytes): Binary data containing lap data packet.

        Raises:
        - InvalidPacketLengthError: If the received packet length is not as expected.

        Unpacked Data Members:
        - m_header (PacketHeader): Packet header information.
        - m_LapData (List[LapData]): List of LapData instances for all cars on track.
        - m_LapDataCount (int): Number of LapData entries (constant value: 22).
        - m_timeTrialPBCarIdx (uint8): Index of Personal Best car in time trial (255 if invalid).
        - m_timeTrialRivalCarIdx (uint8): Index of Rival car in time trial (255 if invalid).

        Returns:
        - None
        """
        self.m_header: PacketHeader = header
        self.m_LapData: List[LapData] = []  # LapData[22]
        self.m_LapDataCount = 22
        len_of_lap_data_array = self.m_LapDataCount * F1_23_LAP_DATA_PACKET_PER_CAR_LEN

        # 2 extra bytes for the two uint8 that follow LapData
        expected_len = (len_of_lap_data_array + 2)
        if len(packet) != expected_len:
            raise InvalidPacketLengthError(
                f"Received LapDataPacket length {len(packet)} is not of expected length {expected_len}"
            )

        lap_data_packet_raw = _extract_sublist(packet, 0, len_of_lap_data_array)
        for lap_data_packet in _split_list(lap_data_packet_raw, F1_23_LAP_DATA_PACKET_PER_CAR_LEN):
            self.m_LapData.append(LapData(lap_data_packet))

        time_trial_section_raw = _extract_sublist(packet, len_of_lap_data_array, len(packet))
        unpacked_data = struct.unpack('<bb', time_trial_section_raw)
        (
            self.m_timeTrialPBCarIdx,
            self.m_timeTrialRivalCarIdx
        ) = unpacked_data

    def __str__(self) -> str:
        """
        Return a string representation of the PacketLapData instance.

        Returns:
        - str: String representation of PacketLapData.
        """
        lap_data_str = ", ".join(str(data) for data in self.m_LapData)
        return f"PacketLapData(Header: {str(self.m_header)}, Car Lap Data: [{lap_data_str}])"

# ------------------------- PACKET TYPE 3 - EVENT ------------------------------

class EventPacketType(Enum):
    """
    Enum class representing different event types.
    """

    # Session Started: Sent when the session starts
    SESSION_STARTED = "SSTA"

    # Session Ended: Sent when the session ends
    SESSION_ENDED = "SEND"

    # Fastest Lap: When a driver achieves the fastest lap
    FASTEST_LAP = "FTLP"

    # Retirement: When a driver retires
    RETIREMENT = "RTMT"

    # DRS enabled: Race control have enabled DRS
    DRS_ENABLED = "DRSE"

    # DRS disabled: Race control have disabled DRS
    DRS_DISABLED = "DRSD"

    # Team mate in pits: Your team mate has entered the pits
    TEAM_MATE_IN_PITS = "TMPT"

    # Chequered flag: The chequered flag has been waved
    CHEQUERED_FLAG = "CHQF"

    # Race Winner: The race winner is announced
    RACE_WINNER = "RCWN"

    # Penalty Issued: A penalty has been issued – details in event
    PENALTY_ISSUED = "PENA"

    # Speed Trap Triggered: Speed trap has been triggered by fastest speed
    SPEED_TRAP_TRIGGERED = "SPTP"

    # Start lights: Start lights – number shown
    START_LIGHTS = "STLG"

    # Lights out: Lights out
    LIGHTS_OUT = "LGOT"

    # Drive through served: Drive through penalty served
    DRIVE_THROUGH_SERVED = "DTSV"

    # Stop go served: Stop go penalty served
    STOP_GO_SERVED = "SGSV"

    # Flashback: Flashback activated
    FLASHBACK = "FLBK"

    # Button status: Button status changed
    BUTTON_STATUS = "BUTN"

    # Red Flag: Red flag shown
    RED_FLAG = "RDFL"

    # Overtake: Overtake occurred
    OVERTAKE = "OVTK"

    @staticmethod
    def isValid(event_type: str) -> bool:
        """
        Check if the input event type string maps to a valid enum value.

        Args:
            event_type (str): The event type string to check.

        Returns:
            bool: True if the event type is valid, False otherwise.
        """
        if isinstance(event_type, EventPacketType):
            return True
        try:
            EventPacketType(event_type)
            return True
        except ValueError:
            return False

class FastestLap:
    """
    A class representing the data structure for the fastest lap information.

    Attributes:
        vehicleIdx (int): Vehicle index of the car achieving the fastest lap.
        lapTime (float): Lap time in seconds.
    """

    def __init__(self, data: bytes):
        """
        Initializes a FastestLap object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        format_str = "<Bf"
        unpacked_data = struct.unpack(format_str, data[0:struct.calcsize(format_str)])
        (
            self.vehicleIdx,
            self.lapTime
        ) = unpacked_data

    def __str__(self) -> str:
        """
        Returns a string representation of the FastestLap object.

        Returns:
            str: String representation of the object.
        """
        return f"FastestLap(vehicleIdx={self.vehicleIdx}, lapTime={self.lapTime})"

class Retirement:
    """
    The class representing the RETIREMENT event. This is sent when any driver retires or DNF's
    Attributes:
        vehicleIdx(int) - The index of the vehicle that retired
    """
    def __init__(self, data):
        format_str = "<B"
        self.vehicleIdx = struct.unpack(format_str, data[0:struct.calcsize(format_str)])[0]

    def __str__(self):
        return f"Retirement(vehicleIdx={self.vehicleIdx})"

class TeamMateInPits:
    """
    The class representing the TEAMMATE IN PITS event. This is sent when the player's teammate pits.
    This is not sent in spectator mode
    Attributes:
        vehicleIdx(int) - The index of the vehicle that pitted (the teammates index)
    """
    def __init__(self, data):
        format_str = "<B"
        self.vehicleIdx = struct.unpack(format_str, data[0:struct.calcsize(format_str)])[0]

    def __str__(self):
        return f"TeamMateInPits(vehicleIdx={self.vehicleIdx})"

class RaceWinner:
    def __init__(self, data):
        format_str = "<B"
        self.vehicleIdx = struct.unpack(format_str, data[0:struct.calcsize(format_str)])[0]

    def __str__(self):
        return f"RaceWinner(vehicleIdx={self.vehicleIdx})"

class Penalty:
    def __init__(self, data):

        format_str = "<BBBBBBB"
        unpacked_data = struct.unpack(format_str, data[0:struct.calcsize(format_str)])
        (
            self.penaltyType,
            self.infringementType,
            self.vehicleIdx,
            self.otherVehicleIdx,
            self.time,
            self.lapNum,
            self.placesGained
        ) = unpacked_data

    def __str__(self):
        return f"Penalty(penaltyType={self.penaltyType}, infringementType={self.infringementType}, " \
               f"vehicleIdx={self.vehicleIdx}, otherVehicleIdx={self.otherVehicleIdx}, time={self.time}, " \
               f"lapNum={self.lapNum}, placesGained={self.placesGained})"

class SpeedTrap:
    def __init__(self, data):

        format_str = "<BfBBBf"
        unpacked_data = struct.unpack(format_str, data[0:struct.calcsize(format_str)])
        (
            self.vehicleIdx,
            self.speed,
            self.isOverallFastestInSession,
            self.isDriverFastestInSession,
            self.fastestVehicleIdxInSession,
            self.fastestSpeedInSession
        ) = unpacked_data

    def __str__(self):
        return f"SpeedTrap(vehicleIdx={self.vehicleIdx}, speed={self.speed}, " \
               f"isOverallFastestInSession={self.isOverallFastestInSession}, " \
               f"isDriverFastestInSession={self.isDriverFastestInSession}, " \
               f"fastestVehicleIdxInSession={self.fastestVehicleIdxInSession}, " \
               f"fastestSpeedInSession={self.fastestSpeedInSession})"

class StartLights:
    def __init__(self, data):
        format_str = "<B"
        self.numLights = struct.unpack(format_str, data[0:struct.calcsize(format_str)])

    def __str__(self):
        return f"StartLights(numLights={self.numLights})"

class DriveThroughPenaltyServed:
    def __init__(self, data):
        format_str = "<B"
        self.vehicleIdx = struct.unpack(format_str, data[0:struct.calcsize(format_str)])

    def __str__(self):
        return f"DriveThroughPenaltyServed(vehicleIdx={self.vehicleIdx})"

class StopGoPenaltyServed:
    def __init__(self, data):
        format_str = "<B"
        self.vehicleIdx = struct.unpack(format_str, data[0:struct.calcsize(format_str)])

    def __str__(self):
        return f"StopGoPenaltyServed(vehicleIdx={self.vehicleIdx})"

class Flashback:
    def __init__(self, data):

        format_str = "<If"
        unpacked_data = struct.unpack(format_str, data[0:struct.calcsize(format_str)])
        (
            self.flashbackFrameIdentifier,
            self.flashbackSessionTime
        ) = unpacked_data

    def __str__(self):
        return f"Flashback(flashbackFrameIdentifier={self.flashbackFrameIdentifier}, " \
               f"flashbackSessionTime={self.flashbackSessionTime})"

class Buttons:
    def __init__(self, data):
        format_str = "<B"
        self.buttonStatus = struct.unpack(format_str, data[0:struct.calcsize(format_str)])

    def __str__(self):
        return f"Buttons(buttonStatus={self.buttonStatus})"

class Overtake:
    def __init__(self, data):
        format_str = "<BB"
        self.overtakingVehicleIdx, self.beingOvertakenVehicleIdx = struct.unpack(format_str,
            data[0:struct.calcsize(format_str)])

    def __str__(self):
        return f"Overtake(overtakingVehicleIdx={self.overtakingVehicleIdx}, " \
               f"beingOvertakenVehicleIdx={self.beingOvertakenVehicleIdx})"

class PacketEventData:

    event_type_map = {
        EventPacketType.SESSION_STARTED: None,
        EventPacketType.SESSION_ENDED: None,
        EventPacketType.FASTEST_LAP: FastestLap,
        EventPacketType.RETIREMENT: Retirement,
        EventPacketType.DRS_ENABLED: None,
        EventPacketType.DRS_DISABLED: None,
        EventPacketType.TEAM_MATE_IN_PITS: TeamMateInPits,
        EventPacketType.CHEQUERED_FLAG: None,
        EventPacketType.RACE_WINNER: RaceWinner,
        EventPacketType.PENALTY_ISSUED: Penalty,
        EventPacketType.SPEED_TRAP_TRIGGERED: SpeedTrap,
        EventPacketType.START_LIGHTS: StartLights,
        EventPacketType.LIGHTS_OUT: None,
        EventPacketType.DRIVE_THROUGH_SERVED: DriveThroughPenaltyServed,
        EventPacketType.STOP_GO_SERVED: StopGoPenaltyServed,
        EventPacketType.FLASHBACK: Flashback,
        EventPacketType.BUTTON_STATUS: Buttons,
        EventPacketType.RED_FLAG: None,
        EventPacketType.OVERTAKE: Overtake
    }

    def __init__(self, header, packet: bytes) -> None:
        self.m_header: PacketHeader = header       # PacketHeader
        self.m_eventStringCode: str = ""                         # char[4]

        self.m_eventStringCode = struct.unpack('4s', packet[0:4])[0].decode('ascii')
        if EventPacketType.isValid(self.m_eventStringCode):
            self.m_eventStringCode = EventPacketType(self.m_eventStringCode)
        else:
            raise TypeError("Unsupported Event Type " + self.m_eventStringCode)

        if PacketEventData.event_type_map.get(self.m_eventStringCode, None):
            self.mEventDetails = PacketEventData.event_type_map[self.m_eventStringCode](packet[4:])
        else:
            self.mEventDetails = None

    def __str__(self) -> str:
        event_str = (f"Event: {str(self.mEventDetails)}") if self.mEventDetails else ""
        return f"PacketEventData(Header: {str(self.m_header)}, Event String Code: {self.m_eventStringCode}, {event_str})"

# ------------------------- PACKET TYPE 4 - PARTICIPANTS -----------------------

class ParticipantData:
    """
    A class representing participant data in a racing simulation.

    Attributes:
        m_aiControlled (int): Whether the vehicle is AI (1) or Human (0) controlled.
        m_driverId (int): Driver id - see appendix, 255 if network human.
        networkId (int): Network id - unique identifier for network players.
        m_teamId (ParticipantData.TeamID): See TeamID enumeration
        m_myTeam (int): My team flag - 1 = My Team, 0 = otherwise.
        m_raceNumber (int): Race number of the car.
        m_nationality (int): Nationality of the driver.
        m_name (str): Name of participant in UTF-8 format - null terminated.
                      Will be truncated with … (U+2026) if too long.
        m_yourTelemetry (int): The player's UDP setting, 0 = restricted, 1 = public.
        m_showOnlineNames (int): The player's show online names setting, 0 = off, 1 = on.
        m_platform (ParticipantData.Platform): Gaming platform (see Platform enumeration).

        Note:
            The m_platform attribute is an instance of ParticipantData.Platform.
    """

    class TelemetrySetting(Enum):
        """
        Enumeration representing the telemetry setting for the player.

        Attributes:
            RESTRICTED (int): Telemetry setting is restricted (0).
            PUBLIC (int): Telemetry setting is public (1).
        """

        RESTRICTED = 0
        PUBLIC = 1

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the telemetry setting.

            Returns:
                str: String representation of the telemetry setting.
            """
            return {
                ParticipantData.TelemetrySetting.RESTRICTED: "Restricted",
                ParticipantData.TelemetrySetting.PUBLIC: "Public",
            }.get(self)

        @staticmethod
        def isValid(telemetry_setting_code: int) -> bool:
            """Check if the given telemetry setting code is valid.

            Args:
                driver_id (int): The telemetry setting code to be validated.

            Returns:
                bool: True if valid.
            """
            if isinstance(telemetry_setting_code, ParticipantData.TelemetrySetting):
                return True  # It's already an instance of TelemetrySetting
            else:
                min_value = min(member.value for member in ParticipantData.TelemetrySetting)
                max_value = max(member.value for member in ParticipantData.TelemetrySetting)
                return min_value <= telemetry_setting_code <= max_value

    class TeamID(Enum):
        MERCEDES = 0
        FERRARI = 1
        RED_BULL_RACING = 2
        WILLIAMS = 3
        ASTON_MARTIN = 4
        ALPINE = 5
        ALPHA_TAURI = 6
        HAAS = 7
        MCLAREN = 8
        ALFA_ROMEO = 9
        MERCEDES_2020 = 85
        FERRARI_2020 = 86
        RED_BULL_2020 = 87
        WILLIAMS_2020 = 88
        RACING_POINT_2020 = 89
        RENAULT_2020 = 90
        ALPHA_TAURI_2020 = 91
        HAAS_2020 = 92
        MCLAREN_2020 = 93
        ALFA_ROMEO_2020 = 94
        ASTON_MARTIN_DB11_V12 = 95
        ASTON_MARTIN_VANTAGE_F1_EDITION = 96
        ASTON_MARTIN_VANTAGE_SAFETY_CAR = 97
        FERRARI_F8_TRIBUTO = 98
        FERRARI_ROMA = 99
        MCLAREN_720S = 100
        MCLAREN_ARTURA = 101
        MERCEDES_AMG_GT_BLACK_SERIES_SAFETY_CAR = 102
        MERCEDES_AMG_GTR_PRO = 103
        F1_CUSTOM_TEAM = 104
        PREMA_21 = 106
        UNI_VIRTUOSI_21 = 107
        CARLIN_21 = 108
        HITECH_21 = 109
        ART_GP_21 = 110
        MP_MOTORSPORT_21 = 111
        CHAROUZ_21 = 112
        DAMS_21 = 113
        CAMPOS_21 = 114
        BWT_21 = 115
        TRIDENT_21 = 116
        MERCEDES_AMG_GT_BLACK_SERIES = 117
        MERCEDES_22 = 118
        FERRARI_22 = 119
        RED_BULL_RACING_22 = 120
        WILLIAMS_22 = 121
        ASTON_MARTIN_22 = 122
        ALPINE_22 = 123
        ALPHA_TAURI_22 = 124
        HAAS_22 = 125
        MCLAREN_22 = 126
        ALFA_ROMEO_22 = 127
        KONNERSPORT_22 = 128
        KONNERSPORT = 129
        PREMA_22 = 130
        VIRTUOSI_22 = 131
        CARLIN_22 = 132
        MP_MOTORSPORT_22 = 133
        CHAROUZ_22 = 134
        DAMS_22 = 135
        CAMPOS_22 = 136
        VAN_AMERSFOORT_RACING_22 = 137
        TRIDENT_22 = 138
        HITECH_22 = 139
        ART_GP_22 = 140

        @staticmethod
        def isValid(driver_id: int) -> bool:
            """Check if the given driver ID is valid.

            Args:
                driver_id (int): The driver ID to be validated.

            Returns:
                bool: True if valid.
            """
            if isinstance(driver_id, ParticipantData.TeamID):
                return True  # It's already an instance of TeamID
            else:
                min_value = min(member.value for member in ParticipantData.TeamID)
                max_value = max(member.value for member in ParticipantData.TeamID)
                return min_value <= driver_id <= max_value

        def __str__(self) -> str:
            """Return the string representation of the driver.

            Returns:
                str: String representation of the driver.
            """
            teams_mapping = {
                0: "Mercedes", 1: "Ferrari", 2: "Red Bull Racing",
                3: "Williams", 4: "Aston Martin", 5: "Alpine",
                6: "Alpha Tauri", 7: "Haas", 8: "McLaren",
                9: "Alfa Romeo", 85: "Mercedes 2020", 86: "Ferrari 2020",
                87: "Red Bull 2020", 88: "Williams 2020", 89: "Racing Point 2020",
                90: "Renault 2020", 91: "Alpha Tauri 2020", 92: "Haas 2020",
                93: "McLaren 2020", 94: "Alfa Romeo 2020", 95: "Aston Martin DB11 V12",
                96: "Aston Martin Vantage F1 Edition", 97: "Aston Martin Vantage Safety Car",
                98: "Ferrari F8 Tributo", 99: "Ferrari Roma", 100: "McLaren 720S",
                101: "McLaren Artura", 102: "Mercedes AMG GT Black Series Safety Car",
                103: "Mercedes AMG GTR Pro", 104: "F1 Custom Team",
                106: "Prema '21", 107: "Uni-Virtuosi '21", 108: "Carlin '21",
                109: "Hitech '21", 110: "Art GP '21", 111: "MP Motorsport '21",
                112: "Charouz '21", 113: "Dams '21", 114: "Campos '21",
                115: "BWT '21", 116: "Trident '21", 117: "Mercedes AMG GT Black Series",
                118: "Mercedes '22", 119: "Ferrari '22", 120: "Red Bull Racing '22",
                121: "Williams '22", 122: "Aston Martin '22", 123: "Alpine '22",
                124: "Alpha Tauri '22", 125: "Haas '22", 126: "McLaren '22",
                127: "Alfa Romeo '22", 128: "Konnersport '22", 129: "Konnersport",
                130: "Prema '22", 131: "Virtuosi '22", 132: "Carlin '22",
                133: "MP Motorsport '22", 134: "Charouz '22", 135: "Dams '22",
                136: "Campos '22", 137: "Van Amersfoort Racing '22", 138: "Trident '22",
                139: "Hitech '22", 140: "Art GP '22"
            }
            return teams_mapping.get(self.value, "---")

    class Platform(Enum):
        """
        Enumeration representing different gaming platforms.

        Attributes:
            STEAM (int): Steam platform.
            PLAYSTATION (int): PlayStation platform.
            XBOX (int): Xbox platform.
            ORIGIN (int): Origin platform.
            UNKNOWN (int): Unknown platform.

            Note:
                Each attribute represents a unique gaming platform identified by an integer value.
        """
        STEAM = 1
        PLAYSTATION = 3
        XBOX = 4
        ORIGIN = 6
        UNKNOWN = 255

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the gaming platform.

            Returns:
                str: String representation of the gaming platform.
            """
            return {
                ParticipantData.Platform.STEAM: "Steam",
                ParticipantData.Platform.PLAYSTATION: "PlayStation",
                ParticipantData.Platform.XBOX: "Xbox",
                ParticipantData.Platform.ORIGIN: "Origin",
                ParticipantData.Platform.UNKNOWN: "Unknown",
            }[self]

        @staticmethod
        def isValid(session_type_code: int):
            """Check if the given session type code is valid.

            Args:
                flag_type (int): The session type code to be validated.
                    Also supports type SessionType. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(session_type_code, ParticipantData.Platform):
                return True  # It's already an instance of SafetyCarStatus
            else:
                min_value = min(member.value for member in ParticipantData.Platform)
                max_value = max(member.value for member in ParticipantData.Platform)
                return min_value <= session_type_code <= max_value

    def __init__(self, data) -> None:
        """
        Initializes a ParticipantData object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        unpacked_data = struct.unpack(participant_format_string, data)
        (
            self.m_aiControlled,
            self.m_driverId,
            self.networkId,
            self.m_teamId,
            self.m_myTeam,
            self.m_raceNumber,
            self.m_nationality,
            self.m_name,
            self.m_yourTelemetry,
            self.m_showOnlineNames,
            self.m_platform
        ) = unpacked_data

        self.m_name = self.m_name.decode('utf-8').rstrip('\x00')
        if ParticipantData.Platform.isValid(self.m_platform):
            self.m_platform = ParticipantData.Platform(self.m_platform)
        if ParticipantData.TeamID.isValid(self.m_teamId):
            self.m_teamId = ParticipantData.TeamID(self.m_teamId)
        if ParticipantData.TelemetrySetting.isValid(self.m_yourTelemetry):
            self.m_yourTelemetry = ParticipantData.TelemetrySetting(self.m_yourTelemetry)

    def __str__(self):
        """
        Returns a string representation of the ParticipantData object.

        Returns:
            str: String representation of the object.
        """
        return (
            f"ParticipantData("
            f"m_aiControlled={self.m_aiControlled}, "
            f"m_driverId={self.m_driverId}, "
            f"networkId={self.networkId}, "
            f"m_teamId={self.m_teamId}, "
            f"m_myTeam={self.m_myTeam}, "
            f"m_raceNumber={self.m_raceNumber}, "
            f"m_nationality={self.m_nationality}, "
            f"m_name={self.m_name}, "
            f"m_yourTelemetry={self.m_yourTelemetry}, "
            f"m_showOnlineNames={self.m_showOnlineNames}, "
            f"m_platform={self.m_platform})"
        )

class PacketParticipantsData:
    """
    A class representing participant data in a racing simulation.

    Attributes:
        max_participants (int): Maximum number of participants (cars) in the packet.
        m_header (PacketHeader): Header containing general information about the packet.
        m_numActiveCars (int): Number of active cars in the data – should match the number of cars on HUD.
        m_participants (List[ParticipantData]): List of ParticipantData objects representing information
            about each participant in the race.

            Note:
                The length of m_participants should not exceed max_participants.
    """

    max_participants = 22
    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """
        Initializes a PacketParticipantsData object by unpacking the provided binary data.

        Parameters:
            header (PacketHeader): Header containing general information about the packet.
            packet (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        self.m_header: PacketHeader = header         # PacketHeader
        self.m_numActiveCars: int = struct.unpack("<B", packet[0:1])[0]
        self.m_participants: List[ParticipantData] = []            # ParticipantData[22]

        for participant_data_raw in _split_list(packet[1:], F1_23_PER_PARTICIPANT_INFO_LEN):
            self.m_participants.append(ParticipantData(participant_data_raw))

    def __str__(self) -> str:
        """
        Returns a string representation of the PacketParticipantsData object.

        Returns:
            str: String representation of the object.
        """
        participants_str = ", ".join(str(participant) for participant in self.m_participants[self.m_numActiveCars:])
        return (
            f"PacketParticipantsData("
            f"Header: {str(self.m_header)}, "
            f"Number of Active Cars: {self.m_numActiveCars}, "
            f"Participants: [{participants_str}])"
        )

# ------------------------- PACKET TYPE 5 - CAR SETUP --------------------------

class PacketCarSetupData:
    """
    A class representing the setup data for all cars in a racing simulation.

    Attributes:
        m_header (PacketHeader): Header containing general information about the packet.
        m_carSetups (List[CarSetupData]): List of CarSetupData objects representing the setup information
            for each car in the race.

            Note:
                The length of m_carSetups should not exceed the maximum number of participants.
    """

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """
        Initializes a PacketCarSetupData object by unpacking the provided binary data.

        Parameters:
            header (PacketHeader): Header containing general information about the packet.
            packet (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        self.m_header: PacketHeader = header
        self.m_carSetups: List[CarSetupData] = []

        for setup_per_car_raw_data in _split_list(packet, F1_23_CAR_SETUPS_LEN):
            self.m_carSetups.append(CarSetupData(setup_per_car_raw_data))

    def __str__(self) -> str:
        """
        Returns a string representation of the PacketCarSetupData object.

        Returns:
            str: String representation of the object.
        """
        setups_str = ", ".join(str(setup) for setup in self.m_carSetups)
        return f"PacketCarSetupData(Header: {str(self.m_header)}, Car Setups: [{setups_str}])"

class CarSetupData:
    """
    A class representing the setup data for a car in a racing simulation.

    Attributes:
        m_frontWing (int): Front wing aero.
        m_rearWing (int): Rear wing aero.
        m_onThrottle (int): Differential adjustment on throttle (percentage).
        m_offThrottle (int): Differential adjustment off throttle (percentage).
        m_frontCamber (float): Front camber angle (suspension geometry).
        m_rearCamber (float): Rear camber angle (suspension geometry).
        m_frontToe (float): Front toe angle (suspension geometry).
        m_rearToe (float): Rear toe angle (suspension geometry).
        m_frontSuspension (int): Front suspension.
        m_rearSuspension (int): Rear suspension.
        m_frontAntiRollBar (int): Front anti-roll bar.
        m_rearAntiRollBar (int): Rear anti-roll bar.
        m_frontSuspensionHeight (int): Front ride height.
        m_rearSuspensionHeight (int): Rear ride height.
        m_brakePressure (int): Brake pressure (percentage).
        m_brakeBias (int): Brake bias (percentage).
        m_rearLeftTyrePressure (float): Rear left tyre pressure (PSI).
        m_rearRightTyrePressure (float): Rear right tyre pressure (PSI).
        m_frontLeftTyrePressure (float): Front left tyre pressure (PSI).
        m_frontRightTyrePressure (float): Front right tyre pressure (PSI).
        m_ballast (int): Ballast.
        m_fuelLoad (float): Fuel load.
    """

    def __init__(self, data: bytes) -> None:
        """
        Initializes a CarSetupData object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        unpacked_data = struct.unpack(car_setups_format_string, data)

        (
            self.m_frontWing,
            self.m_rearWing,
            self.m_onThrottle,
            self.m_offThrottle,
            self.m_frontCamber,
            self.m_rearCamber,
            self.m_frontToe,
            self.m_rearToe,
            self.m_frontSuspension,
            self.m_rearSuspension,
            self.m_frontAntiRollBar,
            self.m_rearAntiRollBar,
            self.m_frontSuspensionHeight,
            self.m_rearSuspensionHeight,
            self.m_brakePressure,
            self.m_brakeBias,
            self.m_rearLeftTyrePressure,
            self.m_rearRightTyrePressure,
            self.m_frontLeftTyrePressure,
            self.m_frontRightTyrePressure,
            self.m_ballast,
            self.m_fuelLoad,
        ) = unpacked_data

    def __str__(self) -> str:
        """
        Returns a string representation of the CarSetupData object.

        Returns:
            str: String representation of the object.
        """
        return (
            f"CarSetupData(\n"
            f"  Front Wing: {self.m_frontWing}\n"
            f"  Rear Wing: {self.m_rearWing}\n"
            f"  On Throttle: {self.m_onThrottle}\n"
            f"  Off Throttle: {self.m_offThrottle}\n"
            f"  Front Camber: {self.m_frontCamber}\n"
            f"  Rear Camber: {self.m_rearCamber}\n"
            f"  Front Toe: {self.m_frontToe}\n"
            f"  Rear Toe: {self.m_rearToe}\n"
            f"  Front Suspension: {self.m_frontSuspension}\n"
            f"  Rear Suspension: {self.m_rearSuspension}\n"
            f"  Front Anti-Roll Bar: {self.m_frontAntiRollBar}\n"
            f"  Rear Anti-Roll Bar: {self.m_rearAntiRollBar}\n"
            f"  Front Suspension Height: {self.m_frontSuspensionHeight}\n"
            f"  Rear Suspension Height: {self.m_rearSuspensionHeight}\n"
            f"  Brake Pressure: {self.m_brakePressure}\n"
            f"  Brake Bias: {self.m_brakeBias}\n"
            f"  Rear Left Tyre Pressure: {self.m_rearLeftTyrePressure}\n"
            f"  Rear Right Tyre Pressure: {self.m_rearRightTyrePressure}\n"
            f"  Front Left Tyre Pressure: {self.m_frontLeftTyrePressure}\n"
            f"  Front Right Tyre Pressure: {self.m_frontRightTyrePressure}\n"
            f"  Ballast: {self.m_ballast}\n"
            f"  Fuel Load: {self.m_fuelLoad}\n"
            f")"
        )

# ------------------------- PACKET TYPE 6 - CAR TELEMETRY-----------------------

class PacketCarTelemetryData:
    """
    A class representing telemetry data for multiple cars in a racing simulation.

    Attributes:
        m_header (PacketHeader): Header information for the telemetry data.
        m_carTelemetryData (List[CarTelemetryData]): List of CarTelemetryData objects for each car.
        m_mfdPanelIndex (int): Index of MFD (Multi-Function Display) panel open.
            - 255: MFD closed (Single player, race)
            - 0: Car setup
            - 1: Pits
            - 2: Damage
            - 3: Engine
            - 4: Temperatures
            May vary depending on the game mode.
        m_mfdPanelIndexSecondaryPlayer (int): Secondary player's MFD panel index. See m_mfdPanelIndex for details.
        m_suggestedGear (int): Suggested gear for the player (1-8), 0 if no gear is suggested.
    """

    max_telemetry_entries = 22
    def __init__(self, header:PacketHeader, packet: bytes) -> None:
        """
        Initializes a PacketCarTelemetryData object by unpacking the provided binary data.

        Parameters:
            header (PacketHeader): Header information for the telemetry data.
            packet (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """

        self.m_header: PacketHeader = header
        self.m_carTelemetryData: List[CarTelemetryData] = []         # CarTelemetryData[22]
        len_all_car_telemetry = PacketCarTelemetryData.max_telemetry_entries * F1_23_CAR_TELEMETRY_LEN

        for per_car_telemetry_raw_data in _split_list(packet[:len_all_car_telemetry], F1_23_CAR_TELEMETRY_LEN):
            self.m_carTelemetryData.append(CarTelemetryData(per_car_telemetry_raw_data))

        self.mfdPanelIndex, self.m_mfdPanelIndexSecondaryPlayer, self.m_suggestedGear = \
            struct.unpack("<BBb", packet[len_all_car_telemetry:])

    def __str__(self) -> str:
        """
        Returns a string representation of the PacketCarTelemetryData object.

        Returns:
            str: String representation of the object.
        """
        telemetry_data_str = ", ".join(str(telemetry) for telemetry in self.m_carTelemetryData)
        mfdPanelIndex_to_string = lambda value: {
            255: "MFD closed Single player, race",
            0: "Car setup",
            1: "Pits",
            2: "Damage",
            3: "Engine",
            4: "Temperatures",
        }.get(value, f"Unknown state: {value}")
        return (
            f"PacketCarTelemetryData("
            f"Header: {str(self.m_header)}, "
            f"Car Telemetry Data: [{telemetry_data_str}], "
            f"MFD Panel Index: {mfdPanelIndex_to_string(self.mfdPanelIndex)}), "
            f"MFD Panel Index Secondary: {mfdPanelIndex_to_string(self.mfdPanelIndex)}), "
            f"Suggested Gear: {self.m_suggestedGear}"
        )

class CarTelemetryData:
    """
    A class representing telemetry data for a single car in a racing simulation.

    Attributes:
        m_speed (int): Speed of the car in kilometers per hour.
        m_throttle (float): Amount of throttle applied (0.0 to 1.0).
        m_steer (float): Steering value (-1.0 (full lock left) to 1.0 (full lock right)).
        m_brake (float): Amount of brake applied (0.0 to 1.0).
        m_clutch (int): Amount of clutch applied (0 to 100).
        m_gear (int): Gear selected (1-8, N=0, R=-1).
        m_engineRPM (int): Engine RPM.
        m_drs (int): DRS (Drag Reduction System) state (0 = off, 1 = on).
        m_revLightsPercent (int): Rev lights indicator (percentage).
        m_revLightsBitValue (int): Rev lights represented as a bitfield.
        m_brakesTemperature (List[int]): List of brake temperatures (celsius) for each wheel.
        m_tyresSurfaceTemperature (List[int]): List of surface temperatures (celsius) for each tyre.
        m_tyresInnerTemperature (List[int]): List of inner temperatures (celsius) for each tyre.
        m_engineTemperature (int): Engine temperature (celsius).
        m_tyresPressure (List[float]): List of tyre pressures (PSI) for each tyre.
        m_surfaceType (List[int]): List of surface types for each wheel, see appendices.

            Note:
                The length of each list attribute should be 4, corresponding to the four wheels of the car.
    """

    def __init__(self, data) -> None:
        """
        Initializes a CarTelemetryData object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        unpacked_data = struct.unpack(car_telemetry_format_string, data)

        (
            self.m_speed,
            self.m_throttle,
            self.m_steer,
            self.m_brake,
            self.m_clutch,
            self.m_gear,
            self.m_engineRPM,
            self.m_drs,
            self.m_revLightsPercent,
            self.m_revLightsBitValue,
            brake_temp1,
            brake_temp2,
            brake_temp3,
            brake_temp4,
            tyre_surface_temp1,
            tyre_surface_temp2,
            tyre_surface_temp3,
            tyre_surface_temp4,
            tyre_inner_temp1,
            tyre_inner_temp2,
            tyre_inner_temp3,
            tyre_inner_temp4,
            self.m_engineTemperature,
            tyre_pressure_1,
            tyre_pressure_2,
            tyre_pressure_3,
            tyre_pressure_4,
            surface_type_1,
            surface_type_2,
            surface_type_3,
            surface_type_4,
        ) = unpacked_data

        self.m_brakesTemperature = [brake_temp1, brake_temp2, brake_temp3, brake_temp4]
        self.m_tyresSurfaceTemperature = [tyre_surface_temp1, tyre_surface_temp2, tyre_surface_temp3, tyre_surface_temp4]
        self.m_tyresInnerTemperature = [tyre_inner_temp1, tyre_inner_temp2, tyre_inner_temp3, tyre_inner_temp4]
        self.m_tyresPressure = [tyre_pressure_1, tyre_pressure_2, tyre_pressure_3, tyre_pressure_4]
        self.m_surfaceType = [surface_type_1, surface_type_2, surface_type_3, surface_type_4]

    def __str__(self) -> str:
        """
        Returns a string representation of the CarTelemetryData object.

        Returns:
            str: String representation of the object.
        """
        return (
            f"CarTelemetryData("
            f"Speed: {self.m_speed}, "
            f"Throttle: {self.m_throttle}, "
            f"Steer: {self.m_steer}, "
            f"Brake: {self.m_brake}, "
            f"Clutch: {self.m_clutch}, "
            f"Gear: {self.m_gear}, "
            f"Engine RPM: {self.m_engineRPM}, "
            f"DRS: {self.m_drs}, "
            f"Rev Lights Percent: {self.m_revLightsPercent}, "
            f"Brakes Temperature: {str(self.m_brakesTemperature)}, "
            f"Tyres Surface Temperature: {str(self.m_tyresSurfaceTemperature)}, "
            f"Tyres Inner Temperature: {str(self.m_tyresInnerTemperature)}, "
            f"Engine Temperature: {str(self.m_engineTemperature)}, "
            f"Tyres Pressure: {str(self.m_tyresPressure)})"
        )

# ------------------------- PACKET TYPE 7 - CAR STATUS -------------------------

class PacketCarStatusData:
    """
    Class containing details on car statuses for all the cars in the race.

    Attributes:
        - m_header(PacketHeader) - packet header info
        - m_carStatusData(List[CarStatusData]) - List of statuses of every car
    """

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """Initialise the object from the raw bytes list

        Args:
            header (PacketHeader): Object containing header info
            packet (bytes): List of bytes representing the packet payload
        """
        self.m_header: PacketHeader = header
        self.m_carStatusData: List[CarStatusData] = []               # CarStatusData[22]

        for status_per_car_raw_data in _split_list(packet, F1_23_CAR_STATUS_LEN):
            self.m_carStatusData.append(CarStatusData(status_per_car_raw_data))

    def __str__(self) -> str:
        """Generate a human readable string of this object's contents

        Returns:
            str: Printable/Loggable string
        """
        status_data_str = ", ".join(str(status) for status in self.m_carStatusData)
        return f"PacketCarStatusData(Header: {str(self.m_header)}, Car Status Data: [{status_data_str}])"

class CarStatusData:
    """
    Class representing car status data.

    Attributes:
        - m_tractionControl (uint8): Traction control - 0 = off, 1 = medium, 2 = full
        - m_antiLockBrakes (uint8): Anti-lock brakes - 0 (off) - 1 (on)
        - m_fuelMix (uint8): Fuel mix - 0 = lean, 1 = standard, 2 = rich, 3 = max
        - m_frontBrakeBias (uint8): Front brake bias (percentage)
        - m_pitLimiterStatus (uint8): Pit limiter status - 0 = off, 1 = on
        - m_fuelInTank (float): Current fuel mass
        - m_fuelCapacity (float): Fuel capacity
        - m_fuelRemainingLaps (float): Fuel remaining in terms of laps (value on MFD)
        - m_maxRPM (uint16): Cars max RPM, point of rev limiter
        - m_idleRPM (uint16): Cars idle RPM
        - m_maxGears (uint8): Maximum number of gears
        - m_drsAllowed (uint8): DRS allowed - 0 = not allowed, 1 = allowed
        - m_drsActivationDistance (uint16): DRS activation distance -
                                          0 = DRS not available, non-zero - DRS will be available in [X] metres
        - m_actualTyreCompound (ActualTyreCompound): Actual tyre compound (enum)
        - m_visualTyreCompound (VisualTyreCompound): Visual tyre compound (enum)
        - m_tyresAgeLaps (uint8): Age in laps of the current set of tyres
        - m_vehicleFiaFlags (VehicleFIAFlags): Vehicle FIA flags (enum)
        - m_enginePowerICE (float): Engine power output of ICE (W)
        - m_enginePowerMGUK (float): Engine power output of MGU-K (W)
        - m_ersStoreEnergy (float): ERS energy store in Joules
        - m_ersDeployMode (ERSDeployMode): ERS deployment mode (enum)
        - m_ersHarvestedThisLapMGUK (float): ERS energy harvested this lap by MGU-K
        - m_ersHarvestedThisLapMGUH (float): ERS energy harvested this lap by MGU-H
        - m_ersDeployedThisLap (float): ERS energy deployed this lap
        - m_networkPaused (uint8): Whether the car is paused in a network game

    Note:
        The class uses enum classes for certain attributes for better readability and type safety.
    """

    class ActualTyreCompound(Enum):
        """
        Enumeration representing different tyre compounds used in Formula 1 and Formula 2.

        Attributes:
            C5 (int): F1 Modern - C5
            C4 (int): F1 Modern - C4
            C3 (int): F1 Modern - C3
            C2 (int): F1 Modern - C2
            C1 (int): F1 Modern - C1
            C0 (int): F1 Modern - C0
            INTER (int): F1 Modern - Intermediate
            WET (int): F1 Modern - Wet
            DRY (int): F1 Classic - Dry
            WET_CLASSIC (int): F1 Classic - Wet
            SUPER_SOFT (int): F2 - Super Soft
            SOFT (int): F2 - Soft
            MEDIUM (int): F2 - Medium
            HARD (int): F2 - Hard
            WET_F2 (int): F2 - Wet

            Note:
                Each attribute represents a unique tyre compound identified by an integer value.
        """

        C5 = 16
        C4 = 17
        C3 = 18
        C2 = 19
        C1 = 20
        C0 = 21
        INTER = 7
        WET = 8
        DRY = 9
        WET_CLASSIC = 10
        SUPER_SOFT = 11
        SOFT = 12
        MEDIUM = 13
        HARD = 14
        WET_F2 = 15

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the tyre compound.

            Returns:
                str: String representation of the tyre compound.
            """
            return {
                CarStatusData.ActualTyreCompound.C5: "C5",
                CarStatusData.ActualTyreCompound.C4: "C4",
                CarStatusData.ActualTyreCompound.C3: "C3",
                CarStatusData.ActualTyreCompound.C2: "C2",
                CarStatusData.ActualTyreCompound.C1: "C1",
                CarStatusData.ActualTyreCompound.C0: "C0",
                CarStatusData.ActualTyreCompound.INTER: "Inters",
                CarStatusData.ActualTyreCompound.WET: "Wet",
                CarStatusData.ActualTyreCompound.DRY: "Dry",
                CarStatusData.ActualTyreCompound.WET_CLASSIC: "Wet (Classic)",
                CarStatusData.ActualTyreCompound.SUPER_SOFT: "Super Soft",
                CarStatusData.ActualTyreCompound.SOFT: "Soft",
                CarStatusData.ActualTyreCompound.MEDIUM: "Medium",
                CarStatusData.ActualTyreCompound.HARD: "Hard",
                CarStatusData.ActualTyreCompound.WET_F2: "Wet (F2)",
            }[self]

        @staticmethod
        def isValid(actual_tyre_compound: int) -> bool:
            """
            Check if the input event type string maps to a valid enum value.

            Args:
                event_type (int): The actual tyre compound code

            Returns:
                bool: True if the event type is valid, False otherwise.
            """
            if isinstance(actual_tyre_compound, CarStatusData.ActualTyreCompound):
                return True  # It's already an instance of CarStatusData.ActualTyreCompound
            else:
                # check if the integer value falls in range
                min_value = min(member.value for member in CarStatusData.ActualTyreCompound)
                max_value = max(member.value for member in CarStatusData.ActualTyreCompound)
                return min_value <= actual_tyre_compound <= max_value

    class VisualTyreCompound(Enum):
        """
        Enumeration representing different visual tyre compounds used in Formula 1 and Formula 2.

        Attributes:
            SOFT (int): Soft tyre compound
            MEDIUM (int): Medium tyre compound
            HARD (int): Hard tyre compound
            INTER (int): Intermediate tyre compound
            WET (int): Wet tyre compound
            WET_CLASSIC (int): Wet tyre compound (Classic)
            SUPER_SOFT (int): Super Soft tyre compound (F2 '19)
            SOFT_F2 (int): Soft tyre compound (F2 '19)
            MEDIUM_F2 (int): Medium tyre compound (F2 '19)
            HARD_F2 (int): Hard tyre compound (F2 '19)
            WET_F2 (int): Wet tyre compound (F2 '19)

            Note:
                Each attribute represents a unique visual tyre compound identified by an integer value.
        """

        SOFT = 16
        MEDIUM = 17
        HARD = 18
        INTER = 7
        WET = 8
        WET_CLASSIC = 8  # Same value as WET for F1 visual (Classic)
        SUPER_SOFT = 19
        SOFT_F2 = 20
        MEDIUM_F2 = 21
        HARD_F2 = 22
        WET_F2 = 15

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the visual tyre compound.

            Returns:
                str: String representation of the visual tyre compound.
            """
            return {
                CarStatusData.VisualTyreCompound.SOFT: "Soft",
                CarStatusData.VisualTyreCompound.MEDIUM: "Medium",
                CarStatusData.VisualTyreCompound.HARD: "Hard",
                CarStatusData.VisualTyreCompound.INTER: "Inters",
                CarStatusData.VisualTyreCompound.WET: "Wet",
                # CarStatusData.VisualTyreCompound.WET_CLASSIC: "Wet (Classic)",
                CarStatusData.VisualTyreCompound.WET_CLASSIC: "Wet",
                CarStatusData.VisualTyreCompound.SUPER_SOFT: "Super Soft (F2 '19)",
                CarStatusData.VisualTyreCompound.SOFT_F2: "Soft (F2 '19)",
                CarStatusData.VisualTyreCompound.MEDIUM_F2: "Medium (F2 '19)",
                CarStatusData.VisualTyreCompound.HARD_F2: "Hard (F2 '19)",
                CarStatusData.VisualTyreCompound.WET_F2: "Wet (F2 '19)",
            }[self]

        @staticmethod
        def isValid(visual_tyre_compound: int) -> bool:
            """
            Check if the input event type string maps to a valid enum value.

            Args:
                event_type (int): The actual tyre compound code

            Returns:
                bool: True if the event type is valid, False otherwise.
            """
            if isinstance(visual_tyre_compound, CarStatusData.VisualTyreCompound):
                return True  # It's already an instance of CarStatusData.VisualTyreCompound
            else:
                # check if the integer value falls in range
                min_value = min(member.value for member in CarStatusData.VisualTyreCompound)
                max_value = max(member.value for member in CarStatusData.VisualTyreCompound)
                return min_value <= visual_tyre_compound <= max_value

    class VehicleFIAFlags(Enum):
        """
        Enumeration representing different FIA flags related to vehicles.

        Attributes:
            INVALID_UNKNOWN (int): Invalid or unknown FIA flag (-1)
            NONE (int): No FIA flag (0)
            GREEN (int): Green flag (1)
            BLUE (int): Blue flag (2)
            YELLOW (int): Yellow flag (3)

            Note:
                Each attribute represents a unique FIA flag identified by an integer value.
        """

        INVALID_UNKNOWN = -1
        NONE = 0
        GREEN = 1
        BLUE = 2
        YELLOW = 3

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the FIA flag.

            Returns:
                str: String representation of the FIA flag.
            """
            return {
                CarStatusData.VehicleFIAFlags.INVALID_UNKNOWN: "Invalid/Unknown",
                CarStatusData.VehicleFIAFlags.NONE: "None",
                CarStatusData.VehicleFIAFlags.GREEN: "Green",
                CarStatusData.VehicleFIAFlags.BLUE: "Blue",
                CarStatusData.VehicleFIAFlags.YELLOW: "Yellow",
            }[self]

        @staticmethod
        def isValid(fia_flag_code: int) -> bool:
            """
            Check if the input flag code maps to a valid enum value.

            Args:
                fia_flag_code (int): The actual FIA flag status code

            Returns:
                bool: True if the event type is valid, False otherwise.
            """
            if isinstance(fia_flag_code, CarStatusData.VehicleFIAFlags):
                return True  # It's already an instance of CarStatusData.VehicleFIAFlags
            else:
                # check if the integer value falls in range
                min_value = min(member.value for member in CarStatusData.VehicleFIAFlags)
                max_value = max(member.value for member in CarStatusData.VehicleFIAFlags)
                return min_value <= fia_flag_code <= max_value

    class ERSDeployMode(Enum):
        """
        Enumeration representing different ERS deployment modes.

        Attributes:
            NONE (int): No ERS deployment (0)
            MEDIUM (int): Medium ERS deployment (1)
            HOPLAP (int): Hotlap ERS deployment (2)
            OVERTAKE (int): Overtake ERS deployment (3)

            Note:
                Each attribute represents a unique ERS deployment mode identified by an integer value.
        """

        NONE = 0
        MEDIUM = 1
        HOPLAP = 2
        OVERTAKE = 3

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the ERS deployment mode.

            Returns:
                str: String representation of the ERS deployment mode.
            """
            return {
                CarStatusData.ERSDeployMode.NONE: "None",
                CarStatusData.ERSDeployMode.MEDIUM: "Medium",
                CarStatusData.ERSDeployMode.HOPLAP: "Hotlap",
                CarStatusData.ERSDeployMode.OVERTAKE: "Overtake",
            }[self]

        @staticmethod
        def isValid(ers_deploy_mode_code: int) -> bool:
            """
            Check if the ERS deploy mode code maps to a valid enum value.

            Args:
                event_type (int): The ERS deploy mode code

            Returns:
                bool: True if the event type is valid, False otherwise.
            """
            if isinstance(ers_deploy_mode_code, CarStatusData.ERSDeployMode):
                return True  # It's already an instance of CarStatusData.ERSDeployMode
            else:
                # check if the integer value falls in range
                min_value = min(member.value for member in CarStatusData.ERSDeployMode)
                max_value = max(member.value for member in CarStatusData.ERSDeployMode)
                return min_value <= ers_deploy_mode_code <= max_value

    max_ers_store_energy = 4000000.0 # Figured out through trial and error
    def __init__(self, data) -> None:
        """
        Initializes CarStatusData with raw data.

        Args:
            data (bytes): Raw data representing car status.
        """
        (
            self.m_tractionControl,
            self.m_antiLockBrakes,
            self.m_fuelMix,
            self.m_frontBrakeBias,
            self.m_pitLimiterStatus,
            self.m_fuelInTank,
            self.m_fuelCapacity,
            self.m_fuelRemainingLaps,
            self.m_maxRPM,
            self.m_idleRPM,
            self.m_maxGears,
            self.m_drsAllowed,
            self.m_drsActivationDistance,
            self.m_actualTyreCompound,
            self.m_visualTyreCompound,
            self.m_tyresAgeLaps,
            self. m_vehicleFiaFlags,
            self.m_enginePowerICE,
            self.m_enginePowerMGUK,
            self.m_ersStoreEnergy,
            self.m_ersDeployMode,
            self.m_ersHarvestedThisLapMGUK,
            self.m_ersHarvestedThisLapMGUH,
            self.m_ersDeployedThisLap,
            self.m_networkPaused
        ) = struct.unpack(car_status_format_string, data)

        if CarStatusData.ActualTyreCompound.isValid(self.m_actualTyreCompound):
            self.m_actualTyreCompound = CarStatusData.ActualTyreCompound(self.m_actualTyreCompound)
        if CarStatusData.VisualTyreCompound.isValid(self.m_visualTyreCompound):
            self.m_visualTyreCompound = CarStatusData.VisualTyreCompound(self.m_visualTyreCompound)
        if CarStatusData.VehicleFIAFlags.isValid(self.m_vehicleFiaFlags):
            self.m_vehicleFiaFlags = CarStatusData.VehicleFIAFlags(self.m_vehicleFiaFlags)
        if CarStatusData.ERSDeployMode.isValid(self.m_ersDeployMode):
            self.m_ersDeployMode = CarStatusData.ERSDeployMode(self.m_ersDeployMode)

    def __str__(self):
        """
        Returns a string representation of CarStatusData.

        Returns:
            str: String representation of CarStatusData.
        """
        return (
            f"CarStatusData("
            f"m_tractionControl={self.m_tractionControl}, "
            f"m_antiLockBrakes={self.m_antiLockBrakes}, "
            f"m_fuelMix={self.m_fuelMix}, "
            f"m_frontBrakeBias={self.m_frontBrakeBias}, "
            f"m_pitLimiterStatus={self.m_pitLimiterStatus}, "
            f"m_fuelInTank={self.m_fuelInTank}, "
            f"m_fuelCapacity={self.m_fuelCapacity}, "
            f"m_fuelRemainingLaps={self.m_fuelRemainingLaps}, "
            f"m_maxRPM={self.m_maxRPM}, "
            f"m_idleRPM={self.m_idleRPM}, "
            f"m_maxGears={self.m_maxGears}, "
            f"m_drsAllowed={self.m_drsAllowed}, "
            f"m_drsActivationDistance={self.m_drsActivationDistance}, "
            f"m_actualTyreCompound={self.m_actualTyreCompound}, "
            f"m_visualTyreCompound={self.m_visualTyreCompound}, "
            f"m_tyresAgeLaps={self.m_tyresAgeLaps}, "
            f"m_vehicleFiaFlags={self.m_vehicleFiaFlags}, "
            f"m_enginePowerICE={self.m_enginePowerICE}, "
            f"m_enginePowerMGUK={self.m_enginePowerMGUK}, "
            f"m_ersStoreEnergy={self.m_ersStoreEnergy}, "
            f"m_ersDeployMode={self.m_ersDeployMode}, "
            f"m_ersHarvestedThisLapMGUK={self.m_ersHarvestedThisLapMGUK}, "
            f"m_ersHarvestedThisLapMGUH={self.m_ersHarvestedThisLapMGUH}, "
            f"m_ersDeployedThisLap={self.m_ersDeployedThisLap}, "
            f"m_networkPaused={self.m_networkPaused})"
        )

# ------------------------- PACKET TYPE 8 - FINAL CLASSIFICATION ---------------

class PacketFinalClassificationData:
    """
    Class representing the packet for final classification data.

    Attributes:
        m_header (PacketHeader): Header information.
        m_numCars (int): Number of cars in the final classification.
        m_classificationData (List[FinalClassificationData]): List of final classification data for each car.

    Note:
        The class is designed to parse and represent the final classification data packet.
    """

    max_cars = 22

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """
        Initializes PacketFinalClassificationData with raw data.

        Args:
            header (PacketHeader): Header information for the packet.
            packet (bytes): Raw data representing the packet for final classification data.
        """
        self.m_header: PacketHeader = header
        self.m_numCars: int = struct.unpack("<B", packet[0:1])[0]
        self.m_classificationData: List[FinalClassificationData] = []

        for classification_per_car_raw_data in _split_list(packet[1:], F1_23_FINAL_CLASSIFICATION_PER_CAR_LEN):
            self.m_classificationData.append(FinalClassificationData(classification_per_car_raw_data))

    def __str__(self) -> str:
        """
        Returns a string representation of PacketFinalClassificationData.

        Returns:
            str: String representation of PacketFinalClassificationData.
        """
        classification_data_str = ", ".join(str(data) for data in self.m_classificationData[:self.m_numCars])
        return (
            f"PacketFinalClassificationData("
            f"Number of Cars: {self.m_numCars}, "
            f"Classification Data: [{classification_data_str}])"
        )

class FinalClassificationData:
    """
    Class representing final classification data for a car in a race.

    Attributes:
        m_position (uint8): Finishing position
        m_numLaps (uint8): Number of laps completed
        m_gridPosition (uint8): Grid position of the car
        m_points (uint8): Number of points scored
        m_numPitStops (uint8): Number of pit stops made
        m_resultStatus (ResultStatus): See ResultStatus enumeration for more info
        m_bestLapTimeInMS (uint32): Best lap time of the session in milliseconds
        m_totalRaceTime (double): Total race time in seconds without penalties
        m_penaltiesTime (uint8): Total penalties accumulated in seconds
        m_numPenalties (uint8): Number of penalties applied to this driver
        m_numTyreStints (uint8): Number of tyre stints up to maximum
        m_tyreStintsActual (List[uint8]): Actual tyres used by this driver (array of 8)
        m_tyreStintsVisual (List[uint8]): Visual tyres used by this driver (array of 8)
        m_tyreStintsEndLaps (List[uint8]): The lap number stints end on (array of 8)

    Note:
        The class is designed to parse and represent the final classification data for a car in a race.
    """
    def __init__(self, data) -> None:
        """
        Initializes FinalClassificationData with raw data.

        Args:
            data (bytes): Raw data representing final classification for a car in a race.
        """

        self.m_tyreStintsActual = [0] * 8
        self.m_tyreStintsVisual = [0] * 8
        self.m_tyreStintsEndLaps = [0] * 8
        (
            self.m_position,
            self.m_numLaps,
            self.m_gridPosition,
            self.m_points,
            self.m_numPitStops,
            self.m_resultStatus,
            self.m_bestLapTimeInMS,
            self.m_totalRaceTime,
            self.m_penaltiesTime,
            self.m_numPenalties,
            self.m_numTyreStints,
            # self.m_tyreStintsActual,  # array of 8
            self.m_tyreStintsActual[0],
            self.m_tyreStintsActual[1],
            self.m_tyreStintsActual[2],
            self.m_tyreStintsActual[3],
            self.m_tyreStintsActual[4],
            self.m_tyreStintsActual[5],
            self.m_tyreStintsActual[6],
            self.m_tyreStintsActual[7],
            # self.m_tyreStintsVisual,  # array of 8
            self.m_tyreStintsVisual[0],
            self.m_tyreStintsVisual[1],
            self.m_tyreStintsVisual[2],
            self.m_tyreStintsVisual[3],
            self.m_tyreStintsVisual[4],
            self.m_tyreStintsVisual[5],
            self.m_tyreStintsVisual[6],
            self.m_tyreStintsVisual[7],
            # self.m_tyreStintsEndLaps,  # array of 8
            self.m_tyreStintsEndLaps[0],
            self.m_tyreStintsEndLaps[1],
            self.m_tyreStintsEndLaps[2],
            self.m_tyreStintsEndLaps[3],
            self.m_tyreStintsEndLaps[4],
            self.m_tyreStintsEndLaps[5],
            self.m_tyreStintsEndLaps[6],
            self.m_tyreStintsEndLaps[7]
        ) = struct.unpack(final_classification_per_car_format_string, data)

        if ResultStatus.isValid(self.m_resultStatus):
            self.m_resultStatus = ResultStatus(self.m_resultStatus)

    def __str__(self):
        """
        Returns a string representation of FinalClassificationData.

        Returns:
            str: String representation of FinalClassificationData.
        """
        return (
            f"FinalClassificationData("
            f"m_position={self.m_position}, "
            f"m_numLaps={self.m_numLaps}, "
            f"m_gridPosition={self.m_gridPosition}, "
            f"m_points={self.m_points}, "
            f"m_numPitStops={self.m_numPitStops}, "
            f"m_resultStatus={self.m_resultStatus}, "
            f"m_bestLapTimeInMS={self.m_bestLapTimeInMS}, "
            f"m_totalRaceTime={self.m_totalRaceTime}, "
            f"m_penaltiesTime={self.m_penaltiesTime}, "
            f"m_numPenalties={self.m_numPenalties}, "
            f"m_numTyreStints={self.m_numTyreStints}, "
            f"m_tyreStintsActual={str(self.m_tyreStintsActual)}, "
            f"m_tyreStintsVisual={str(self.m_tyreStintsVisual)}, "
            f"m_tyreStintsEndLaps={str(self.m_tyreStintsEndLaps)})"
        )

# ------------------------- PACKET TYPE 9 - LOBBY INFO -------------------------

class PacketLobbyInfoData:
    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        self.m_header: PacketHeader = header
        self.m_numPlayers: int = struct.unpack("<B", packet[:1])[0]
        self.m_lobbyPlayers: List[LobbyInfoData] = []              # LobbyInfoData[22]

        for lobby_info_per_player_raw_data in _split_list(packet[1:], F1_23_LOBBY_INFO_PER_PLAYER_LEN):
            self.m_lobbyPlayers.append(LobbyInfoData(lobby_info_per_player_raw_data))


    def __str__(self) -> str:
        lobby_players_str = ", ".join(str(player) for player in self.m_lobbyPlayers[:self.m_numPlayers])
        return (
            f"PacketLobbyInfoData("
            f"Number of Players: {self.m_numPlayers}, "
            f"Lobby Players: [{lobby_players_str}])"
        )

class LobbyInfoData:
    def __init__(self, data ) -> None:

        (
            self.m_aiControlled,
            self.m_teamId,
            self.m_nationality,
            self.m_platform,
            self.m_name,
            self.m_carNumber,
            self.m_readyStatus,
        ) = struct.unpack(lobby_info_format_string, data)

    def __str__(self):
        return (
            f"LobbyInfoData("
            f"m_aiControlled={self.m_aiControlled}, "
            f"m_teamId={self.m_teamId}, "
            f"m_nationality={self.m_nationality}, "
            f"m_platform={self.m_platform}, "
            f"m_name={self.m_name}, "
            f"m_carNumber={self.m_carNumber}, "
            f"m_readyStatus={self.m_readyStatus})"
        )

# ------------------------- PACKET TYPE 10 - CAR DAMAGE ------------------------

class CarDamageData:
    """
    Class representing the packet for car damage data.

    Attributes:
        m_tyresWear (List[float]): List of tyre wear percentages for each tyre.
        m_tyresDamage (List[int]): List of tyre damage percentages for each tyre.
        m_brakesDamage (List[int]): List of brake damage percentages for each brake.
        m_frontLeftWingDamage (int): Front left wing damage percentage.
        m_frontRightWingDamage (int): Front right wing damage percentage.
        m_rearWingDamage (int): Rear wing damage percentage.
        m_floorDamage (int): Floor damage percentage.
        m_diffuserDamage (int): Diffuser damage percentage.
        m_sidepodDamage (int): Sidepod damage percentage.
        m_drsFault (bool): Indicator for DRS fault
        m_ersFault (bool): Indicator for ERS fault
        m_gearBoxDamage (int): Gearbox damage percentage.
        m_engineDamage (int): Engine damage percentage.
        m_engineMGUHWear (int): Engine wear MGU-H percentage.
        m_engineESWear (int): Engine wear ES percentage.
        m_engineCEWear (int): Engine wear CE percentage.
        m_engineICEWear (int): Engine wear ICE percentage.
        m_engineMGUKWear (int): Engine wear MGU-K percentage.
        m_engineTCWear (int): Engine wear TC percentage.
        m_engineBlown (bool): Engine blown, 0 = OK, 1 = fault.
        m_engineSeized (bool): Engine seized, 0 = OK, 1 = fault.

    Note:
        The class is designed to parse and represent the car damage data packet.
    """

    def __init__(self, data) -> None:
        """
        Initializes CarDamageData with raw data.

        Args:
            data (bytes): Raw data representing the packet for car damage data.
        """
        self.m_tyresWear = [0.0] * 4
        self.m_tyresDamage = [0] * 4
        self.m_brakesDamage = [0] * 4
        (
            self.m_tyresWear[0],
            self.m_tyresWear[1],
            self.m_tyresWear[2],
            self.m_tyresWear[3],
            self.m_tyresDamage[0],
            self.m_tyresDamage[1],
            self.m_tyresDamage[2],
            self.m_tyresDamage[3],
            self.m_brakesDamage[0],
            self.m_brakesDamage[1],
            self.m_brakesDamage[2],
            self.m_brakesDamage[3],
            self.m_frontLeftWingDamage,
            self.m_frontRightWingDamage,
            self.m_rearWingDamage,
            self.m_floorDamage,
            self.m_diffuserDamage,
            self.m_sidepodDamage,
            self.m_drsFault,
            self.m_ersFault,
            self.m_gearBoxDamage,
            self.m_engineDamage,
            self.m_engineMGUHWear,
            self.m_engineESWear,
            self.m_engineCEWear,
            self.m_engineICEWear,
            self.m_engineMGUKWear,
            self.m_engineTCWear,
            self.m_engineBlown,
            self.m_engineSeized,
        ) = struct.unpack(car_damage_packet_format_string, data)

        self.m_drsFault = bool(self.m_drsFault)
        self.m_ersFault = bool(self.m_ersFault)
        self.m_engineBlown = bool(self.m_engineBlown)
        self.m_engineSeized = bool(self.m_engineSeized)

    def __str__(self) -> str:
        """
        Returns a string representation of CarDamageData.

        Returns:
            str: String representation of CarDamageData.
        """
        return (
            f"Tyres Wear: {str(self.m_tyresWear)}, Tyres Damage: {str(self.m_tyresDamage)}, "
            f"Brakes Damage: {str(self.m_brakesDamage)}, Front Left Wing Damage: {self.m_frontLeftWingDamage}, "
            f"Front Right Wing Damage: {self.m_frontRightWingDamage}, Rear Wing Damage: {self.m_rearWingDamage}, "
            f"Floor Damage: {self.m_floorDamage}, Diffuser Damage: {self.m_diffuserDamage}, "
            f"Sidepod Damage: {self.m_sidepodDamage}, DRS Fault: {self.m_drsFault}, ERS Fault: {self.m_ersFault}, "
            f"Gear Box Damage: {self.m_gearBoxDamage}, Engine Damage: {self.m_engineDamage}, "
            f"Engine MGU-H Wear: {self.m_engineMGUHWear}, Engine ES Wear: {self.m_engineESWear}, "
            f"Engine CE Wear: {self.m_engineCEWear}, Engine ICE Wear: {self.m_engineICEWear}, "
            f"Engine MGU-K Wear: {self.m_engineMGUKWear}, Engine TC Wear: {self.m_engineTCWear}, "
            f"Engine Blown: {self.m_engineBlown}, Engine Seized: {self.m_engineSeized}"
        )

class PacketCarDamageData:
    """
    Class representing the packet for car damage data.

    Attributes:
        m_header (PacketHeader): The header of the packet.
        m_carDamageData (List[CarDamageData]): List of CarDamageData objects for each car.

    Note:
        The class is designed to parse and represent the car damage data packet.
    """

    def __init__(self, header: PacketHeader, data: bytes) -> None:
        """
        Initializes PacketCarDamageData with raw data.

        Args:
            header (PacketHeader): The header of the packet.
            data (bytes): Raw data representing the packet for car damage data.
        """
        self.m_header: PacketHeader = header
        self.m_carDamageData: List[CarDamageData] = []

        for raw_data_per_car in _split_list(data, F1_23_DAMAGE_PER_CAR_PACKET_LEN):
            self.m_carDamageData.append(CarDamageData(raw_data_per_car))

    def __str__(self) -> str:
        """
        Returns a string representation of PacketCarDamageData.

        Returns:
            str: String representation of PacketCarDamageData.
        """
        return f"Header: {str(self.m_header)}, Car Damage Data: {[str(car_data) for car_data in self.m_carDamageData]}"

# ------------------------- PACKET TYPE 11 - SESSION HISTORY -------------------

class LapHistoryData:
    """
    Class representing lap history data for a session.

    Attributes:
        m_lapTimeInMS (uint32): Lap time in milliseconds.
        m_sector1TimeInMS (uint16): Sector 1 time in milliseconds.
        m_sector1TimeMinutes (uint8): Sector 1 whole minute part.
        m_sector2TimeInMS (uint16): Sector 2 time in milliseconds.
        m_sector2TimeMinutes (uint8): Sector 2 whole minute part.
        m_sector3TimeInMS (uint16): Sector 3 time in milliseconds.
        m_sector3TimeMinutes (uint8): Sector 3 whole minute part.
        m_lapValidBitFlags (uint8): Bit flags representing lap and sector validity.

    Note:
        - The lapValidBitFlags use individual bits to indicate the validity of the lap and each sector.
        - 0x01 bit set: Lap valid
        - 0x02 bit set: Sector 1 valid
        - 0x04 bit set: Sector 2 valid
        - 0x08 bit set: Sector 3 valid
    """

    def __init__(self, data: bytes) -> None:
        """
        Initializes LapHistoryData with raw data.

        Args:
            data (bytes): Raw data representing lap history for a session.
        """
        (
            self.m_lapTimeInMS,
            self.m_sector1TimeInMS,
            self.m_sector1TimeMinutes,
            self.m_sector2TimeInMS,
            self.m_sector2TimeMinutes,
            self.m_sector3TimeInMS,
            self.m_sector3TimeMinutes,
            self.m_lapValidBitFlags,
        ) = struct.unpack(session_history_lap_history_data_format_string, data)

    def __str__(self) -> str:
        """
        Returns a string representation of LapHistoryData.

        Returns:
            str: String representation of LapHistoryData.
        """
        return (
            f"Lap Time: {self.m_lapTimeInMS} ms, Sector 1 Time: {self.m_sector1TimeInMS} ms, Sector 1 Minutes: {self.m_sector1TimeMinutes}, "
            f"Sector 2 Time: {self.m_sector2TimeInMS} ms, Sector 2 Minutes: {self.m_sector2TimeMinutes}, "
            f"Sector 3 Time: {self.m_sector3TimeInMS} ms, Sector 3 Minutes: {self.m_sector3TimeMinutes}, "
            f"Lap Valid Bit Flags: {self.m_lapValidBitFlags}"
        )

class TyreStintHistoryData:
    """
    Class representing tyre stint history data for a session.

    Attributes:
        m_endLap (uint8): Lap the tyre usage ends on (255 if current tyre).
        m_tyreActualCompound (uint8): Actual tyres used by this driver.
        m_tyreVisualCompound (uint8): Visual tyres used by this driver.
    """

    def __init__(self, data: bytes) -> None:
        """
        Initializes TyreStintHistoryData with raw data.

        Args:
            data (bytes): Raw data representing tyre stint history for a session.
        """
        (
            self.m_endLap,
            self.m_tyreActualCompound,
            self.m_tyreVisualCompound,
        ) = struct.unpack(session_history_tyre_stint_format_string, data)

    def __str__(self) -> str:
        """
        Returns a string representation of TyreStintHistoryData.

        Returns:
            str: String representation of TyreStintHistoryData.
        """
        return (
            f"End Lap: {self.m_endLap}, "
            f"Tyre Actual Compound: {self.m_tyreActualCompound}, "
            f"Tyre Visual Compound: {self.m_tyreVisualCompound}"
        )

class PacketSessionHistoryData:
    """
    Represents the packet containing session history data for a specific car.

    Attributes:
        m_header (PacketHeader): The header of the packet.
        m_carIdx (int): Index of the car this lap data relates to.
        m_numLaps (int): Number of laps in the data (including the current partial lap).
        m_numTyreStints (int): Number of tyre stints in the data.
        m_bestLapTimeLapNum (int): Lap the best lap time was achieved on.
        m_bestSector1LapNum (int): Lap the best Sector 1 time was achieved on.
        m_bestSector2LapNum (int): Lap the best Sector 2 time was achieved on.
        m_bestSector3LapNum (int): Lap the best Sector 3 time was achieved on.
        m_lapHistoryData (List[LapHistoryData]): List of lap history data for each lap.
        m_tyreStintsHistoryData (List[TyreStintHistoryData]): List of tyre stint history data.
    """

    max_laps = 100
    max_tyre_stint_count = 8

    def __init__(self, header, data) -> None:
        """
        Initializes PacketSessionHistoryData with raw data.

        Args:
            header (PacketHeader): The header of the packet.
            data (bytes): Raw data representing session history for a car in a race.
        """
        self.m_header: PacketHeader = header
        (
            self.m_carIdx,
            self.m_numLaps,
            self.m_numTyreStints,
            self.m_bestLapTimeLapNum,
            self.m_bestSector1LapNum,
            self.m_bestSector2LapNum,
            self.m_bestSector3LapNum,
        ) = struct.unpack(session_history_format_string, data[:F1_23_SESSION_HISTORY_LEN])
        bytes_index_so_far = F1_23_SESSION_HISTORY_LEN

        self.m_lapHistoryData: List[LapHistoryData] = []
        self.m_tyreStintsHistoryData: List[TyreStintHistoryData] = []

        # Next, parse the lap history data
        len_total_lap_hist = F1_23_SESSION_HISTORY_LAP_HISTORY_DATA_LEN * PacketSessionHistoryData.max_laps
        laps_history_data_all = _extract_sublist(data, bytes_index_so_far, bytes_index_so_far+len_total_lap_hist)
        for per_lap_history_raw in _split_list(laps_history_data_all, F1_23_SESSION_HISTORY_LAP_HISTORY_DATA_LEN):
            self.m_lapHistoryData.append(LapHistoryData(per_lap_history_raw))
        bytes_index_so_far += len_total_lap_hist

        # Finally, parse tyre stint data
        len_total_tyre_stint = PacketSessionHistoryData.max_tyre_stint_count * F1_23_SESSION_HISTORY_TYRE_STINT_LEN
        tyre_stint_history_all = _extract_sublist(data, bytes_index_so_far, (bytes_index_so_far+len_total_tyre_stint))
        for tyre_history_per_stint_raw in _split_list(tyre_stint_history_all, F1_23_SESSION_HISTORY_TYRE_STINT_LEN):
            self.m_tyreStintsHistoryData.append(TyreStintHistoryData(tyre_history_per_stint_raw))

    def __str__(self) -> str:
        """
        Returns a string representation of PacketSessionHistoryData.

        Returns:
            str: String representation of PacketSessionHistoryData.
        """
        return (
            f"Header: {str(self.m_header)}, "
            f"Car Index: {self.m_carIdx}, "
            f"Num Laps: {self.m_numLaps}, "
            f"Num Tyre Stints: {self.m_numTyreStints}, "
            f"Best Lap Time Lap Num: {self.m_bestLapTimeLapNum}, "
            f"Best Sector 1 Lap Num: {self.m_bestSector1LapNum}, "
            f"Best Sector 2 Lap Num: {self.m_bestSector2LapNum}, "
            f"Best Sector 3 Lap Num: {self.m_bestSector3LapNum}, "
            f"Lap History Data: {[str(lap_data) for lap_data in self.m_lapHistoryData[self.m_numLaps:]]}, "
            f"Tyre Stints History Data: {[str(tyre_stint_data) for tyre_stint_data in self.m_tyreStintsHistoryData[self.m_numTyreStints:]]}"
        )

# ------------------------- PACKET TYPE 12 - TYRE SETS -------------------------

class TyreSetData:
    """
    Represents information about a specific tyre set, including its compound, wear, availability, and other details.

    Attributes:
        m_actualTyreCompound (int): Actual tyre compound used.
        m_visualTyreCompound (int): Visual tyre compound used.
        m_wear (int): Tyre wear percentage.
        m_available (int): Whether this set is currently available.
        m_recommendedSession (int): Recommended session for the tyre set.
        m_lifeSpan (int): Laps left in this tyre set.
        m_usableLife (int): Max number of laps recommended for this compound.
        m_lapDeltaTime (int): Lap delta time in milliseconds compared to the fitted set.
        m_fitted (int): Whether the set is fitted or not.

    Methods:
        __init__(self, data: bytes) -> None:
            Initializes TyreSetData with raw data.

        __str__(self) -> str:
            Returns a string representation of TyreSetData.
    """

    def __init__(self, data) -> None:
        """
        Initializes TyreSetData with raw data.

        Args:
            data (bytes): Raw data representing information about a tyre set.
        """
        (
            self.m_actualTyreCompound,
            self.m_visualTyreCompound,
            self.m_wear,
            self.m_available,
            self.m_recommendedSession,
            self.m_lifeSpan,
            self.m_usableLife,
            self.m_lapDeltaTime,
            self.m_fitted,
        ) = struct.unpack(tyre_set_data_per_set_format_string, data)

    def __str__(self) -> str:
        """
        Returns a string representation of TyreSetData.

        Returns:
            str: String representation of TyreSetData.
        """
        return (
            f"Actual Tyre Compound: {self.m_actualTyreCompound}, Visual Tyre Compound: {self.m_visualTyreCompound}, "
            f"Wear: {self.m_wear}%, Available: {self.m_available}, Recommended Session: {self.m_recommendedSession}, "
            f"Life Span: {self.m_lifeSpan}, Usable Life: {self.m_usableLife}, Lap Delta Time: {self.m_lapDeltaTime} ms, "
            f"Fitted: {self.m_fitted}"
        )

class PacketTyreSetsData:
    """
    Represents information about tyre sets for a specific car in a race.

    Attributes:
        m_header (PacketHeader): Header information for the packet.
        m_carIdx (int): Index of the car this data relates to.
        m_tyreSetData (List[TyreSetData]): List of TyreSetData objects representing tyre set information.
        m_fittedIdx (int): Index into the array of the fitted tyre.

    """
    max_tyre_sets = 20

    def __init__(self, header, data) -> None:
        """
        Initializes PacketTyreSetsData with raw data.

        Args:
            header (PacketHeader): Header information for the packet.
            data (bytes): Raw data representing information about tyre sets for a car in a race.
        """
        self.m_header: PacketHeader = header
        self.m_carIdx: int = struct.unpack("<B", data[0:1])[0]
        self.m_tyreSetData: List[TyreSetData] = []

        tyre_set_data_full_len = PacketTyreSetsData.max_tyre_sets * F1_23_TYRE_SET_DATA_PER_SET_LEN
        full_tyre_set_data_raw = _extract_sublist(data, 1, 1 + tyre_set_data_full_len)
        for tyre_set_data_raw in _split_list(full_tyre_set_data_raw, F1_23_TYRE_SET_DATA_PER_SET_LEN):
            self.m_tyreSetData.append(TyreSetData(tyre_set_data_raw))

        self.m_fittedIdx = struct.unpack("<B", data[(1 + tyre_set_data_full_len):])[0]

    def __str__(self) -> str:
        """
        Returns a string representation of PacketTyreSetsData.

        Returns:
            str: String representation of PacketTyreSetsData.
        """
        return (
            f"Header: {str(self.m_header)}, Car Index: {self.m_carIdx}, "
            f"Tyre Set Data: {[str(tyre_set_data) for tyre_set_data in self.m_tyreSetData]}, Fitted Index: {self.m_fittedIdx}"
        )

# ------------------------- PACKET TYPE 13 - MOTION EX -------------------------

class PacketMotionExData:
    """
    Represents extended motion data for a player's car.

    Attributes:
        m_header (PacketHeader): Header information for the packet.
        m_suspensionPosition (List[float]): Suspension position for each wheel.
        m_suspensionVelocity (List[float]): Suspension velocity for each wheel.
        m_suspensionAcceleration (List[float]): Suspension acceleration for each wheel.
        m_wheelSpeed (List[float]): Speed of each wheel.
        m_wheelSlipRatio (List[float]): Slip ratio for each wheel.
        m_wheelSlipAngle (List[float]): Slip angles for each wheel.
        m_wheelLatForce (List[float]): Lateral forces for each wheel.
        m_wheelLongForce (List[float]): Longitudinal forces for each wheel.
        m_heightOfCOGAboveGround (float): Height of the center of gravity above ground.
        m_localVelocityX (float): Velocity in local space along the X-axis.
        m_localVelocityY (float): Velocity in local space along the Y-axis.
        m_localVelocityZ (float): Velocity in local space along the Z-axis.
        m_angularVelocityX (float): Angular velocity around the X-axis.
        m_angularVelocityY (float): Angular velocity around the Y-axis.
        m_angularVelocityZ (float): Angular velocity around the Z-axis.
        m_angularAccelerationX (float): Angular acceleration around the X-axis.
        m_angularAccelerationY (float): Angular acceleration around the Y-axis.
        m_angularAccelerationZ (float): Angular acceleration around the Z-axis.
        m_frontWheelsAngle (float): Current front wheels angle in radians.
        m_wheelVertForce (List[float]): Vertical forces for each wheel.

    """

    def __init__(self, header, data) -> None:
        """
        Initializes PacketMotionExData with raw data.

        Args:
            header (PacketHeader): Header information for the packet.
            data (bytes): Raw data representing extended motion information for a player's car.
        """
        self.m_header = header

        # ... (same initialization as provided in the code snippet)

    def __str__(self) -> str:
        """
        Returns a string representation of PacketMotionExData.

        Returns:
            str: String representation of PacketMotionExData.
        """
        return (
            f"Header: {str(self.m_header)}, "
            f"Suspension Position: {str(self.m_suspensionPosition)}, "
            f"Suspension Velocity: {str(self.m_suspensionVelocity)}, "
            f"Suspension Acceleration: {str(self.m_suspensionAcceleration)}, "
            f"Wheel Speed: {str(self.m_wheelSpeed)}, "
            f"Wheel Slip Ratio: {str(self.m_wheelSlipRatio)}, "
            f"Wheel Slip Angle: {str(self.m_wheelSlipAngle)}, "
            f"Wheel Lat Force: {str(self.m_wheelLatForce)}, "
            f"Wheel Long Force: {str(self.m_wheelLongForce)}, "
            f"Height of COG Above Ground: {self.m_heightOfCOGAboveGround}, "
            f"Local Velocity (X, Y, Z): ({self.m_localVelocityX}, {self.m_localVelocityY}, {self.m_localVelocityZ}), "
            f"Angular Velocity (X, Y, Z): ({self.m_angularVelocityX}, {self.m_angularVelocityY}, {self.m_angularVelocityZ}), "
            f"Angular Acceleration (X, Y, Z): ({self.m_angularAccelerationX}, {self.m_angularAccelerationY}, {self.m_angularAccelerationZ}), "
            f"Front Wheels Angle: {self.m_frontWheelsAngle}, "
            f"Wheel Vertical Force: {str(self.m_wheelVertForce)}"
        )