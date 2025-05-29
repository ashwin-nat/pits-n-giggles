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

from .tests_packet_0_car_motion_data import TestPacketCarMotionData
from .tests_packet_1_session_data import TestPacketSessionData
from .tests_packet_2_lap_data import TestPacketLapData
from .tests_packet_3_event_data import TestPacketEventData
from .tests_packet_4_participants_data import TestPacketParticipantsData
from .tests_packet_5_car_setups_data import TestPacketCarSetupData
from .tests_packet_6_car_telemetry_data import TestPacketCarTelemetryData
from .tests_packet_7_status_data import TestPacketCarStatusData
from .tests_packet_8_final_classification import TestPacketFinalClassificationData
from .tests_packet_9_lobby_info_data import TestPacketLobbyInfoData
from .tests_packet_10_car_damage_data import TestPacketCarDamageData
from .tests_packet_11_session_history_data import TestPacketSessionHistoryData
from .tests_packet_12_tyre_sets_data import TestPacketTyreSetsData
from .tests_packet_13_motion_ex_data import TestPacketMotionExData
from .tests_packet_14_time_trial_data import TestPacketTimeTrialData
from .tests_packet_15_lap_positions_data import TestPacketLapPositionsData

__all__ = [
    'TestPacketCarMotionData',
    'TestPacketSessionData',
    'TestPacketLapData',
    'TestPacketEventData',
    'TestPacketParticipantsData',
    'TestPacketCarSetupData',
    'TestPacketCarTelemetryData',
    'TestPacketCarStatusData',
    'TestPacketFinalClassificationData',
    'TestPacketLobbyInfoData',
    'TestPacketCarDamageData',
    'TestPacketSessionHistoryData',
    'TestPacketTyreSetsData',
    'TestPacketMotionExData',
    'TestPacketTimeTrialData',
    'TestPacketLapPositionsData',
]