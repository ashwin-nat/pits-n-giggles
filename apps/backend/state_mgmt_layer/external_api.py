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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import logging
from typing import TYPE_CHECKING

from lib.f1_types import PacketSessionData, SessionType, TrackID
from lib.openf1 import getMostRecentPoleLap

if TYPE_CHECKING:
    # Only for the type hint below - session_state.py imports this module's
    # handleExternalApiUpdate, so importing SessionState back here at runtime would be circular.
    from .session_state import SessionState

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def handleExternalApiUpdate(
        logger: logging.Logger,
        track_id: TrackID,
        session_type: SessionType,
        formula_type: PacketSessionData.FormulaType,
        session_state_ref: "SessionState") -> None:
    """One-shot external API lookup, fire_and_forget dispatched by SessionState whenever the
    session changes (see SessionState._notifyExternalApiTask).

    Args:
        logger (logging.Logger): Logger
        track_id (TrackID): The new session's track
        session_type (SessionType): The new session's type
        formula_type (PacketSessionData.FormulaType): The new session's formula type
        session_state_ref (SessionState): Reference to the session state, updated in place
    """

    if not formula_type.is_f1() or not session_type.isTimeTrialTypeSession():
        logger.debug("Skipping external API update as session is unsupported. "
                     "track=%s session_type=%s formula_type=%s", track_id, session_type, formula_type)
        pole_lap = None
    else:
        try:
            pole_lap = await getMostRecentPoleLap(track_id=track_id, logger=logger)
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Error fetching most recent pole lap: %s", e)
            pole_lap = None

    # No session-identity guard here: a session change takes seconds (loading screens etc.), far
    # longer than this lookup, so a stale write racing a newer session is not worth guarding against.
    session_state_ref.m_session_info.m_most_recent_pole_lap = pole_lap
