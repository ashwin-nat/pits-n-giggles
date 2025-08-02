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
from lib.ipc import IpcChildAsync
from typing import List
from functools import partial
import os

from apps.save_viewer.save_viewer_state import open_file_helper
# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_ipc_task(logger: logging.Logger, ipc_port: int, tasks: List[asyncio.Task]) -> None:
    """Initialize the IPC task.

    Args:
        logger (logging.Logger): Logger
        ipc_port (int): IPC port
        tasks (List[asyncio.Task]): List of tasks
    """
    ipc_server = IpcChildAsync(ipc_port, "Save Viewer")
    tasks.append(ipc_server.get_task(partial(handle_ipc_message, logger=logger)))

async def handle_ipc_message(msg: dict, logger: logging.Logger) -> None:
    """Handles incoming IPC messages and dispatches commands.

    Args:
        msg (dict): IPC message
        logger (logging.Logger): Logger
    """

    logger.info(f"Received IPC message: {msg}")

    cmd = msg.get("cmd")
    args: dict = msg.get("args", {})

    if cmd == "open-file":
        return await _handle_open_file(args)
    elif cmd == "shutdown":
        asyncio.create_task(shutdown_handler(args.get("reason", "N/A"), logger))
        return {"status": "success"}

async def _handle_open_file(args: dict) -> dict:
    """Handles the 'open-file' IPC command.

    Args:
        args (dict): IPC command arguments
    """
    if not (file_path := args.get("file-path")):
        return {"status": "error", "message": "Missing or invalid file path"}
    else:
        return await open_file_helper(file_path)

async def shutdown_handler(reason: str, logger: logging.Logger) -> None:
    """Shutdown handler function.

    Args:
        reason (str): The reason for the shutdown
        logger (logging.Logger): Logger
    """
    await asyncio.sleep(2.0)
    logger.info(f"Shutting down. Reason: {reason}")
    os._exit(0)
