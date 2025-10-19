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

import asyncio
import logging
from typing import List, Optional

from lib.inter_task_communicator import AsyncInterTaskCommunicator, SessionChangeNotification
from lib.openf1 import getMostRecentPoleLap

from .telemetry_state import SessionState

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initExternalApiTask(
    tasks: List[asyncio.Task],
    shutdown_event: asyncio.Event,
    session_state_ref: SessionState) -> None:
    """Initialise the state management layer

    Args:
        tasks (List[asyncio.Task]): List of tasks
        shutdown_event (asyncio.Event): Shutdown event
        session_state_ref (SessionState): Reference to the session state
    """
    tasks.append(asyncio.create_task(externalApiTask(shutdown_event, session_state_ref), name="External API Task"))

async def externalApiTask(
        shutdown_event: asyncio.Event,
        session_state_ref: SessionState) -> None:
    """The actual task that calls the external API's

    Args:
        shutdown_event (asyncio.Event): Shutdown event
        session_state_ref (SessionState): Reference to the session state
    """

    logger = logging.getLogger('png')

    while not shutdown_event.is_set():
        message: Optional[SessionChangeNotification] = await AsyncInterTaskCommunicator().receive("external-api-update")
        if message:
            if not message.m_formula_type.is_f1() or not message.m_session_type.isTimeTrialTypeSession():
                logger.debug("Skipping external API update as session is unsupported. %s", message)
                pole_lap = None
            else:
                try:
                    pole_lap = await getMostRecentPoleLap(track_id=message.m_trackID, logger=logger)
                except Exception as e: # pylint: disable=broad-exception-caught
                    logger.error(f"Error fetching most recent pole lap: {e}")
                    pole_lap = None
            session_state_ref.m_session_info.m_most_recent_pole_lap = pole_lap

    logger.debug("Shutting down External API task...")
