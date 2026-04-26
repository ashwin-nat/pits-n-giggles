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
import os
import webbrowser
from typing import Any, Dict, List

import apps.save_viewer.save_viewer_state as SaveViewerState
from apps.save_viewer.save_web_server import SaveViewerWebServer
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.child_proc_mgmt import report_ipc_port_from_child
from lib.ipc import IpcServerAsync
from lib.web_server import ClientType

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SaveViewerIpc:
    def __init__(self, logger: logging.Logger, server: SaveViewerWebServer) -> None:
        """Initialize the IPC server.

        Args:
            logger (logging.Logger): Logger
            server (SaveViewerWebServer): Web server
        """
        self.m_logger = logger
        self.m_server = server
        self.m_should_open_ui = True
        self.m_ipc_server = IpcServerAsync(name="Save Viewer")
        self._register_routes()
        report_ipc_port_from_child(self.m_ipc_server.port)

    async def run(self) -> None:
        """Starts the IPC server."""
        await self.m_ipc_server.run()

    def _register_routes(self):
        """Registers routes for the IPC server."""

        @self.m_ipc_server.on_heartbeat_missed
        async def _heartbeat_missed_handler(count: int) -> dict:
            """Handle terminate command"""

            print(f"[SAVE_VIEWER] Missed heartbeat {count} times. "
                  "This process has probably been orphaned. Terminating...")
            # os._exit required: child process must terminate immediately without
            # running atexit handlers or flushing stdio buffers from parent.
            os._exit(PNG_LOST_CONN_TO_PARENT)

        @self.m_ipc_server.on_shutdown
        async def _shutdown_handler(args: dict) -> Dict[str, Any]:
            """Shutdown handler function.

            Args:
                args (dict): IPC command arguments

            Returns:
                Dict[str, Any]: Shutdown response
            """
            reason = args["reason"]
            self.m_logger.info("Shutting down. Reason: %s", reason)
            await self.m_server.stop()
            return {"status": "success"}

        @self.m_ipc_server.on("open-file")
        async def _handle_open_file(args: dict) -> dict:
            """Handles the 'open-file' IPC command."""
            file_path = args.get("file-path")

            result = await SaveViewerState.open_file_helper(file_path)
            if result.get("status") != "success":
                return result

            # Open the webpage once
            if self.m_should_open_ui:
                self.m_should_open_ui = False
                webbrowser.open(f'http://localhost:{self.m_server.m_port}', new=2)

            # Update all clients
            await self.m_server.send_to_clients_of_type(
                event='race-table-update',
                data=SaveViewerState.getTelemetryInfo(),
                client_type=ClientType.RACE_TABLE,
            )

            return {"status": "success"}

        @self.m_ipc_server.on_get_stats
        async def _handle_get_stats(_args: dict) -> Dict[str, Any]:
            return {
                "status": "success",
                "stats": self.m_server.get_stats(),
            }

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_ipc_task(logger: logging.Logger, server: SaveViewerWebServer, tasks: List[asyncio.Task]) -> None:
    """Initialize the IPC task.

    Args:
        logger (logging.Logger): Logger
        server (SaveViewerWebServer): Web server
        tasks (List[asyncio.Task]): List of tasks
    """
    ipc_server = SaveViewerIpc(logger, server)
    tasks.append(asyncio.create_task(ipc_server.run(), name="IPC Server Task"))
