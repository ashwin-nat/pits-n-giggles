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

from dataclasses import dataclass
from typing import Optional

from lib.f1_types import (CarDamageData, CarMotionData, CarSetupData,
                          CarStatusData, CarTelemetryData,
                          FinalClassificationData, LapData,
                          PacketSessionHistoryData, PacketTyreSetsData,
                          ParticipantData)

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass(slots=True)
class PacketCopies:
    """
    Class holding copies of various telemetry and status packets for a driver.

    Attributes:
        m_packet_lap_data (Optional[LapData]): Copy of the LapData packet.
        m_packet_particpant_data (Optional[ParticipantData]): Copy of the ParticipantData packet.
        m_packet_car_telemetry (Optional[CarTelemetryData]): Copy of the CarTelemetryData packet.
        m_packet_car_status (Optional[CarStatusData]): Copy of the CarStatusData packet.
        m_packet_car_damage (Optional[CarDamageData]): Copy of the CarDamageData packet.
        m_packet_session_history (Optional[PacketSessionHistoryData]): Copy of the PacketSessionHistoryData packet.
        m_packet_tyre_sets (Optional[PacketTyreSetsData]): Copy of the PacketTyreSetsData packet.
        m_packet_final_classification (Optional[FinalClassificationData]): Copy of the FinalClassificationData packet.
        m_packet_motion (Optional[CarMotionData]): Copy of the CarMotionData packet.
        m_packet_car_setup (Optional[CarSetupData]): Copy of the CarSetupData packet.
    """
    m_packet_lap_data: Optional[LapData] = None
    m_packet_particpant_data: Optional[ParticipantData] = None
    m_packet_car_telemetry: Optional[CarTelemetryData] = None
    m_packet_car_status: Optional[CarStatusData] = None
    m_packet_car_damage: Optional[CarDamageData] = None
    m_packet_session_history: Optional[PacketSessionHistoryData] = None
    m_packet_tyre_sets: Optional[PacketTyreSetsData] = None
    m_packet_final_classification: Optional[FinalClassificationData] = None
    m_packet_motion: Optional[CarMotionData] = None
    m_packet_car_setup: Optional[CarSetupData] = None
