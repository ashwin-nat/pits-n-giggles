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
from typing import List, Optional, Tuple

from lib.config import CaptureSettings

from .telemetry_forwarder import setupForwarder
from .telemetry_handler import setupTelemetryTask

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initTelemetryLayer(
        port_number: int,
        replay_server: bool,
        logger: logging.Logger,
        capture_settings: CaptureSettings,
        udp_custom_action_code: Optional[int],
        udp_tyre_delta_action_code: Optional[int],
        forwarding_targets: List[Tuple[str, int]],
        ver_str: str,
        tasks: List[asyncio.Task]) -> None:
    """Initialize the telemetry layer

    Args:
        port_number (int): Port number for the telemetry client.
        replay_server (bool): Whether to enable the TCP replay debug server.
        logger (logging.Logger): Logger instance
        capture_settings (CaptureSettings): Capture settings
        udp_custom_action_code (Optional[int]): UDP custom action code.
        udp_tyre_delta_action_code (Optional[int]): UDP tyre delta action code.
        forwarding_targets (List[Tuple[str, int]]): List of IP addr port pairs to forward packets to
        ver_str (str): Version string
        tasks (List[asyncio.Task]): List of tasks to be executed
    """

    setupTelemetryTask(
        port_number=port_number,
        replay_server=replay_server,
        logger=logger,
        capture_settings=capture_settings,
        udp_custom_action_code=udp_custom_action_code,
        udp_tyre_delta_action_code=udp_tyre_delta_action_code,
        forwarding_targets=forwarding_targets,
        ver_str=ver_str,
        tasks=tasks
    )
    setupForwarder(
        forwarding_targets=forwarding_targets,
        tasks=tasks,
        logger=logger
    )
