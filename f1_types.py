# MIT License
#
# Copyright (c) [year] [Your Name]
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

def _split_list(original_list, sublist_length):
    return [original_list[i:i+sublist_length] for i in range(0, len(original_list), sublist_length)]

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


class CarLapData:
    def __init__(self, data) -> None:

        unpacked_data = struct.unpack(motion_format_string, data)

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
            f"CarLapData("
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
        self.m_carLapData: List[CarLapData] = []                 # CarLapData[22]

        if ((len(packet) % F1_23_LAP_DATA_PACKET_PER_CAR_LEN) != 0):
            raise InvalidPacketLengthError("Received packet length " + str(len(packet)) + " is not a multiple of " +
                                            str(F1_23_LAP_DATA_PACKET_PER_CAR_LEN))
        lap_data_packet_per_car = _split_list(packet, F1_23_LAP_DATA_PACKET_PER_CAR_LEN)
        for lap_data_packet in lap_data_packet_per_car:
            self.m_carMotionData.append(CarLapData(lap_data_packet))

    def __str__(self) -> str:
        lap_data_str = ", ".join(str(data) for data in self.m_carLapData)
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



class MarshalZone:
    def __init__(self) -> None:
        self.m_zoneStart: float = 0.0  # Fraction (0..1) of way through the lap the marshal zone starts
        self.m_zoneFlag: int = -1      # -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow

    def __str__(self) -> str:
        return f"MarshalZone(Start: {self.m_zoneStart}, Flag: {self.m_zoneFlag})"


class WeatherForecastSample:
    def __init__(self) -> None:
        self.m_sessionType: int = 0                   # uint8
        self.m_timeOffset: int = 0                    # uint8
        self.m_weather: int = 0                       # uint8
        self.m_trackTemperature: int = 0              # int8
        self.m_trackTemperatureChange: int = 0        # int8
        self.m_airTemperature: int = 0                # int8
        self.m_airTemperatureChange: int = 0          # int8
        self.m_rainPercentage: int = 0               # uint8

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
    def __init__(self) -> None:
        self.m_header: PacketHeader = PacketHeader()          # Header
        self.m_weather: int = 0                             # uint8
        self.m_trackTemperature: int = 0                    # int8
        self.m_airTemperature: int = 0                      # int8
        self.m_totalLaps: int = 0                           # uint8
        self.m_trackLength: int = 0                         # uint16
        self.m_sessionType: int = 0                         # uint8
        self.m_trackId: int = 0                             # int8
        self.m_formula: int = 0                             # uint8
        self.m_sessionTimeLeft: int = 0                     # uint16
        self.m_sessionDuration: int = 0                     # uint16
        self.m_pitSpeedLimit: int = 0                       # uint8
        self.m_gamePaused: int = 0                          # uint8
        self.m_isSpectating: int = 0                        # uint8
        self.m_spectatorCarIndex: int = 0                   # uint8
        self.m_sliProNativeSupport: int = 0                 # uint8
        self.m_numMarshalZones: int = 0                     # uint8
        self.m_marshalZones: List[MarshalZone] = []         # List of marshal zones – max 21
        self.m_safetyCarStatus: int = 0                     # uint8
        self.m_networkGame: int = 0                         # uint8
        self.m_numWeatherForecastSamples: int = 0           # uint8
        self.m_weatherForecastSamples: List[WeatherForecastSample] = []  # Array of weather forecast samples
        self.m_forecastAccuracy: int = 0                    # uint8
        self.m_aiDifficulty: int = 0                        # uint8
        self.m_seasonLinkIdentifier: int = 0               # uint32
        self.m_weekendLinkIdentifier: int = 0              # uint32
        self.m_sessionLinkIdentifier: int = 0              # uint32
        self.m_pitStopWindowIdealLap: int = 0              # uint8
        self.m_pitStopWindowLatestLap: int = 0             # uint8
        self.m_pitStopRejoinPosition: int = 0              # uint8
        self.m_steeringAssist: int = 0                     # uint8
        self.m_brakingAssist: int = 0                      # uint8
        self.m_gearboxAssist: int = 0                      # uint8
        self.m_pitAssist: int = 0                          # uint8
        self.m_pitReleaseAssist: int = 0                   # uint8
        self.m_ERSAssist: int = 0                          # uint8
        self.m_DRSAssist: int = 0                          # uint8
        self.m_dynamicRacingLine: int = 0                 # uint8
        self.m_dynamicRacingLineType: int = 0             # uint8
        self.m_gameMode: int = 0                           # uint8
        self.m_ruleSet: int = 0                            # uint8
        self.m_timeOfDay: int = 0                          # uint32
        self.m_sessionLength: int = 0                      # uint8
        self.m_speedUnitsLeadPlayer: int = 0              # uint8
        self.m_temperatureUnitsLeadPlayer: int = 0        # uint8
        self.m_speedUnitsSecondaryPlayer: int = 0         # uint8
        self.m_temperatureUnitsSecondaryPlayer: int = 0   # uint8
        self.m_numSafetyCarPeriods: int = 0               # uint8
        self.m_numVirtualSafetyCarPeriods: int = 0        # uint8
        self.m_numRedFlagPeriods: int = 0                 # uint8

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


class PacketCarTelemetryData:
    def __init__(self, packet: bytes) -> None:
        self.m_header: PacketHeader = PacketHeader(packet)           # PacketHeader
        self.m_carTelemetryData: List[CarTelemetryData] = []         # CarTelemetryData[22]
        self.m_buttonStatus: int = 0                                # uint32

    def __str__(self) -> str:
        telemetry_data_str = ", ".join(str(data) for data in self.m_carTelemetryData)
        return (
            f"PacketCarTelemetryData("
            f"Header: {str(self.m_header)}, "
            f"Car Telemetry Data: [{telemetry_data_str}], "
            f"Button Status: {self.m_buttonStatus})"
        )


class PacketCarStatusData:
    def __init__(self, packet: bytes) -> None:
        self.m_header: PacketHeader = PacketHeader(packet)           # PacketHeader
        self.m_carStatusData: List[CarStatusData] = []               # CarStatusData[22]

    def __str__(self) -> str:
        status_data_str = ", ".join(str(data) for data in self.m_carStatusData)
        return f"PacketCarStatusData(Header: {str(self.m_header)}, Car Status Data: [{status_data_str}])"




class PacketEventData:
    def __init__(self, packet: bytes) -> None:
        self.m_header: PacketHeader = PacketHeader(packet)       # PacketHeader
        self.m_eventStringCode: str = ""                         # char[4]

    def __str__(self) -> str:
        return f"PacketEventData(Header: {str(self.m_header)}, Event String Code: {self.m_eventStringCode})"


class ParticipantData:
    def __init__(self) -> None:
        self.m_aiControlled: int = 0               # uint8
        self.m_driverId: int = 0                   # uint8
        self.m_teamId: int = 0                     # uint8
        self.m_raceNumber: int = 0                 # uint8
        self.m_nationality: int = 0                # uint8
        self.m_name: str = ""                      # char[48]
        self.m_yourTelemetry: int = 0             # uint8

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
    def __init__(self, packet: bytes) -> None:
        self.m_header: PacketHeader = PacketHeader(packet)         # PacketHeader
        self.m_numActiveCars: int = 0                              # uint8
        self.m_participants: List[ParticipantData] = []            # ParticipantData[22]

    def __str__(self) -> str:
        participants_str = ", ".join(str(participant) for participant in self.m_participants)
        return (
            f"PacketParticipantsData("
            f"Header: {str(self.m_header)}, "
            f"Number of Active Cars: {self.m_numActiveCars}, "
            f"Participants: [{participants_str}])"
        )


class PacketCarSetupData:
    def __init__(self, packet: bytes) -> None:
        self.m_header: PacketHeader = PacketHeader(packet)       # PacketHeader
        self.m_carSetups: List[CarSetupData] = []                # CarSetupData[22]

    def __str__(self) -> str:
        setups_str = ", ".join(str(setup) for setup in self.m_carSetups)
        return f"PacketCarSetupData(Header: {str(self.m_header)}, Car Setups: [{setups_str}])"


class CarSetupData:
    def __init__(self) -> None:
        self.m_frontWing: int = 0               # uint8
        self.m_rearWing: int = 0                # uint8
        self.m_onThrottle: int = 0              # uint8
        self.m_offThrottle: int = 0             # uint8
        self.m_frontCamber: float = 0           # float
        self.m_rearCamber: float = 0            # float
        self.m_frontToe: float = 0              # float
        self.m_rearToe: float = 0               # float
        self.m_frontSuspension: int = 0         # uint8
        self.m_rearSuspension: int = 0          # uint8
        self.m_frontAntiRollBar: int = 0        # uint8
        self.m_rearAntiRollBar: int = 0         # uint8
        self.m_frontSuspensionHeight: int = 0   # uint8
        self.m_rearSuspensionHeight: int = 0    # uint8
        self.m_brakePressure: int = 0           # uint8
        self.m_brakeBias: int = 0               # uint8
        self.m_frontTyrePressure: float = 0     # float
        self.m_rearTyrePressure: float = 0      # float
        self.m_ballast: int = 0                 # uint8
        self.m_fuelLoad: float = 0              # float

    def __str__(self) -> str:
        return (
            f"CarSetupData("
            f"Front Wing: {self.m_frontWing}, "
            f"Rear Wing: {self.m_rearWing}, "
            f"On Throttle: {self.m_onThrottle}, "
            f"Off Throttle: {self.m_offThrottle}, "
            f"Front Camber: {self.m_frontCamber}, "
            f"Rear Camber: {self.m_rearCamber}, "
            f"Front Toe: {self.m_frontToe}, "
            f"Rear Toe: {self.m_rearToe}, "
            f"Front Suspension: {self.m_frontSuspension}, "
            f"Rear Suspension: {self.m_rearSuspension}, "
            f"Front Anti-Roll Bar: {self.m_frontAntiRollBar}, "
            f"Rear Anti-Roll Bar: {self.m_rearAntiRollBar}, "
            f"Front Suspension Height: {self.m_frontSuspensionHeight}, "
            f"Rear Suspension Height: {self.m_rearSuspensionHeight}, "
            f"Brake Pressure: {self.m_brakePressure}, "
            f"Brake Bias: {self.m_brakeBias}, "
            f"Front Tyre Pressure: {self.m_frontTyrePressure}, "
            f"Rear Tyre Pressure: {self.m_rearTyrePressure}, "
            f"Ballast: {self.m_ballast}, "
            f"Fuel Load: {self.m_fuelLoad})"
        )


class PacketCarTelemetryData:
    def __init__(self, packet: bytes) -> None:
        self.m_header: PacketHeader = PacketHeader(packet)           # PacketHeader
        self.m_carTelemetryData: List[CarTelemetryData] = []         # CarTelemetryData[22]
        self.m_buttonStatus: int = 0                                # uint32

    def __str__(self) -> str:
        telemetry_data_str = ", ".join(str(telemetry) for telemetry in self.m_carTelemetryData)
        return (
            f"PacketCarTelemetryData("
            f"Header: {str(self.m_header)}, "
            f"Car Telemetry Data: [{telemetry_data_str}], "
            f"Button Status: {self.m_buttonStatus})"
        )


class CarTelemetryData:
    def __init__(self) -> None:
        self.m_speed: int = 0                   # uint16
        self.m_throttle: float = 0              # float
        self.m_steer: float = 0                 # float
        self.m_brake: float = 0                 # float
        self.m_clutch: int = 0                  # uint8
        self.m_gear: int = 0                    # int8
        self.m_engineRPM: int = 0               # uint16
        self.m_drs: int = 0                     # uint8
        self.m_revLightsPercent: int = 0        # uint8
        self.m_brakesTemperature: List[int] = []           # uint16[4]
        self.m_tyresSurfaceTemperature: List[int] = []     # uint8[4]
        self.m_tyresInnerTemperature: List[int] = []       # uint8[4]
        self.m_engineTemperature: int = 0                   # uint16
        self.m_tyresPressure: List[float] = []              # float[4]

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
            f"Brakes Temperature: {self.m_brakesTemperature}, "
            f"Tyres Surface Temperature: {self.m_tyresSurfaceTemperature}, "
            f"Tyres Inner Temperature: {self.m_tyresInnerTemperature}, "
            f"Engine Temperature: {self.m_engineTemperature}, "
            f"Tyres Pressure: {self.m_tyresPressure})"
        )


class PacketCarStatusData:
    def __init__(self, packet: bytes) -> None:
        self.m_header: PacketHeader = PacketHeader(packet)           # PacketHeader
        self.m_carStatusData: List[CarStatusData] = []               # CarStatusData[22]

    def __str__(self) -> str:
        status_data_str = ", ".join(str(status) for status in self.m_carStatusData)
        return f"PacketCarStatusData(Header: {str(self.m_header)}, Car Status Data: [{status_data_str}])"


class CarStatusData:
    def __init__(self) -> None:
        self.m_tractionControl: int = 0             # uint8
        self.m_antiLockBrakes: int = 0              # uint8
        self.m_fuelMix: int = 0                     # uint8
        self.m_frontBrakeBias: int = 0              # uint8
        self.m_pitLimiterStatus: int = 0            # uint8
        self.m_fuelInTank: float = 0                # float
        self.m_fuelCapacity: float = 0              # float
        self.m_maxRPM: int = 0                      # uint16
        self.m_idleRPM: int = 0                     # uint16
        self.m_maxGears: int = 0                    # uint8
        self.m_drsAllowed: int = 0                  # uint8
        self.m_tyresWear: List[int] = []            # uint8[4]
        self.m_tyreCompound: int = 0                # uint8
        self.m_visualTyreCompound: int = 0          # uint8
        self.m_tyresAgeLaps: int = 0                # uint8
        self.m_tyresDamage: List[int] = []          # uint8[4]
        self.m_frontLeftWingDamage: int = 0         # uint8
        self.m_frontRightWingDamage: int = 0        # uint8
        self.m_rearWingDamage: int = 0              # uint8
        self.m_engineDamage: int = 0                # uint8
        self.m_gearBoxDamage: int = 0               # uint8
        self.m_exhaustDamage: int = 0               # uint8
        self.m_vehicleFiaFlags: int = 0             # int8

    def __str__(self) -> str:
        return (
            f"CarStatusData("
            f"Traction Control: {self.m_tractionControl}, "
            f"Anti-lock Brakes: {self.m_antiLockBrakes}, "
            f"Fuel Mix: {self.m_fuelMix}, "
            f"Front Brake Bias: {self.m_frontBrakeBias}, "
            f"Pit Limiter Status: {self.m_pitLimiterStatus}, "
            f"Fuel In Tank: {self.m_fuelInTank}, "
            f"Fuel Capacity: {self.m_fuelCapacity}, "
            f"Max RPM: {self.m_maxRPM}, "
            f"Idle RPM: {self.m_idleRPM}, "
            f"Max Gears: {self.m_maxGears}, "
            f"DRS Allowed: {self.m_drsAllowed}, "
            f"Tyres Wear: {self.m_tyresWear}, "
            f"Tyre Compound: {self.m_tyreCompound}, "
            f"Visual Tyre Compound: {self.m_visualTyreCompound}, "
            f"Tyres Age Laps: {self.m_tyresAgeLaps}, "
            f"Tyres Damage: {self.m_tyresDamage}, "
            f"Front Left Wing Damage: {self.m_frontLeftWingDamage}, "
            f"Front Right Wing Damage: {self.m_frontRightWingDamage}, "
            f"Rear Wing Damage: {self.m_rearWingDamage}, "
            f"Engine Damage: {self.m_engineDamage}, "
            f"Gearbox Damage: {self.m_gearBoxDamage}, "
            f"Exhaust Damage: {self.m_exhaustDamage}, "
            f"Vehicle FIA Flags: {self.m_vehicleFiaFlags})"
        )

class PacketFinalClassificationData:
    def __init__(self, packet: bytes) -> None:
        self.m_header: PacketHeader = PacketHeader(packet)           # PacketHeader
        self.m_numCars: int = 0                                      # uint8
        self.m_classificationData: List[FinalClassificationData] = []  # FinalClassificationData[22]

    def __str__(self) -> str:
        classification_data_str = ", ".join(str(data) for data in self.m_classificationData)
        return (
            f"PacketFinalClassificationData("
            f"Header: {str(self.m_header)}, "
            f"Number of Cars: {self.m_numCars}, "
            f"Classification Data: [{classification_data_str}])"
        )


class FinalClassificationData:
    def __init__(self) -> None:
        self.m_position: int = 0                   # uint8
        self.m_lapTime: float = 0                   # float
        self.m_numLaps: int = 0                     # uint8
        self.m_gridPosition: int = 0                # uint8
        self.m_points: int = 0                      # uint8
        self.m_numPitStops: int = 0                 # uint8
        self.m_resultStatus: int = 0                # uint8
        self.m_bestLapTime: float = 0               # float
        self.m_totalRaceTime: float = 0             # double

    def __str__(self) -> str:
        return (
            f"FinalClassificationData("
            f"Position: {self.m_position}, "
            f"Lap Time: {self.m_lapTime}, "
            f"Number of Laps: {self.m_numLaps}, "
            f"Grid Position: {self.m_gridPosition}, "
            f"Points: {self.m_points}, "
            f"Number of Pit Stops: {self.m_numPitStops}, "
            f"Result Status: {self.m_resultStatus}, "
            f"Best Lap Time: {self.m_bestLapTime}, "
            f"Total Race Time: {self.m_totalRaceTime})"
        )


class PacketLobbyInfoData:
    def __init__(self, packet: bytes) -> None:
        self.m_header: PacketHeader = PacketHeader(packet)         # PacketHeader
        self.m_numPlayers: int = 0                                  # uint8
        self.m_lobbyPlayers: List[LobbyInfoData] = []              # LobbyInfoData[22]

    def __str__(self) -> str:
        lobby_players_str = ", ".join(str(player) for player in self.m_lobbyPlayers)
        return (
            f"PacketLobbyInfoData("
            f"Header: {str(self.m_header)}, "
            f"Number of Players: {self.m_numPlayers}, "
            f"Lobby Players: [{lobby_players_str}])"
        )


class LobbyInfoData:
    def __init__(self) -> None:
        self.m_aiControlled: int = 0               # uint8
        self.m_teamId: int = 0                     # uint8
        self.m_nationality: int = 0                # uint8
        self.m_name: str = ""                      # char[48]
        self.m_readyStatus: int = 0                # uint8

    def __str__(self) -> str:
        return (
            f"LobbyInfoData("
            f"AI Controlled: {self.m_aiControlled}, "
            f"Team ID: {self.m_teamId}, "
            f"Nationality: {self.m_nationality}, "
            f"Name: {self.m_name}, "
            f"Ready Status: {self.m_readyStatus})"
        )


class CarDamageData:
    def __init__(self) -> None:
        self.m_tyresWear: List[float] = [0.0, 0.0, 0.0, 0.0]  # Tyre wear (percentage)
        self.m_tyresDamage: List[int] = [0, 0, 0, 0]          # Tyre damage (percentage)
        self.m_brakesDamage: List[int] = [0, 0, 0, 0]         # Brakes damage (percentage)
        self.m_frontLeftWingDamage: int = 0                  # Front left wing damage (percentage)
        self.m_frontRightWingDamage: int = 0                 # Front right wing damage (percentage)
        self.m_rearWingDamage: int = 0                       # Rear wing damage (percentage)
        self.m_floorDamage: int = 0                          # Floor damage (percentage)
        self.m_diffuserDamage: int = 0                       # Diffuser damage (percentage)
        self.m_sidepodDamage: int = 0                        # Sidepod damage (percentage)
        self.m_drsFault: int = 0                             # Indicator for DRS fault, 0 = OK, 1 = fault
        self.m_ersFault: int = 0                             # Indicator for ERS fault, 0 = OK, 1 = fault
        self.m_gearBoxDamage: int = 0                        # Gear box damage (percentage)
        self.m_engineDamage: int = 0                         # Engine damage (percentage)
        self.m_engineMGUHWear: int = 0                       # Engine wear MGU-H (percentage)
        self.m_engineESWear: int = 0                         # Engine wear ES (percentage)
        self.m_engineCEWear: int = 0                         # Engine wear CE (percentage)
        self.m_engineICEWear: int = 0                        # Engine wear ICE (percentage)
        self.m_engineMGUKWear: int = 0                       # Engine wear MGU-K (percentage)
        self.m_engineTCWear: int = 0                         # Engine wear TC (percentage)
        self.m_engineBlown: int = 0                          # Engine blown, 0 = OK, 1 = fault
        self.m_engineSeized: int = 0                         # Engine seized, 0 = OK, 1 = fault

    def __str__(self) -> str:
        return (
            f"Tyres Wear: {self.m_tyresWear}, Tyres Damage: {self.m_tyresDamage}, "
            f"Brakes Damage: {self.m_brakesDamage}, Front Left Wing Damage: {self.m_frontLeftWingDamage}, "
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
    def __init__(self) -> None:
        self.m_header: PacketHeader = PacketHeader()
        self.m_carDamageData: List[CarDamageData] = [CarDamageData() for _ in range(22)]

    def __str__(self) -> str:
        return f"Header: {str(self.m_header)}, Car Damage Data: {[str(car_data) for car_data in self.m_carDamageData]}"

class LapHistoryData:
    def __init__(self) -> None:
        self.m_lapTimeInMS: int = 0
        self.m_sector1TimeInMS: int = 0
        self.m_sector1TimeMinutes: int = 0
        self.m_sector2TimeInMS: int = 0
        self.m_sector2TimeMinutes: int = 0
        self.m_sector3TimeInMS: int = 0
        self.m_sector3TimeMinutes: int = 0
        self.m_lapValidBitFlags: int = 0

    def __str__(self) -> str:
        return (
            f"Lap Time: {self.m_lapTimeInMS} ms, Sector 1 Time: {self.m_sector1TimeInMS} ms, Sector 1 Minutes: {self.m_sector1TimeMinutes}, "
            f"Sector 2 Time: {self.m_sector2TimeInMS} ms, Sector 2 Minutes: {self.m_sector2TimeMinutes}, "
            f"Sector 3 Time: {self.m_sector3TimeInMS} ms, Sector 3 Minutes: {self.m_sector3TimeMinutes}, "
            f"Lap Valid Bit Flags: {self.m_lapValidBitFlags}"
        )

class TyreStintHistoryData:
    def __init__(self) -> None:
        self.m_endLap: int = 0
        self.m_tyreActualCompound: int = 0
        self.m_tyreVisualCompound: int = 0

    def __str__(self) -> str:
        return f"End Lap: {self.m_endLap}, Tyre Actual Compound: {self.m_tyreActualCompound}, Tyre Visual Compound: {self.m_tyreVisualCompound}"

class PacketSessionHistoryData:
    def __init__(self) -> None:
        self.m_header: PacketHeader = PacketHeader()
        self.m_carIdx: int = 0
        self.m_numLaps: int = 0
        self.m_numTyreStints: int = 0
        self.m_bestLapTimeLapNum: int = 0
        self.m_bestSector1LapNum: int = 0
        self.m_bestSector2LapNum: int = 0
        self.m_bestSector3LapNum: int = 0
        self.m_lapHistoryData: List[LapHistoryData] = []
        self.m_tyreStintsHistoryData: List[TyreStintHistoryData] = []

    def __str__(self) -> str:
        return (
            f"Header: {str(self.m_header)}, Car Index: {self.m_carIdx}, Num Laps: {self.m_numLaps}, "
            f"Num Tyre Stints: {self.m_numTyreStints}, Best Lap Time Lap Num: {self.m_bestLapTimeLapNum}, "
            f"Best Sector 1 Lap Num: {self.m_bestSector1LapNum}, Best Sector 2 Lap Num: {self.m_bestSector2LapNum}, "
            f"Best Sector 3 Lap Num: {self.m_bestSector3LapNum}, Lap History Data: {[str(lap_data) for lap_data in self.m_lapHistoryData]}, "
            f"Tyre Stints History Data: {[str(tyre_stint_data) for tyre_stint_data in self.m_tyreStintsHistoryData]}"
        )

class TyreSetData:
    def __init__(self) -> None:
        self.m_actualTyreCompound: int = 0
        self.m_visualTyreCompound: int = 0
        self.m_wear: int = 0
        self.m_available: int = 0
        self.m_recommendedSession: int = 0
        self.m_lifeSpan: int = 0
        self.m_usableLife: int = 0
        self.m_lapDeltaTime: int = 0
        self.m_fitted: int = 0

    def __str__(self) -> str:
        return (
            f"Actual Tyre Compound: {self.m_actualTyreCompound}, Visual Tyre Compound: {self.m_visualTyreCompound}, "
            f"Wear: {self.m_wear}%, Available: {self.m_available}, Recommended Session: {self.m_recommendedSession}, "
            f"Life Span: {self.m_lifeSpan}, Usable Life: {self.m_usableLife}, Lap Delta Time: {self.m_lapDeltaTime} ms, "
            f"Fitted: {self.m_fitted}"
        )

class PacketTyreSetsData:
    def __init__(self) -> None:
        self.m_header: PacketHeader = PacketHeader()
        self.m_carIdx: int = 0
        self.m_tyreSetData: List[TyreSetData] = []
        self.m_fittedIdx: int = 0

    def __str__(self) -> str:
        return (
            f"Header: {str(self.m_header)}, Car Index: {self.m_carIdx}, "
            f"Tyre Set Data: {[str(tyre_set_data) for tyre_set_data in self.m_tyreSetData]}, Fitted Index: {self.m_fittedIdx}"
        )

class PacketMotionExData:
    def __init__(self) -> None:
        self.m_header: PacketHeader = PacketHeader()
        self.m_suspensionPosition: List[float] = [0.0, 0.0, 0.0, 0.0]
        self.m_suspensionVelocity: List[float] = [0.0, 0.0, 0.0, 0.0]
        self.m_suspensionAcceleration: List[float] = [0.0, 0.0, 0.0, 0.0]
        self.m_wheelSpeed: List[float] = [0.0, 0.0, 0.0, 0.0]
        self.m_wheelSlipRatio: List[float] = [0.0, 0.0, 0.0, 0.0]
        self.m_wheelSlipAngle: List[float] = [0.0, 0.0, 0.0, 0.0]
        self.m_wheelLatForce: List[float] = [0.0, 0.0, 0.0, 0.0]
        self.m_wheelLongForce: List[float] = [0.0, 0.0, 0.0, 0.0]
        self.m_heightOfCOGAboveGround: float = 0.0
        self.m_localVelocityX: float = 0.0
        self.m_localVelocityY: float = 0.0
        self.m_localVelocityZ: float = 0.0
        self.m_angularVelocityX: float = 0.0
        self.m_angularVelocityY: float = 0.0
        self.m_angularVelocityZ: float = 0.0
        self.m_angularAccelerationX: float = 0.0
        self.m_angularAccelerationY: float = 0.0
        self.m_angularAccelerationZ: float = 0.0
        self.m_frontWheelsAngle: float = 0.0
        self.m_wheelVertForce: List[float] = [0.0, 0.0, 0.0, 0.0]

    def __str__(self) -> str:
        return (
            f"Header: {str(self.m_header)}, Suspension Position: {self.m_suspensionPosition}, "
            f"Suspension Velocity: {self.m_suspensionVelocity}, Suspension Acceleration: {self.m_suspensionAcceleration}, "
            f"Wheel Speed: {self.m_wheelSpeed}, Wheel Slip Ratio: {self.m_wheelSlipRatio}, Wheel Slip Angle: {self.m_wheelSlipAngle}, "
            f"Wheel Lat Force: {self.m_wheelLatForce}, Wheel Long Force: {self.m_wheelLongForce}, "
            f"Height of COG Above Ground: {self.m_heightOfCOGAboveGround}, Local Velocity (X, Y, Z): "
            f"({self.m_localVelocityX}, {self.m_localVelocityY}, {self.m_localVelocityZ}), "
            f"Angular Velocity (X, Y, Z): ({self.m_angularVelocityX}, {self.m_angularVelocityY}, {self.m_angularVelocityZ}), "
            f"Angular Acceleration (X, Y, Z): ({self.m_angularAccelerationX}, {self.m_angularAccelerationY}, {self.m_angularAccelerationZ}), "
            f"Front Wheels Angle: {self.m_frontWheelsAngle}, Wheel Vertical Force: {self.m_wheelVertForce}"
        )
