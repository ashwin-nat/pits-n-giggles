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
from functools import partial
from typing import List

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.telemetry_layer import F1TelemetryHandler
from lib.ipc import IpcServerAsync
from lib.child_proc_mgmt import report_ipc_port_from_child

from .command_dispatcher import processIpcCommand
from .command_handlers import handleHeartbeatMissed, handleShutdown

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def registerIpcTask(
        run_ipc_server: bool,
        logger: logging.Logger,
        session_state: SessionState,
        telemetry_handler: F1TelemetryHandler,
        tasks: List[asyncio.Task]
        ) -> None:
    """Register the IPC task

    Args:
        run_ipc_server (bool): Whether to run the IPC server
        logger (logging.Logger): Logger
        session_state (SessionState): Handle to the session state object
        telemetry_handler (F1TelemetryHandler): Telemetry handler
        tasks (List[asyncio.Task]): List of tasks
    """

    # Register the IPC task only if port is specified
    if run_ipc_server:
        logger.debug("Starting IPC server")
        server = IpcServerAsync(name="Backend")
        report_ipc_port_from_child(server.port)
        logger.debug("Started IPC server on port %d", server.port)
        server.register_shutdown_callback(partial(handleShutdown, logger=logger, telemetry_handler=telemetry_handler))
        server.register_heartbeat_missed_callback(partial(handleHeartbeatMissed, logger=logger))
        tasks.append(asyncio.create_task(server.run(partial(
            processIpcCommand, logger=logger, session_state=session_state, telemetry_handler=telemetry_handler)),
                name="IPC Task"))

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "registerIpcTask",
]
