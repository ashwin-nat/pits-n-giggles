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

from lib.child_proc_mgmt import report_ipc_port_from_child
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.ipc import IpcServerAsync

from .subscriber import McpSubscriber

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class McpIpc:
    def __init__(self, logger: logging.Logger, ipc_sub: McpSubscriber, mcp_task: asyncio.Task) -> None:
        """Initialize the IPC server.

        Args:
            logger (logging.Logger): Logger
            ipc_sub (McpSubscriber): MCP Subscriber
            mcp_task (asyncio.Task): MCP Task
        """
        self.m_logger = logger
        self.m_should_open_ui = True
        self.m_ipc_server = IpcServerAsync(name="MCP IPC Server")
        self.m_ipc_server.register_shutdown_callback(self._shutdown_handler)
        self.m_ipc_server.register_heartbeat_missed_callback(self._heartbeat_missed_handler)
        self.m_ipc_sub = ipc_sub
        self.m_mcp_task = mcp_task
        report_ipc_port_from_child(self.m_ipc_server.port)

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
        self.m_logger.debug("Received IPC message: %s", msg)
        return {"status": "error", "message": "IPC commands are not supported on this subsystem."}

    async def _shutdown_handler(self, args: dict) -> Dict[str, Any]:
        """Shutdown handler function.

        Args:
            args (dict): IPC command arguments

        Returns:
            Dict[str, Any]: Shutdown response
        """
        reason = args["reason"]
        self.m_logger.info(f"Shutting down. Reason: {reason}")
        asyncio.create_task(self._handle_shutdown_task())
        return {"status": "success"}

    async def _heartbeat_missed_handler(self, count: int) -> dict:
        """Handle terminate command"""

        print(f"[MCP] Missed heartbeat {count} times. This process has probably been orphaned. Terminating...")
        os._exit(PNG_LOST_CONN_TO_PARENT)

    async def _handle_shutdown_task(self) -> None:
        """Handles shutdown signal."""
        self.m_logger.info("Shutting down MCP IPC Subscriber")
        await self.m_ipc_sub.close()
        self.m_mcp_task.cancel()

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_ipc_task(
        logger: logging.Logger,
        tasks: List[asyncio.Task],
        ipc_sub: McpSubscriber,
        mcp_task: asyncio.Task) -> None:
    """Initialize the IPC task.

    Args:
        logger (logging.Logger): Logger
        tasks (List[asyncio.Task]): List of tasks
        ipc_sub (McpSubscriber): MCP Subscriber
        mcp_task (asyncio.Task): MCP Task
    """
    ipc_server = McpIpc(logger, ipc_sub=ipc_sub, mcp_task=mcp_task)
    tasks.append(asyncio.create_task(ipc_server.run(), name="IPC Server Task"))
