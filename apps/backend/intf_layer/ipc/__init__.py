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

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.telemetry_layer import F1TelemetryHandler
from lib.ipc import IpcServerAsync, IpcPublisherAsync
from lib.child_proc_mgmt import report_ipc_port_from_child

from .command_handlers import (handleGetStats, handleManualSave, handleHeartbeatMissed, handleShutdown,
                               handleUdpActionCodeChange)
from ..telemetry_web_server import TelemetryWebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def registerIpcTask(
        run_ipc_server: bool,
        logger: logging.Logger,
        session_state: SessionState,
        telemetry_handler: F1TelemetryHandler,
        ipc_pub: IpcPublisherAsync,
        web_server: TelemetryWebServer,
        tasks: List[asyncio.Task]
        ) -> None:
    """Register the IPC task

    Args:
        run_ipc_server (bool): Whether to run the IPC server
        logger (logging.Logger): Logger
        session_state (SessionState): Handle to the session state object
        telemetry_handler (F1TelemetryHandler): Telemetry handler
        ipc_pub (IpcPublisherAsync): IPC publisher
        web_server (TelemetryWebServer): Telemetry web server
        tasks (List[asyncio.Task]): List of tasks
    """

    # Register the IPC task only if port is specified
    if not run_ipc_server:
        return

    logger.debug("Starting IPC server")
    server = IpcServerAsync(name="Backend")
    report_ipc_port_from_child(server.port)
    logger.debug("Started IPC server on port %d", server.port)

    @server.on_heartbeat_missed
    async def _handle_heartbeat_missed(count: int):
        return await handleHeartbeatMissed(count, logger=logger)

    @server.on_shutdown
    async def _handle_shutdown(args: dict):
        return await handleShutdown(args, logger=logger)

    @server.on("manual-save")
    async def _handle_manual_save(_args: dict):
        return await handleManualSave(logger=logger, session_state=session_state)

    @server.on("udp-action-code-change")
    async def _handle_udp_action_code_change(args: dict):
        return await handleUdpActionCodeChange(args, logger, telemetry_handler)

    @server.on_get_stats
    async def _handle_get_stats(_args: dict):
        return await handleGetStats(telemetry_handler, ipc_pub, web_server)

    tasks.append(asyncio.create_task(server.run(), name="IPC Server"))

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "registerIpcTask",
]
