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
from typing import Any, Dict, List

from lib.ipc import IpcSubscriberAsync

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class McpSubscriber:
    def __init__(self, logger: logging.Logger, port: int) -> None:
        """Initialize the IPC server.

        Args:
            logger (logging.Logger): Logger
        """
        self.m_ipc_sub = IpcSubscriberAsync(port=port, logger=logger)
        self._init_routes()

    def _init_routes(self) -> None:
        """Initialize the IPC routes."""
        @self.m_ipc_sub.route("race-table-update")
        async def _handle_race_table_update(msg: Dict[str, Any]) -> None:
            """Handle race table update messages."""
            self.m_ipc_sub.logger.debug("Received race table update")

    async def run(self) -> None:
        """Starts the IPC server."""
        await self.m_ipc_sub.run()

    async def close(self) -> None:
        """Closes the IPC subscriber."""
        await self.m_ipc_sub.close()

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_subscriber_task(port: int, logger: logging.Logger, tasks: List[asyncio.Task]) -> None:
    """Initialize the IPC task.

    Args:
        port (int): IPC port
        logger (logging.Logger): Logger
        tasks (List[asyncio.Task]): List of tasks
    """
    ipc_sub = McpSubscriber(logger, port)
    tasks.append(asyncio.create_task(ipc_sub.run(), name="IPC Server Task"))
    return ipc_sub
