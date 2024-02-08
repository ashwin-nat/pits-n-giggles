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

from enum import Enum, auto
from typing import List
from f1_packet_info import *
import struct
import binascii

def _split_list(original_list, sublist_length):
    return [original_list[i:i+sublist_length] for i in range(0, len(original_list), sublist_length)]

def _extract_sublist(data: bytes, lower_index: int, upper_index: int) -> bytes:
    # Ensure the indices are within bounds
    if lower_index < 0 or upper_index > len(data) or lower_index > upper_index:
        # Return an empty bytes object to indicate an error
        return b''

    # Extract the sub-list
    sub_list: bytes = data[lower_index:upper_index]
    return sub_list

def _packetDump(data):

    # Convert the raw bytes to a string of hex values in upper case with a space between each byte
    hex_string = binascii.hexlify(data).decode('utf-8').upper()

    # Add a space between each pair of characters and format as 8 bytes per line
    formatted_hex_string = ''
    i=0
    for char in hex_string:
        formatted_hex_string += char
        if i%32 == 0:
            formatted_hex_string += '\n'
        elif i%16 == 0:
            formatted_hex_string +='    '
        elif i%2 == 0:
            formatted_hex_string += ' '
        i += 1

    return formatted_hex_string

# -------------------- PACKET FORMAT STRINGS ---------------------------------
header_format_string = "<HBBBBBQfIIBB"
F1_23_PACKET_HEADER_LEN: int = struct.calcsize(header_format_string)

'''
    H # packet format
    B # year
    B # major
    B # minor
    B # ver
    B # pktID
    Q # sessionID
    f # session time
    I # uint32
    I # uint32
    B # carIndex
    B # sec car index
'''

class F1PacketType(Enum):
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
    def isValid(packet_type):
        if isinstance(packet_type, F1PacketType):
            return True  # It's already an instance of F1PacketType
        else:
            min_value = min(member.value for member in F1PacketType)
            max_value = max(member.value for member in F1PacketType)
            return min_value <= packet_type <= max_value

    def __str__(self):
        if F1PacketType.isValid(self.value):
            return self.name
        else:
            return 'packet type ' + str(self.value)

class InvalidPacketLengthError(Exception):
    def __init__(self, message):
        super().__init__("Invalid packet length. " + message)

class PacketHeader:
    def __init__(self, data) -> None:

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

    def isPacketTypeSupported(self):
        return self.is_supported_packet_type



class CarMotionData:
    def __init__(self, data) -> None:
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
        self.m_header: PacketHeader = header       # PacketHeader
        if ((len(packet) % F1_23_MOTION_PACKET_PER_CAR_LEN) != 0):
            raise InvalidPacketLengthError("Received packet length " + str(len(packet)) + " is not a multiple of " +
                                            str(F1_23_MOTION_PACKET_PER_CAR_LEN))
        self.m_carMotionData: List[CarMotionData] = []
        motion_data_packet_per_car = _split_list(packet, F1_23_MOTION_PACKET_PER_CAR_LEN)
        for motion_data_packet in motion_data_packet_per_car:
            self.m_carMotionData.append(CarMotionData(motion_data_packet))

    def __str__(self) -> str:
        car_motion_data_str = ", ".join(str(car) for car in self.m_carMotionData)
        return f"PacketMotionData(Header: {str(self.m_header)}, CarMotionData: [{car_motion_data_str}])"


class LapData:
    def __init__(self, data) -> None:

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


    def __str__(self) -> str:
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
        self.m_header: PacketHeader = header
        self.m_LapData: List[LapData] = []                 # LapData[22]
        self.m_LapDataCount = 22
        len_of_lap_data_array = self.m_LapDataCount * F1_23_LAP_DATA_PACKET_PER_CAR_LEN

        # 2 extra bytes for the two uint8 that follow LapData
        expected_len = (len_of_lap_data_array+2)
        if ((len(packet) != expected_len) != 0):
            raise InvalidPacketLengthError("Received LapDataPacket length " + str(len(packet)) + " is not of expected length " +
                                            str(expected_len))
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
        lap_data_str = ", ".join(str(data) for data in self.m_LapData)
        return f"PacketLapData(Header: {str(self.m_header)}, Car Lap Data: [{lap_data_str}])"

class CarSignalData:
    def __init__(self) -> None:
        self.m_bumperDamage: int = 0                # uint8
        self.m_lightDamage: int = 0                 # uint8
        self.m_leftEndPlateDamage: int = 0          # uint8
        self.m_rightEndPlateDamage: int = 0         # uint8

    def __str__(self) -> str:
        return (
            f"CarSignalData("
            f"Bumper Damage: {self.m_bumperDamage}, "
            f"Light Damage: {self.m_lightDamage}, "
            f"Left End Plate Damage: {self.m_leftEndPlateDamage}, "
            f"Right End Plate Damage: {self.m_rightEndPlateDamage})"
        )

class MarshalZoneFlagType(Enum):

    INVALID_UNKNOWN = -1
    NONE = 0
    GREEN_FLAG = 1
    BLUE_FLAG = 2
    YELLOW_FLAG = 3


    @staticmethod
    def isValid(packet_type):
        if isinstance(packet_type, MarshalZoneFlagType):
            return True  # It's already an instance of MarshalZoneFlagType
        else:
            min_value = min(member.value for member in MarshalZoneFlagType)
            max_value = max(member.value for member in MarshalZoneFlagType)
            return min_value <= packet_type <= max_value

    def __str__(self):
        if F1PacketType.isValid(self.value):
            return self.name
        else:
            return 'Marshal Zone Flag type ' + str(self.value)

class MarshalZone:
    def __init__(self, data) -> None:

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
    def __init__(self, data) -> None:

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

    def __str__(self) -> str:
        return (
            f"WeatherForecastSample("
            f"Session Type: {self.m_sessionType}, "
            f"Time Offset: {self.m_timeOffset}, "
            f"Weather: {self.m_weather}, "
            f"Track Temperature: {self.m_trackTemperature}, "
            f"Track Temp Change: {self.m_trackTemperatureChange}, "
            f"Air Temperature: {self.m_airTemperature}, "
            f"Air Temp Change: {self.m_airTemperatureChange}, "
            f"Rain Percentage: {self.m_rainPercentage})"
        )

class PacketSessionData:
    def __init__(self, header, data) -> None:
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

        # Next section 1, marshalZones
        section_1_size = marshal_zone_packet_len * self.m_maxMarshalZones
        section_1_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far+section_1_size)
        byte_index_so_far += section_1_size
        self.m_marshalZones: List[MarshalZone] = []         # List of marshal zones – max 21
        for per_marshal_zone_raw_data in _split_list(section_1_raw_data, marshal_zone_packet_len):
            self.m_marshalZones.append(MarshalZone(per_marshal_zone_raw_data))
        # section_1_raw_data = None

        # Section 2, till numWeatherForecastSamples
        section_2_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far + F1_23_SESSION_SECTION_2_PACKET_LEN)
        byte_index_so_far += F1_23_SESSION_SECTION_2_PACKET_LEN
        unpacked_data = struct.unpack(packet_session_section_2_format_str, section_2_raw_data)
        (
            self.m_safetyCarStatus, #           // 0 = no safety car, 1 = full 2 = virtual, 3 = formation lap
            self.m_networkGame, #               // 0 = offline, 1 = online
            self.m_numWeatherForecastSamples # // Number of weather samples to follow
        ) = unpacked_data
        # section_2_raw_data = None


        # Section 3 - weather forecast samples
        section_3_size = weather_forecast_sample_packet_len * self.m_maxWeatherForecastSamples
        section_3_raw_data = _extract_sublist(data, byte_index_so_far, byte_index_so_far+section_3_size)
        byte_index_so_far += section_3_size
        self.m_weatherForecastSamples: List[WeatherForecastSample] = []  # Array of weather forecast samples
        for per_weather_sample_raw_data in _split_list(section_3_raw_data, weather_forecast_sample_packet_len):
            self.m_weatherForecastSamples.append(WeatherForecastSample(per_weather_sample_raw_data))
        # section_3_raw_data = None

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
            f"Session Type: {self.m_sessionType}, "
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
    def __init__(self, data):

        format_str = "<Bf"
        unpacked_data = struct.unpack(format_str, data[0:struct.calcsize(format_str)])
        (
            self.vehicleIdx,
            self.lapTime
        ) = unpacked_data

    def __str__(self):
        return f"FastestLap(vehicleIdx={self.vehicleIdx}, lapTime={self.lapTime})"


class Retirement:
    def __init__(self, data):
        format_str = "<B"
        self.vehicleIdx = struct.unpack(format_str, data[0:struct.calcsize(format_str)])

    def __str__(self):
        return f"Retirement(vehicleIdx={self.vehicleIdx})"


class TeamMateInPits:
    def __init__(self, data):
        format_str = "<B"
        self.vehicleIdx = struct.unpack(format_str, data[0:struct.calcsize(format_str)])

    def __str__(self):
        return f"TeamMateInPits(vehicleIdx={self.vehicleIdx})"


class RaceWinner:
    def __init__(self, data):
        format_str = "<B"
        self.vehicleIdx = struct.unpack(format_str, data[0:struct.calcsize(format_str)])

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


class ParticipantData:
    def __init__(self, data) -> None:

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

    def __str__(self) -> str:
        return (
            f"ParticipantData("
            f"AI Controlled: {self.m_aiControlled}, "
            f"Driver ID: {self.m_driverId}, "
            f"Team ID: {self.m_teamId}, "
            f"Race Number: {self.m_raceNumber}, "
            f"Nationality: {self.m_nationality}, "
            f"Name: {self.m_name}, "
            f"Your Telemetry: {self.m_yourTelemetry})"
        )


class PacketParticipantsData:
    max_participants = 22
    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        self.m_header: PacketHeader = header         # PacketHeader
        self.m_numActiveCars: int = struct.unpack("<B", packet[0:1])[0]
        self.m_participants: List[ParticipantData] = []            # ParticipantData[22]

        for participant_data_raw in _split_list(packet[1:], F1_23_PER_PARTICIPANT_INFO_LEN):
            self.m_participants.append(ParticipantData(participant_data_raw))

    def __str__(self) -> str:
        participants_str = ", ".join(str(participant) for participant in self.m_participants)
        return (
            f"PacketParticipantsData("
            f"Header: {str(self.m_header)}, "
            f"Number of Active Cars: {self.m_numActiveCars}, "
            f"Participants: [{participants_str}])"
        )


class PacketCarSetupData:
    def __init__(self, header, packet: bytes) -> None:
        self.m_header: PacketHeader = header
        self.m_carSetups: List[CarSetupData] = []                # CarSetupData[22]

        for setup_per_car_raw_data in _split_list(packet, F1_23_CAR_SETUPS_LEN):
            self.m_carSetups.append(CarSetupData(setup_per_car_raw_data))

    def __str__(self) -> str:
        setups_str = ", ".join(str(setup) for setup in self.m_carSetups)
        return f"PacketCarSetupData(Header: {str(self.m_header)}, Car Setups: [{setups_str}])"


class CarSetupData:
    def __init__(self, data) -> None:

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


class PacketCarTelemetryData:

    max_telemetry_entries = 22
    def __init__(self, header:PacketHeader, packet: bytes) -> None:
        self.m_header: PacketHeader = header
        self.m_carTelemetryData: List[CarTelemetryData] = []         # CarTelemetryData[22]
        len_all_car_telemetry = PacketCarTelemetryData.max_telemetry_entries * F1_23_CAR_TELEMETRY_LEN

        for per_car_telemetry_raw_data in _split_list(packet[:len_all_car_telemetry], F1_23_CAR_TELEMETRY_LEN):
            self.m_carTelemetryData.append(CarTelemetryData(per_car_telemetry_raw_data))

        self.mfdPanelIndex, self.m_mfdPanelIndexSecondaryPlayer, self.m_suggestedGear = \
            struct.unpack("<BBb", packet[len_all_car_telemetry:])

    def __str__(self) -> str:
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
    def __init__(self, data) -> None:

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
            # self.m_brakesTemperature,  # array of 4
            brake_temp1,
            brake_temp2,
            brake_temp3,
            brake_temp4,
            # self.m_tyresSurfaceTemperature,  # array of 4
            tyre_surface_temp1,
            tyre_surface_temp2,
            tyre_surface_temp3,
            tyre_surface_temp4,
            # self.m_tyresInnerTemperature,  # array of 4
            tyre_inner_temp1,
            tyre_inner_temp2,
            tyre_inner_temp3,
            tyre_inner_temp4,
            self.m_engineTemperature,
            # self.m_tyresPressure,  # array of 4
            tyre_pressure_1,
            tyre_pressure_2,
            tyre_pressure_3,
            tyre_pressure_4,
            # self.m_surfaceType,  # array of 4
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


class PacketCarStatusData:
    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        self.m_header: PacketHeader = header
        self.m_carStatusData: List[CarStatusData] = []               # CarStatusData[22]

        for status_per_car_raw_data in _split_list(packet, F1_23_CAR_STATUS_LEN):
            self.m_carStatusData.append(CarStatusData(status_per_car_raw_data))


    def __str__(self) -> str:
        status_data_str = ", ".join(str(status) for status in self.m_carStatusData)
        return f"PacketCarStatusData(Header: {str(self.m_header)}, Car Status Data: [{status_data_str}])"


class CarStatusData:
    def __init__(self, data) -> None:

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


    def __str__(self):
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

class PacketFinalClassificationData:
    max_cars = 22
    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        self.m_header: PacketHeader = header
        self.m_numCars: int = struct.unpack("<B", packet[0:1])[0]
        self.m_classificationData: List[FinalClassificationData] = []  # FinalClassificationData[22]

        for classification_per_car_raw_data in _split_list(packet[1:], F1_23_FINAL_CLASSIFICATION_PER_CAR_LEN):
            self.m_classificationData.append(FinalClassificationData(classification_per_car_raw_data))

    def __str__(self) -> str:
        classification_data_str = ", ".join(str(data) for data in self.m_classificationData[:self.m_numCars])
        return (
            f"PacketFinalClassificationData("
            f"Number of Cars: {self.m_numCars}, "
            f"Classification Data: [{classification_data_str}])"
        )


class FinalClassificationData:
    def __init__(self, data) -> None:

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
            tyre_stints_actual1,
            tyre_stints_actual2,
            tyre_stints_actual3,
            tyre_stints_actual4,
            tyre_stints_actual5,
            tyre_stints_actual6,
            tyre_stints_actual7,
            tyre_stints_actual8,
            # self.m_tyreStintsVisual,  # array of 8
            tyre_stints_visual1,
            tyre_stints_visual2,
            tyre_stints_visual3,
            tyre_stints_visual4,
            tyre_stints_visual5,
            tyre_stints_visual6,
            tyre_stints_visual7,
            tyre_stints_visual8,
            # self.m_tyreStintsEndLaps,  # array of 8
            tyre_stints_end_laps1,
            tyre_stints_end_laps2,
            tyre_stints_end_laps3,
            tyre_stints_end_laps4,
            tyre_stints_end_laps5,
            tyre_stints_end_laps6,
            tyre_stints_end_laps7,
            tyre_stints_end_laps8,
        ) = struct.unpack(final_classification_per_car_format_string, data)

        self.m_tyreStintsActual = [tyre_stints_actual1, tyre_stints_actual2, tyre_stints_actual3, tyre_stints_actual4,
                                   tyre_stints_actual5, tyre_stints_actual6, tyre_stints_actual7, tyre_stints_actual8]
        self.m_tyreStintsVisual = [tyre_stints_visual1, tyre_stints_visual2, tyre_stints_visual3, tyre_stints_visual4,
                                   tyre_stints_visual5, tyre_stints_visual6, tyre_stints_visual7, tyre_stints_visual8]
        self.m_tyreStintsEndLaps = [tyre_stints_end_laps1, tyre_stints_end_laps2, tyre_stints_end_laps3, tyre_stints_end_laps4,
                                    tyre_stints_end_laps5, tyre_stints_end_laps6, tyre_stints_end_laps7, tyre_stints_end_laps8]

    def __str__(self):
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


class CarDamageData:
    def __init__(self, data) -> None:

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

    def __str__(self) -> str:
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
    def __init__(self, header, data) -> None:
        self.m_header: PacketHeader = header
        self.m_carDamageData: List[CarDamageData] = []

        for raw_data_per_car in _split_list(data, F1_23_DAMAGE_PER_CAR_PACKET_LEN):
            self.m_carDamageData.append(CarDamageData(raw_data_per_car))

    def __str__(self) -> str:
        return f"Header: {str(self.m_header)}, Car Damage Data: {[str(car_data) for car_data in self.m_carDamageData]}"

class LapHistoryData:
    def __init__(self, data) -> None:
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
        return (
            f"Lap Time: {self.m_lapTimeInMS} ms, Sector 1 Time: {self.m_sector1TimeInMS} ms, Sector 1 Minutes: {self.m_sector1TimeMinutes}, "
            f"Sector 2 Time: {self.m_sector2TimeInMS} ms, Sector 2 Minutes: {self.m_sector2TimeMinutes}, "
            f"Sector 3 Time: {self.m_sector3TimeInMS} ms, Sector 3 Minutes: {self.m_sector3TimeMinutes}, "
            f"Lap Valid Bit Flags: {self.m_lapValidBitFlags}"
        )

class TyreStintHistoryData:
    def __init__(self, data) -> None:
        (
            self.m_endLap,
            self.m_tyreActualCompound,
            self.m_tyreVisualCompound,
        ) = struct.unpack(session_history_tyre_stint_format_string, data)

    def __str__(self) -> str:
        return f"End Lap: {self.m_endLap}, Tyre Actual Compound: {self.m_tyreActualCompound}, Tyre Visual Compound: {self.m_tyreVisualCompound}"

class PacketSessionHistoryData:
    max_laps = 100
    max_tyre_stint_count = 8
    def __init__(self, header, data) -> None:
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
        return (
            f"Header: {str(self.m_header)}, Car Index: {self.m_carIdx}, Num Laps: {self.m_numLaps}, "
            f"Num Tyre Stints: {self.m_numTyreStints}, Best Lap Time Lap Num: {self.m_bestLapTimeLapNum}, "
            f"Best Sector 1 Lap Num: {self.m_bestSector1LapNum}, Best Sector 2 Lap Num: {self.m_bestSector2LapNum}, "
            f"Best Sector 3 Lap Num: {self.m_bestSector3LapNum}, Lap History Data: {[str(lap_data) for lap_data in self.m_lapHistoryData[self.m_numLaps:]]}, "
            f"Tyre Stints History Data: {[str(tyre_stint_data) for tyre_stint_data in self.m_tyreStintsHistoryData[self.m_numTyreStints:]]}"
        )

class TyreSetData:
    def __init__(self, data) -> None:
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
        return (
            f"Actual Tyre Compound: {self.m_actualTyreCompound}, Visual Tyre Compound: {self.m_visualTyreCompound}, "
            f"Wear: {self.m_wear}%, Available: {self.m_available}, Recommended Session: {self.m_recommendedSession}, "
            f"Life Span: {self.m_lifeSpan}, Usable Life: {self.m_usableLife}, Lap Delta Time: {self.m_lapDeltaTime} ms, "
            f"Fitted: {self.m_fitted}"
        )

class PacketTyreSetsData:
    max_tyre_sets = 20
    def __init__(self, header, data) -> None:
        self.m_header: PacketHeader = header
        self.m_carIdx: int = struct.unpack("<B", data[0:1])[0]
        self.m_tyreSetData: List[TyreSetData] = []

        tyre_set_data_full_len = PacketTyreSetsData.max_tyre_sets * F1_23_TYRE_SET_DATA_PER_SET_LEN
        full_tyre_set_data_raw = _extract_sublist(data, 1, 1+tyre_set_data_full_len)
        for tyre_set_data_raw in _split_list(full_tyre_set_data_raw, F1_23_TYRE_SET_DATA_PER_SET_LEN):
            self.m_tyreSetData.append(TyreSetData(tyre_set_data_raw))

        self.m_fittedIdx = struct.unpack("<B", data[(1+tyre_set_data_full_len):])[0]

    def __str__(self) -> str:
        return (
            f"Header: {str(self.m_header)}, Car Index: {self.m_carIdx}, "
            f"Tyre Set Data: {[str(tyre_set_data) for tyre_set_data in self.m_tyreSetData]}, Fitted Index: {self.m_fittedIdx}"
        )

class PacketMotionExData:
    def __init__(self, header, data) -> None:
        self.m_header = header

        self.m_suspensionPosition = [0.0] * 4
        self.m_suspensionVelocity = [0.0] * 4
        self.m_suspensionAcceleration = [0.0] * 4
        self.m_wheelSpeed = [0.0] * 4
        self.m_wheelSlipRatio = [0.0] * 4
        self.m_wheelSlipAngle = [0.0] * 4
        self.m_wheelLatForce = [0.0] * 4
        self.m_wheelLongForce = [0.0] * 4
        self.m_wheelVertForce = [0.0] * 4
        (
            self.m_suspensionPosition[0],           # array of floats
            self.m_suspensionPosition[1],           # array of floats
            self.m_suspensionPosition[2],           # array of floats
            self.m_suspensionPosition[3],           # array of floats
            self.m_suspensionVelocity[0],           # array of floats
            self.m_suspensionVelocity[1],           # array of floats
            self.m_suspensionVelocity[2],           # array of floats
            self.m_suspensionVelocity[3],           # array of floats
            self.m_suspensionAcceleration[0],       # array of floats
            self.m_suspensionAcceleration[1],       # array of floats
            self.m_suspensionAcceleration[2],       # array of floats
            self.m_suspensionAcceleration[3],       # array of floats
            self.m_wheelSpeed[0],                   # array of floats
            self.m_wheelSpeed[1],                   # array of floats
            self.m_wheelSpeed[2],                   # array of floats
            self.m_wheelSpeed[3],                   # array of floats
            self.m_wheelSlipRatio[0],               # array of floats
            self.m_wheelSlipRatio[1],               # array of floats
            self.m_wheelSlipRatio[2],               # array of floats
            self.m_wheelSlipRatio[3],               # array of floats
            self.m_wheelSlipAngle[0],               # array of floats
            self.m_wheelSlipAngle[1],               # array of floats
            self.m_wheelSlipAngle[2],               # array of floats
            self.m_wheelSlipAngle[3],               # array of floats
            self.m_wheelLatForce[0],                # array of floats
            self.m_wheelLatForce[1],                # array of floats
            self.m_wheelLatForce[2],                # array of floats
            self.m_wheelLatForce[3],                # array of floats
            self.m_wheelLongForce[0],               # array of floats
            self.m_wheelLongForce[1],               # array of floats
            self.m_wheelLongForce[2],               # array of floats
            self.m_wheelLongForce[3],               # array of floats
            self.m_heightOfCOGAboveGround,       # float
            self.m_localVelocityX,               # float
            self.m_localVelocityY,               # float
            self.m_localVelocityZ,               # float
            self.m_angularVelocityX,             # float
            self.m_angularVelocityY,             # float
            self.m_angularVelocityZ,             # float
            self.m_angularAccelerationX,         # float
            self.m_angularAccelerationY,         # float
            self.m_angularAccelerationZ,         # float
            self.m_frontWheelsAngle,             # float
            self.m_wheelVertForce[0],               # array of floats
            self.m_wheelVertForce[1],               # array of floats
            self.m_wheelVertForce[2],               # array of floats
            self.m_wheelVertForce[3],               # array of floats
        ) = struct.unpack(motion_ex_format_string, data)

    def __str__(self) -> str:
        return (
            f"Header: {str(self.m_header)}, Suspension Position: {str(self.m_suspensionPosition)}, "
            f"Suspension Velocity: {str(self.m_suspensionVelocity)}, Suspension Acceleration: {str(self.m_suspensionAcceleration)}, "
            f"Wheel Speed: {str(self.m_wheelSpeed)}, Wheel Slip Ratio: {str(self.m_wheelSlipRatio)}, Wheel Slip Angle: {str(self.m_wheelSlipAngle)}, "
            f"Wheel Lat Force: {str(self.m_wheelLatForce)}, Wheel Long Force: {str(self.m_wheelLongForce)}, "
            f"Height of COG Above Ground: {self.m_heightOfCOGAboveGround}, Local Velocity (X, Y, Z): "
            f"({self.m_localVelocityX}, {self.m_localVelocityY}, {self.m_localVelocityZ}), "
            f"Angular Velocity (X, Y, Z): ({self.m_angularVelocityX}, {self.m_angularVelocityY}, {self.m_angularVelocityZ}), "
            f"Angular Acceleration (X, Y, Z): ({self.m_angularAccelerationX}, {self.m_angularAccelerationY}, {self.m_angularAccelerationZ}), "
            f"Front Wheels Angle: {self.m_frontWheelsAngle}, Wheel Vertical Force: {str(self.m_wheelVertForce)}"
        )
