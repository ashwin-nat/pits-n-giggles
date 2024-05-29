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

from .common import (
    InvalidPacketLengthError,
    F1PacketType,
    ResultStatus,
    SessionType23,
    SessionType24,
    ActualTyreCompound,
    VisualTyreCompound,
    SafetyCarType,
    TelemetrySetting,
    Nationality,
    Platform,
    TeamID,
    F1Utils,
    PacketHeader,
    TrackID,
    TractionControlAssistMode,
    GearboxAssistMode,
    SessionLength,
)
from .packet_0_car_motion_data import PacketMotionData, CarMotionData
from .packet_1_session_data import MarshalZone, WeatherForecastSample, PacketSessionData
from .packet_2_lap_data import LapData, PacketLapData
from .packet_3_event_data import PacketEventData
from .packet_4_participants_data import PacketParticipantsData, ParticipantData
from .packet_5_car_setups_data import PacketCarSetupData, CarSetupData
from .packet_6_car_telemetry_data import PacketCarTelemetryData, CarTelemetryData
from .packet_7_car_status_data import PacketCarStatusData, CarStatusData
from .packet_8_final_classification_data import PacketFinalClassificationData, FinalClassificationData
from .packet_9_lobby_info_data import PacketLobbyInfoData, LobbyInfoData
from .packet_10_car_damage_data import PacketCarDamageData, CarDamageData
from .packet_11_session_history_data import PacketSessionHistoryData, TyreStintHistoryData, LapHistoryData
from .packet_12_tyre_sets_packet import PacketTyreSetsData, TyreSetData
from .packet_13_motion_ex_data import PacketMotionExData
from .packet_14_time_trial_data import PacketTimeTrialData, TimeTrialDataSet

# Import other packet classes here
__all__ = [
    # Common Stuff
    "InvalidPacketLengthError",
    "F1PacketType",
    "ResultStatus",
    "SessionType23",
    "SessionType24",
    "ActualTyreCompound",
    "VisualTyreCompound",
    "SafetyCarType",
    "TelemetrySetting",
    "Nationality",
    "Platform",
    "TeamID",
    "F1Utils",
    "PacketHeader",
    "TrackID",
    "TractionControlAssistMode",
    "GearboxAssistMode",
    "SessionLength",

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
    "TimeTrialDataSet"
]