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

from .base import MessageType, RaceCtrlMsgBase
from .driver_event_messages import (FastestLapRaceCtrlMsg, OvertakeRaceCtrlMsg,
                                    RetirementRaceCtrlMsg,
                                    SpeedTrapRaceCtrlMsg)
from .driver_status_messages import (CarDamageRaceCtrlMerssage,
                                     DriverPittingRaceCtrlMsg,
                                     TyreChangeRaceControlMessage,
                                     WingChangeRaceCtrlMsg)
from .incident_messages import (CollisionRaceCtrlMsg, DtPenServedRaceCtrlMsg,
                                PenaltyRaceCtrlMsg, SgPenServedRaceCtrlMsg)
from .session_messages import (ChequeredFlagRaceCtrlMsg,
                               DrsDisabledRaceCtrlMsg, DrsEnabledRaceCtrlMsg,
                               LightsOutRaceCtrlMsg, RaceWinnerRaceCtrlMsg,
                               RedFlagRaceCtrlMsg, SafetyCarRaceCtrlMsg,
                               SessionEndRaceCtrlMsg, SessionStartRaceCtrlMsg,
                               StartLightsRaceCtrlMsg)

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    # base
    "MessageType",
    "RaceCtrlMsgBase",

    # driver - event
    "FastestLapRaceCtrlMsg",
    "RetirementRaceCtrlMsg",
    "SpeedTrapRaceCtrlMsg",
    "OvertakeRaceCtrlMsg",

    # driver - status
    "DriverPittingRaceCtrlMsg",
    "CarDamageRaceCtrlMerssage",
    "WingChangeRaceCtrlMsg",
    "TyreChangeRaceControlMessage",

    # incident
    "CollisionRaceCtrlMsg",
    "PenaltyRaceCtrlMsg",
    "DtPenServedRaceCtrlMsg",
    "SgPenServedRaceCtrlMsg",

    # session
    "ChequeredFlagRaceCtrlMsg",
    "DrsDisabledRaceCtrlMsg",
    "DrsEnabledRaceCtrlMsg",
    "LightsOutRaceCtrlMsg",
    "RaceWinnerRaceCtrlMsg",
    "RedFlagRaceCtrlMsg",
    "SafetyCarRaceCtrlMsg",
    "SessionEndRaceCtrlMsg",
    "SessionStartRaceCtrlMsg",
    "StartLightsRaceCtrlMsg",
]
