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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import logging

from lib.config import PngSettings
from lib.f1_types import PacketSessionData, SessionType, TrackID
from lib.subsystem import AsyncSubsystem

from .session_state import SessionState
from .external_api import handleExternalApiUpdate

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initStateManagementLayer(
    logger: logging.Logger,
    settings: PngSettings,
    ver_str: str,
    subsystem: AsyncSubsystem) -> SessionState:
    """Initialise the state management layer

    Args:
        logger (logging.Logger): Logger
        settings (PngSettings): Settings
        ver_str (str): Version string
        subsystem (AsyncSubsystem): The backend subsystem - used for fire_and_forget, to
            dispatch the (I/O-bound) external API lookup in the background whenever the
            session changes

    Returns:
        SessionState: Handle to the session state data structure
    """

    def notify_external_api(
            track_id: TrackID, session_type: SessionType,
            formula_type: PacketSessionData.FormulaType) -> None:
        subsystem.fire_and_forget(
            handleExternalApiUpdate(logger, track_id, session_type, formula_type, ref),
            name="External API Update")

    ref = SessionState(logger, settings, ver_str, notify_external_api=notify_external_api)
    return ref
