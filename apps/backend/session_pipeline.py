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

"""
SessionPipeline — one independent telemetry session.

Each pipeline owns:
- A SessionState       (state for all 22 drivers in this game instance)
- A F1TelemetryHandler (UDP receiver + packet parser)
- Associated asyncio tasks (telemetry receive loop, watchdog)

The pipeline does NOT own the web server or IPC publisher — those are
shared across all sessions by PngRunner.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import asyncio
import logging
from typing import List

from apps.backend.state_mgmt_layer import SessionState, initStateManagementLayer
from apps.backend.telemetry_layer import F1TelemetryHandler, initTelemetryLayer
from lib.config import PngSettings

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class SessionPipeline:
    """One independent telemetry session: UDP receiver → parser → state.

    Attributes:
        session_state: The session state holding all driver data.
        telemetry_handler: The telemetry handler receiving and parsing UDP packets.
        http_port: The HTTP port this session is served on.
        telemetry_port: The UDP port this session listens on.
        label: Human-readable label for this session.
        is_primary: True for the main pipeline (runs the forwarder).
        tasks: asyncio tasks owned by this pipeline.
    """

    def __init__(
        self,
        settings: PngSettings,
        logger: logging.Logger,
        ver_str: str,
        shutdown_event: asyncio.Event,
        replay_server: bool,
        http_port: int,
        telemetry_port: int,
        label: str,
        tasks: List[asyncio.Task],
        is_primary: bool = True,
    ) -> None:
        """Initialize one telemetry session pipeline.

        Args:
            settings: Application settings (used for non-port config like capture, forwarding, etc.)
            logger: Logger instance.
            ver_str: Version string.
            shutdown_event: Shared shutdown event.
            replay_server: If True, use TCP replay mode instead of live UDP.
            http_port: The HTTP port this session will be served on.
            telemetry_port: The UDP telemetry port to listen on.
            label: Human-readable session label.
            tasks: Shared task list — pipeline appends its own tasks here.
            is_primary: If True, run the UDP forwarder in this pipeline.
        """
        self.http_port: int = http_port
        self.telemetry_port: int = telemetry_port
        self.label: str = label
        self.is_primary: bool = is_primary

        # ITC queue suffix — empty for primary (backward-compat), ":PORT" for additional
        self.itc_queue_suffix: str = "" if is_primary else f":{telemetry_port}"

        # Override the telemetry port in settings so downstream code
        # (F1TelemetryHandler → AsyncF1TelemetryManager) binds the correct UDP port.
        effective_settings = settings
        if telemetry_port != settings.Network.telemetry_port:
            effective_settings = settings.model_copy(
                update={"Network": settings.Network.model_copy(update={"telemetry_port": telemetry_port})}
            )

        self.session_state: SessionState = initStateManagementLayer(
            logger=logger,
            settings=effective_settings,
            ver_str=ver_str,
            tasks=tasks,
            shutdown_event=shutdown_event,
            itc_queue_suffix=self.itc_queue_suffix,
        )

        self.telemetry_handler: F1TelemetryHandler = initTelemetryLayer(
            settings=effective_settings,
            replay_server=replay_server,
            logger=logger,
            ver_str=ver_str,
            shutdown_event=shutdown_event,
            session_state=self.session_state,
            tasks=tasks,
            is_primary=is_primary,
            itc_queue_suffix=self.itc_queue_suffix,
        )

    async def stop(self) -> None:
        """Stop the telemetry handler for this pipeline."""
        await self.telemetry_handler.stop()
