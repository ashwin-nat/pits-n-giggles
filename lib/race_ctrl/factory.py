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

from .messages import (ChequeredFlagRaceCtrlMsg, CollisionRaceCtrlMsg,
                       DriverPittingRaceCtrlMsg, DrsDisabledRaceCtrlMsg,
                       DrsEnabledRaceCtrlMsg, DtPenServedRaceCtrlMsg,
                       FastestLapRaceCtrlMsg, LightsOutRaceCtrlMsg,
                       OvertakeRaceCtrlMsg, PenaltyRaceCtrlMsg,
                       RaceCtrlMsgBase, RaceWinnerRaceCtrlMsg,
                       RedFlagRaceCtrlMsg, RetirementRaceCtrlMsg,
                       SafetyCarRaceCtrlMsg, SessionEndRaceCtrlMsg,
                       SessionStartRaceCtrlMsg, SgPenServedRaceCtrlMsg,
                       SpeedTrapRaceCtrlMsg, StartLightsRaceCtrlMsg)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

def race_ctrl_event_msg_factory(packet: PacketEventData, lap_number: int) -> Optional[RaceCtrlMsgBase]:
    """Create a race control message from a packet

    Args:
        packet (PacketEventData): Packet event data
        lap_number (int): Lap number

    Returns:
        Optional[RaceCtrlMsgBase]: Race control message
    """
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

        case PacketEventData.EventPacketType.CHEQUERED_FLAG:
            return ChequeredFlagRaceCtrlMsg(timestamp=time.time(), lap_number=lap_number)

        case PacketEventData.EventPacketType.RACE_WINNER:
            race_winner: PacketEventData.RaceWinner = packet.mEventDetails
            return RaceWinnerRaceCtrlMsg(timestamp=time.time(), winner_index=race_winner.vehicleIdx,
                                         lap_number=lap_number)

        case PacketEventData.EventPacketType.PENALTY_ISSUED:
            penalty: PacketEventData.Penalty = packet.mEventDetails
            return PenaltyRaceCtrlMsg(timestamp=time.time(), penalty_type=str(penalty.penaltyType),
                                      infringement_type=str(penalty.infringementType), vehicle_index=penalty.vehicleIdx,
                                      other_vehicle_index=penalty.otherVehicleIdx,
                                      time=penalty.time, places_gained=penalty.placesGained, lap_number=penalty.lapNum)

        case PacketEventData.EventPacketType.SPEED_TRAP_TRIGGERED:
            speed_trap: PacketEventData.SpeedTrap = packet.mEventDetails
            return SpeedTrapRaceCtrlMsg(timestamp=time.time(), driver_index=speed_trap.vehicleIdx,
                                        speed=speed_trap.speed, is_session_fastest=speed_trap.isOverallFastestInSession,
                                        is_personal_fastest=speed_trap.isDriverFastestInSession,
                                        fastest_index=speed_trap.fastestVehicleIdxInSession,
                                        session_fastest=speed_trap.fastestSpeedInSession, lap_number=lap_number)

        case PacketEventData.EventPacketType.START_LIGHTS:
            start_lights: PacketEventData.StartLights = packet.mEventDetails
            return StartLightsRaceCtrlMsg(timestamp=time.time(), num_lights=start_lights.numLights,
                                          lap_number=lap_number)

        case PacketEventData.EventPacketType.LIGHTS_OUT:
            return LightsOutRaceCtrlMsg(timestamp=time.time(), lap_number=lap_number)

        case PacketEventData.EventPacketType.DRIVE_THROUGH_SERVED:
            dt_pen_served: PacketEventData.DriveThroughPenaltyServed = packet.mEventDetails
            return DtPenServedRaceCtrlMsg(timestamp=time.time(), driver_index=dt_pen_served.vehicleIdx,
                                          lap_number=lap_number)

        case PacketEventData.EventPacketType.STOP_GO_SERVED:
            sg_pen_served: PacketEventData.StopGoPenaltyServed = packet.mEventDetails
            return SgPenServedRaceCtrlMsg(timestamp=time.time(), driver_index=sg_pen_served.vehicleIdx,
                                          stop_time=sg_pen_served.stopTime, lap_number=lap_number)

        case PacketEventData.EventPacketType.RED_FLAG:
            return RedFlagRaceCtrlMsg(timestamp=time.time(), lap_number=lap_number)

        case PacketEventData.EventPacketType.OVERTAKE:
            overtake: PacketEventData.Overtake = packet.mEventDetails
            return OvertakeRaceCtrlMsg(timestamp=time.time(), overtaker_index=overtake.overtakingVehicleIdx,
                                       overtaken_index=overtake.beingOvertakenVehicleIdx, lap_number=lap_number)

        case PacketEventData.EventPacketType.SAFETY_CAR:
            safety_car: PacketEventData.SafetyCarEvent = packet.mEventDetails
            return SafetyCarRaceCtrlMsg(timestamp=time.time(), sc_type=str(safety_car.m_safety_car_type),
                                        event_type=str(safety_car.m_event_type), lap_number=lap_number)

        case PacketEventData.EventPacketType.COLLISION:
            collision: PacketEventData.Collision = packet.mEventDetails
            return CollisionRaceCtrlMsg(timestamp=time.time(), involved_drivers=[collision.m_vehicle_1_index,
                                                                                collision.m_vehicle_2_index],
                                        lap_number=lap_number)

        case _:
            return None
