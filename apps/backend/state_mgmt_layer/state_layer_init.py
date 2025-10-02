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

import asyncio
import logging
from typing import List

from lib.config import PngSettings

from .telemetry_state import initSessionState
from .telemetry_web_api import initPngApiLayer
from .external_api import initExternalApiTask

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initStateManagementLayer(
    logger: logging.Logger,
    settings: PngSettings,
    ver_str: str,
    tasks: List[asyncio.Task],
    shutdown_event: asyncio.Event) -> None:
    """Initialise the state management layer

    Args:
        logger (logging.Logger): Logger
        settings (PngSettings): Settings
        ver_str (str): Version string
        tasks (List[asyncio.Task]): List of tasks
        shutdown_event (asyncio.Event): Shutdown event
    """
    ref = initSessionState(logger=logger, settings=settings, ver_str=ver_str)
    initPngApiLayer(logger=logger, session_state_ref=ref)
    initExternalApiTask(logger=logger, tasks=tasks, shutdown_event=shutdown_event, session_state_ref=ref)
