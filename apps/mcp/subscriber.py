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
from typing import Any, Dict, List

from lib.ipc import IpcSubscriberAsync
from lib.wdt import WatchDogTimer

from .state import set_state_data

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class McpSubscriber:
    def __init__(self, logger: logging.Logger, port: int, timeout: float) -> None:
        """Initialize the IPC server.

        Args:
            logger (logging.Logger): Logger
            port (int): IPC port
            timeout (float): Connection timeout in seconds
        """
        self.m_ipc_sub = IpcSubscriberAsync(port=port, logger=logger)
        set_state_data("connected", False)
        self.m_wdt = WatchDogTimer(
            status_callback=self._wdt_callback,
            timeout=timeout
        )
        self._init_routes()
        self._init_callbacks()

    def _init_callbacks(self) -> None:
        """Initialize connection callbacks."""
        @self.m_ipc_sub.on_connect
        async def _on_connect() -> None:
            self.m_ipc_sub.logger.info("IPC Subscriber connected")

        @self.m_ipc_sub.on_disconnect
        async def _on_disconnect(exc: Exception | None) -> None:
            self.m_ipc_sub.logger.info("IPC Subscriber disconnected")

    def _init_routes(self) -> None:
        """Initialize the IPC routes."""
        @self.m_ipc_sub.route("race-table-update")
        async def _handle_race_table_update(msg: Dict[str, Any]) -> None:
            """Handle race table update messages."""
            set_state_data("race-table-update", msg)
            self.m_wdt.kick()

    async def run(self) -> None:
        """Starts the IPC server."""
        await self.m_ipc_sub.run()

    async def close(self) -> None:
        """Closes the IPC subscriber."""
        self.m_ipc_sub.close()

    def _wdt_callback(self, active: bool) -> None:
        """Watchdog timer callback to update IPC activity state.

        Args:
            active (bool): True if Subscriptions are active (i.e.) "connected" to producer
        """
        set_state_data("connected", active)
        self.m_ipc_sub.logger.info("Subscriber connected state changed: %s", active)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_subscriber_task(port: int, logger: logging.Logger, tasks: List[asyncio.Task]) -> McpSubscriber:
    """Initialize the IPC task.

    Args:
        port (int): IPC port
        logger (logging.Logger): Logger
        tasks (List[asyncio.Task]): List of tasks

    Returns:
        McpSubscriber: The MCP Subscriber instance
    """
    ipc_sub = McpSubscriber(logger, port, timeout=10.0)
    tasks.append(asyncio.create_task(ipc_sub.run(), name="IPC Subscriber Task"))
    tasks.append(asyncio.create_task(ipc_sub.m_wdt.run(), name="IPC Watchdog Task"))
    return ipc_sub
