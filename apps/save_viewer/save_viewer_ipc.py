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
from lib.ipc import IpcChildAsync
from lib.web_server import ClientType

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SaveViewerIpc:
    def __init__(self, logger: logging.Logger, ipc_port: int, server: SaveViewerWebServer) -> None:
        """Initialize the IPC server.

        Args:
            logger (logging.Logger): Logger
            ipc_port (int): IPC port
            server (SaveViewerWebServer): Web server
        """
        self.m_logger = logger
        self.m_ipc_port = ipc_port
        self.m_server = server
        self.m_should_open_ui = True
        self.m_ipc_server = IpcChildAsync(ipc_port, "Save Viewer")
        self.m_ipc_server.register_shutdown_callback(self._shutdown_handler)
        self.m_ipc_server.register_heartbeat_missed_callback(self._heartbeat_missed_handler)

    async def run(self) -> None:
        """Starts the IPC server."""
        await self.m_ipc_server.run(self._handle_ipc_message)

    async def _handle_ipc_message(self, msg: dict) -> dict:
        """Handles incoming IPC messages and dispatches commands.

        Args:
            msg (dict): IPC message

        Returns:
            dict: IPC response
        """
        self.m_logger.debug(f"Received IPC message: {msg}")
        cmd = msg.get("cmd")
        args: dict = msg.get("args", {})

        if cmd == "open-file":
            return await self._handle_open_file(args)

        return {"status": "error", "message": f"Unknown command: {cmd}"}

    async def _handle_open_file(self, args: dict) -> dict:
        """Handles the 'open-file' IPC command.

        Args:
            args (dict): IPC command arguments
        """
        if not (file_path := args.get("file-path")):
            return {"status": "error", "message": "Missing or invalid file path"}

        try:
            await SaveViewerState.open_file_helper(file_path)
        except Exception as e: # pylint: disable=broad-except
            return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}

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

    async def _shutdown_handler(self, args: dict) -> Dict[str, Any]:
        """Shutdown handler function.

        Args:
            args (dict): IPC command arguments

        Returns:
            Dict[str, Any]: Shutdown response
        """
        reason = args["reason"]
        self.m_logger.info(f"Shutting down. Reason: {reason}")
        await self.m_server.stop()
        return {"status": "success"}

    async def _heartbeat_missed_handler(self, count: int) -> dict:
        """Handle terminate command"""

        print(f"[SAVE_VIEWER] Missed heartbeat {count} times. This process has probably been orphaned. Terminating...")
        os._exit(PNG_LOST_CONN_TO_PARENT)


# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_ipc_task(logger: logging.Logger, ipc_port: int, server: SaveViewerWebServer, tasks: List[asyncio.Task]) -> None:
    """Initialize the IPC task.

    Args:
        logger (logging.Logger): Logger
        ipc_port (int): IPC port
        server (SaveViewerWebServer): Web server
        tasks (List[asyncio.Task]): List of tasks
    """
    ipc_server = SaveViewerIpc(logger, ipc_port, server)
    tasks.append(asyncio.create_task(ipc_server.run(), name="IPC Server Task"))
