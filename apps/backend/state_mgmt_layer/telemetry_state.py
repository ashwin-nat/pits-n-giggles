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

import logging
from typing import Optional

from lib.inter_task_communicator import AsyncInterTaskCommunicator, ITCMessage, TyreDeltaNotificationMessageCollection
from lib.config import PngSettings

from .session_state import SessionState

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_session_state: Optional[SessionState] = None

# -------------------------------------- TELEMETRY PACKET HANDLERS -----------------------------------------------------

async def processCustomMarkerCreate() -> None:
    """Update the data structures with custom marker information
    """

    if custom_marker_obj := _session_state.getInsertCustomMarkerEntryObj():
        await AsyncInterTaskCommunicator().send("frontend-update", ITCMessage(
            m_message_type=ITCMessage.MessageType.CUSTOM_MARKER,
            m_message=custom_marker_obj))

async def processTyreDeltaSound() -> None:
    """Send the tyre delta notification to the frontend."""
    if messages := _session_state.getTyreDeltaNotificationMessages():
        await AsyncInterTaskCommunicator().send(
            "frontend-update",
            ITCMessage(
                m_message_type=ITCMessage.MessageType.TYRE_DELTA_NOTIFICATION_V2,
                m_message=TyreDeltaNotificationMessageCollection(messages)
            )
        )

# -------------------------------------- UTILTIES ----------------------------------------------------------------------

def isDriverIndexValid(index: int) -> bool:
    """Check if the given index is a valid driver index

    Args:
        index (int): Index of the driver

    Returns:
        bool: True if valid
    """

    return  (0 <= index < len(_session_state.m_driver_data)) and \
            (_session_state.m_driver_data[index] and _session_state.m_driver_data[index].is_valid)

def initSessionState(logger: logging.Logger, settings: PngSettings, ver_str: str) -> None:
    """Init the DriverData object

    Args:
        logger (logging.Logger): Logger
        settings (PngSettings): Settings
        ver_str (str): Version string
    """
    global _session_state
    _session_state = SessionState(
        logger,
        settings,
        ver_str
    )

def getSessionStateRef() -> SessionState:
    """Get the SessionState object reference

    Returns:
        SessionState: The SessionState object reference
    """
    global _session_state
    return _session_state
