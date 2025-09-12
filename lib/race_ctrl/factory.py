# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

import time
from typing import Optional

from lib.f1_types import PacketEventData

from .messages import (CollisionRaceCtrlMsg, DrsDisabledRaceCtrlMsg,
                       DrsEnabledRaceCtrlMsg, FastestLapRaceCtrlMsg,
                       OvertakeRaceCtrlMsg, RaceCtrlMsgBase,
                       RetirementRaceCtrlMsg, SessionEndRaceCtrlMsg,
                       SessionStartRaceCtrlMsg)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

def race_ctrl_msg_factory(packet: PacketEventData, lap_number: int) -> Optional[RaceCtrlMsgBase]:

    match packet.m_eventCode:
        case PacketEventData.EventPacketType.SESSION_STARTED:
            return SessionStartRaceCtrlMsg(timestamp=time.time(), lap_number=lap_number)

        case PacketEventData.EventPacketType.SESSION_ENDED:
            return SessionEndRaceCtrlMsg(timestamp=time.time(), lap_number=lap_number)

        case PacketEventData.EventPacketType.FASTEST_LAP:
            fastest_lap: PacketEventData.FastestLap = packet.mEventDetails
            return FastestLapRaceCtrlMsg(timestamp=time.time(), driver_index=fastest_lap.vehicleIdx,
                                         lap_time_ms=int(fastest_lap.lapTime * 1000), lap_number=lap_number)

        case PacketEventData.EventPacketType.RETIREMENT:
            retirement: PacketEventData.Retirement = packet.mEventDetails
            return RetirementRaceCtrlMsg(timestamp=time.time(), driver_index=retirement.vehicleIdx,
                                         reason=str(retirement.m_reason), lap_number=lap_number)

        case PacketEventData.EventPacketType.DRS_ENABLED:
            return DrsEnabledRaceCtrlMsg(timestamp=time.time(), lap_number=lap_number)

        case PacketEventData.EventPacketType.DRS_DISABLED:
            drs_disabled: PacketEventData.DrsDisabled = packet.mEventDetails
            return DrsDisabledRaceCtrlMsg(timestamp=time.time(), reason=str(drs_disabled.m_reason),
                                          lap_number=lap_number)

        case PacketEventData.EventPacketType.OVERTAKE:
            overtake: PacketEventData.Overtake = packet.mEventDetails
            return OvertakeRaceCtrlMsg(timestamp=time.time(), overtaker_index=overtake.overtakingVehicleIdx,
                                       overtaken_index=overtake.beingOvertakenVehicleIdx, lap_number=lap_number)

        case PacketEventData.EventPacketType.COLLISION:
            collision: PacketEventData.Collision = packet.mEventDetails
            return CollisionRaceCtrlMsg(timestamp=time.time(), involved_drivers=[collision.m_vehicle_1_index,
                                                                                collision.m_vehicle_2_index],
                                        lap_number=lap_number)

        case PacketEventData.EventPacketType.FLASHBACK:
            return None
        case PacketEventData.EventPacketType.START_LIGHTS:
            return None
        case _:
            return None
