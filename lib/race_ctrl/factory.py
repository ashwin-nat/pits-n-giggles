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
from lib.f1_types import PacketEventData
from typing import Optional
from .messages import RaceCtrlMsgBase, SessionStartRaceCtrlMsg

# -------------------------------------- CLASSES -----------------------------------------------------------------------

def race_ctrl_msg_factory(packet: PacketEventData, lap_number: int) -> Optional[RaceCtrlMsgBase]:

    match packet.m_eventCode:
        case PacketEventData.EventPacketType.SESSION_STARTED:
            return SessionStartRaceCtrlMsg(timestamp=time.time(), lap_number=lap_number)

        case PacketEventData.EventPacketType.FASTEST_LAP:
            return None
        case PacketEventData.EventPacketType.SESSION_STARTED:
            return None
        case PacketEventData.EventPacketType.RETIREMENT:
            return None
        case PacketEventData.EventPacketType.OVERTAKE:
            return None
        case PacketEventData.EventPacketType.COLLISION:
            return None
        case PacketEventData.EventPacketType.FLASHBACK:
            return None
        case PacketEventData.EventPacketType.START_LIGHTS:
            return None
        case _:
            return None