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
import json
import logging
from functools import partial
from typing import List, Optional, Callable, Awaitable, Dict

import msgpack
import socketio

import apps.backend.state_mgmt_layer as TelWebAPI
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.ipc import IpcChildAsync
from .command_dispatcher import processIpcCommand


# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def registerIpcTask(ipc_port: Optional[int], logger: logging.Logger, tasks: List[asyncio.Task]) -> None:
    """Register the IPC task

    Args:
        ipc_port (Optional[int]): IPC port
        logger (logging.Logger): Logger
        tasks (List[asyncio.Task]): List of tasks
    """

    # Register the IPC task only if port is specified
    if ipc_port:
        logger.debug(f"Starting IPC server on port {ipc_port}")
        server = IpcChildAsync(ipc_port, "Backend")
        tasks.append(server.get_task(partial(processIpcCommand, logger=logger)))

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "registerIpcTask",
]
