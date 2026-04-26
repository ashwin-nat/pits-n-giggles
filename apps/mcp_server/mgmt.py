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

from apps.mcp_server.mcp_server import MCPBridge
from lib.child_proc_mgmt import report_ipc_port_from_child
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.ipc import IpcServerAsync

from .subscriber import McpSubscriber

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class McpIpc:
    def __init__(self,
                 logger: logging.Logger,
                 ipc_sub: McpSubscriber,
                 mcp_server: MCPBridge,
                 mcp_task: asyncio.Task) -> None:
        """Initialize the IPC server.

        Args:
            logger (logging.Logger): Logger
            ipc_sub (McpSubscriber): MCP Subscriber
            mcp_server (MCPBridge): MCP Bridge
            mcp_task (asyncio.Task): MCP Task
        """
        self.m_logger = logger
        self.m_should_open_ui = True
        self.m_ipc_server = IpcServerAsync(name="MCP IPC Server")
        self._register_handlers()
        self.m_ipc_sub = ipc_sub
        self.m_mcp_task = mcp_task
        self.m_mcp_server = mcp_server
        report_ipc_port_from_child(self.m_ipc_server.port)

    async def run(self) -> None:
        """Starts the IPC server."""
        await self.m_ipc_server.run()

    def _register_handlers(self):
        """Registers handlers for IPC commands."""

        @self.m_ipc_server.on_shutdown
        async def _shutdown_handler(args: dict) -> Dict[str, Any]:
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

        @self.m_ipc_server.on_heartbeat_missed
        async def _heartbeat_missed_handler(count: int) -> dict:
            """Handle terminate command"""

            print(f"[MCP] Missed heartbeat {count} times. This process has probably been orphaned. Terminating...")
            os._exit(PNG_LOST_CONN_TO_PARENT)

        @self.m_ipc_server.on_get_stats
        async def _get_stats(_args: dict) -> dict:
            return {
                "status": "success",
                "stats": {
                    "INGRESS": self.m_ipc_sub.get_stats(),
                    "MCP": self.m_mcp_server.get_stats(),
                }
            }

    async def _handle_shutdown_task(self) -> None:
        """Handles shutdown signal."""
        self.m_logger.info("Shutting down MCP IPC Subscriber")
        self.m_ipc_sub.m_wdt.stop()
        self.m_mcp_task.cancel()
        await self.m_ipc_sub.close()
        self.m_logger.debug("MCP shutdown task completed")

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_ipc_task(
        logger: logging.Logger,
        tasks: List[asyncio.Task],
        ipc_sub: McpSubscriber,
        mcp_bridge: MCPBridge,
        mcp_task: asyncio.Task) -> None:
    """Initialize the IPC task.

    Args:
        logger (logging.Logger): Logger
        tasks (List[asyncio.Task]): List of tasks
        ipc_sub (McpSubscriber): MCP Subscriber
        mcp_bridge (MCPBridge): MCP Bridge
        mcp_task (asyncio.Task): MCP Task
    """
    ipc_server = McpIpc(logger, ipc_sub=ipc_sub, mcp_server=mcp_bridge,mcp_task=mcp_task)
    tasks.append(asyncio.create_task(ipc_server.run(), name="IPC Server Task"))
