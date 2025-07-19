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


from .common import (ActualTyreCompound, F1PacketType, F1Utils, GameMode,
                     GearboxAssistMode, InvalidPacketLengthError, Nationality,
                     PacketCountValidationError, PacketHeader,
                     PacketParsingError, Platform, ResultReason, ResultStatus,
                     SafetyCarType, SessionLength, SessionType23,
                     SessionType24, TeamID23, TeamID24, TeamID25,
                     TelemetrySetting, TrackID, TractionControlAssistMode,
                     VisualTyreCompound)
from .packet_0_car_motion_data import CarMotionData, PacketMotionData
from .packet_1_session_data import (MarshalZone, PacketSessionData,
                                    WeatherForecastSample)
from .packet_2_lap_data import LapData, PacketLapData
from .packet_3_event_data import PacketEventData
from .packet_4_participants_data import (LiveryColour, PacketParticipantsData,
                                         ParticipantData)
from .packet_5_car_setups_data import CarSetupData, PacketCarSetupData
from .packet_6_car_telemetry_data import (CarTelemetryData,
                                          PacketCarTelemetryData)
from .packet_7_car_status_data import CarStatusData, PacketCarStatusData
from .packet_8_final_classification_data import (FinalClassificationData,
                                                 PacketFinalClassificationData)
from .packet_9_lobby_info_data import LobbyInfoData, PacketLobbyInfoData
from .packet_10_car_damage_data import CarDamageData, PacketCarDamageData
from .packet_11_session_history_data import (LapHistoryData,
                                             PacketSessionHistoryData,
                                             TyreStintHistoryData)
from .packet_12_tyre_sets_packet import PacketTyreSetsData, TyreSetData
from .packet_13_motion_ex_data import PacketMotionExData
from .packet_14_time_trial_data import PacketTimeTrialData, TimeTrialDataSet
from .packet_15_lap_positions_data import PacketLapPositionsData

# Import other packet classes here
__all__ = [
    # Common Stuff
    "InvalidPacketLengthError",
    "PacketParsingError",
    "PacketCountValidationError",
    "F1PacketType",
    "ResultStatus",
    "ResultReason",
    "SessionType23",
    "SessionType24",
    "ActualTyreCompound",
    "VisualTyreCompound",
    "SafetyCarType",
    "TelemetrySetting",
    "Nationality",
    "Platform",
    "TeamID23",
    "TeamID24",
    "TeamID25",
    "F1Utils",
    "PacketHeader",
    "TrackID",
    "TractionControlAssistMode",
    "GearboxAssistMode",
    "SessionLength",
    "GameMode",

    # Packet 0 - car motion
    "PacketMotionData",
    "CarMotionData",

    # Packet 1 - session data
    "MarshalZone",
    "WeatherForecastSample",
    "PacketSessionData",

    # Packet 2 - lap data
    "LapData",
    "PacketLapData",

    # Packet 3 - event data
    "PacketEventData",

    # Packet 4 - Participants Data
    "LiveryColour",
    "PacketParticipantsData",
    "ParticipantData",

    # Packet 5 - Car Setups
    "PacketCarSetupData",
    "CarSetupData",

    # Packet 6 - Car telemetry
    "PacketCarTelemetryData",
    "CarTelemetryData",

    # Packet 7 - Car status
    "PacketCarStatusData",
    "CarStatusData",

    # Packet 8 - Final Classification
    "PacketFinalClassificationData",
    "FinalClassificationData",

    # Packet 9 - Lobby Info
    "PacketLobbyInfoData",
    "LobbyInfoData",

    # Packet 10 - Car Damage
    "PacketCarDamageData",
    "CarDamageData",

    # Packet 11 - Session History
    "PacketSessionHistoryData",
    "LapHistoryData",
    "TyreStintHistoryData",

    # Packet 12 - Tyre sets
    "PacketTyreSetsData",
    "TyreSetData",

    # Packet 13 - Motion Ex
    "PacketMotionExData",

    # Packet 14 - Time Trial
    "PacketTimeTrialData",
    "TimeTrialDataSet",

    # Packet 15 - Lap positions
    "PacketLapPositionsData",
]
