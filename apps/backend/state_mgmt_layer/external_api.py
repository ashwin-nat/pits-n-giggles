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
from typing import List

from lib.inter_task_communicator import AsyncInterTaskCommunicator

from .telemetry_state import SessionState

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initExternalApiTask(
    logger: logging.Logger,
    tasks: List[asyncio.Task],
    shutdown_event: asyncio.Event,
    session_state_ref: SessionState) -> None:
    """Initialise the state management layer

    Args:
        logger (logging.Logger): Logger
        tasks (List[asyncio.Task]): List of tasks
        shutdown_event (asyncio.Event): Shutdown event
        session_state_ref (SessionState): Reference to the session state
    """
    tasks.append(asyncio.create_task(externalApiTask(logger, shutdown_event, session_state_ref), name="External API Task"))

async def externalApiTask(logger: logging.Logger, shutdown_event: asyncio.Event, session_state_ref: SessionState) -> None:
    """The actual task that calls the external API's

    Args:
        logger (logging.Logger): Logger
        shutdown_event (asyncio.Event): Shutdown event
        session_state_ref (SessionState): Reference to the session state
    """

    while not shutdown_event.is_set():
        if message := await AsyncInterTaskCommunicator().receive("external-api-update"):
            logger.info(f"External API update: {message}")
            # TODO: Call the external API

    logger.debug("Shutting down External API task...")
