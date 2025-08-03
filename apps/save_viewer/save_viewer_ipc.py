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
from typing import List

import apps.save_viewer.save_viewer_state as SaveViewerState
from lib.ipc import IpcChildAsync

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SaveViewerIpc:
    def __init__(self, logger: logging.Logger, ipc_port: int, server_port: int) -> None:
        self.m_logger = logger
        self.m_ipc_port = ipc_port
        self.m_server_port = server_port
        self.m_should_open_ui = True
        self.m_ipc_server = IpcChildAsync(ipc_port, "Save Viewer")

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
        if cmd == "shutdown":
            asyncio.create_task(self._shutdown_handler(args.get("reason", "N/A")))
            return {"status": "success"}

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
            webbrowser.open(f'http://localhost:{self.m_server_port}', new=2)

        return {"status": "success"}

    async def _shutdown_handler(self, reason: str) -> None:
        """Shutdown handler function.

        Args:
            reason (str): The reason for the shutdown
        """
        await asyncio.sleep(2.0)
        self.m_logger.info(f"Shutting down. Reason: {reason}")
        os._exit(0)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_ipc_task(logger: logging.Logger, ipc_port: int, server_port: int, tasks: List[asyncio.Task]) -> None:
    """Initialize the IPC task.

    Args:
        logger (logging.Logger): Logger
        ipc_port (int): IPC port
        server_port (int): Server port
        tasks (List[asyncio.Task]): List of tasks
    """
    ipc_server = SaveViewerIpc(logger, ipc_port, server_port)
    tasks.append(asyncio.create_task(ipc_server.run(), name="IPC Server Task"))
