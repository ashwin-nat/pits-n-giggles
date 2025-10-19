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

import asyncio
import logging
from typing import List

from lib.config import PngSettings

from .telemetry_forwarder import setupForwarder
from .telemetry_handler import F1TelemetryHandler, setupTelemetryTask
from apps.backend.state_mgmt_layer import SessionState

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initTelemetryLayer(
        settings: PngSettings,
        replay_server: bool,
        logger: logging.Logger,
        ver_str: str,
        shutdown_event: asyncio.Event,
        session_state: SessionState,
        tasks: List[asyncio.Task]) -> F1TelemetryHandler:
    """Initialize the telemetry layer

    Args:
        settings (PngSettings): Png settings
        replay_server (bool): Whether to enable the TCP replay debug server.
        logger (logging.Logger): Logger instance
        ver_str (str): Version string
        shutdown_event (asyncio.Event): Shutdown event
        session_state (SessionState): Handle to the session state
        tasks (List[asyncio.Task]): List of tasks to be executed

    Returns:
        F1TelemetryHandler: Telemetry handler
    """

    handler = setupTelemetryTask(
        settings=settings,
        replay_server=replay_server,
        session_state=session_state,
        logger=logger,
        ver_str=ver_str,
        tasks=tasks
    )
    setupForwarder(
        forwarding_targets=settings.Forwarding.forwarding_targets,
        tasks=tasks,
        shutdown_event=shutdown_event,
        logger=logger
    )
    return handler
