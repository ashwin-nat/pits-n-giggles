# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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
from lib.ipc import IpcDealerAsync, IpcServerAsync, IpcSubscriberAsync

from .web_server import WebServer

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WebIpc:
    """IPC server exposing lifecycle + stats endpoints to the launcher."""

    def __init__(
            self,
            logger: logging.Logger,
            web_server: WebServer,
            ipc_sub: IpcSubscriberAsync,
            dealer: IpcDealerAsync,
            shutdown_event: asyncio.Event) -> None:
        """Initialize the IPC server.

        Args:
            logger (logging.Logger): Logger
            web_server (WebServer): Web server
            ipc_sub (IpcSubscriberAsync): Broker subscriber
            dealer (IpcDealerAsync): Router/dealer client
            shutdown_event (asyncio.Event): Event to signal the emit-timer tasks to stop
        """
        self.m_logger = logger
        self.m_web_server = web_server
        self.m_ipc_sub = ipc_sub
        self.m_dealer = dealer
        self.m_shutdown_event = shutdown_event
        self.m_ipc_server = IpcServerAsync(name="Web")
        self._register_routes()
        report_ipc_port_from_child(self.m_ipc_server.port)

    async def run(self) -> None:
        """Starts the IPC server."""
        await self.m_ipc_server.run()

    def _register_routes(self) -> None:
        """Registers routes for the IPC server."""

        @self.m_ipc_server.on_heartbeat_missed
        async def _heartbeat_missed_handler(count: int) -> None:
            self.m_logger.error(
                "Missed heartbeat %d times. This process has probably been orphaned. Terminating...", count)
            # os._exit required: child process must terminate immediately without
            # running atexit handlers or flushing stdio buffers from parent.
            os._exit(PNG_LOST_CONN_TO_PARENT)

        @self.m_ipc_server.on_shutdown
        async def _shutdown_handler(args: dict) -> Dict[str, Any]:
            reason = args["reason"]
            self.m_logger.info("Shutting down. Reason: %s", reason)
            asyncio.create_task(self._handle_shutdown_task(), name="Web Shutdown Task")
            return {"status": "success"}

        @self.m_ipc_server.on_get_stats
        async def _handle_get_stats(_args: dict) -> Dict[str, Any]:
            return {
                "status": "success",
                "stats": {
                    "web_server": self.m_web_server.get_stats(),
                    "ipc_sub": self.m_ipc_sub.get_stats(),
                    "dealer": self.m_dealer.get_stats(),
                },
            }

    async def _handle_shutdown_task(self) -> None:
        """Tears down the web server, emit timers, subscriber and dealer."""
        self.m_shutdown_event.set()
        await self.m_web_server.stop()
        self.m_ipc_sub.close()
        await self.m_dealer.close()
        self.m_logger.debug("Web shutdown task completed")

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_ipc_task(
        logger: logging.Logger,
        web_server: WebServer,
        ipc_sub: IpcSubscriberAsync,
        dealer: IpcDealerAsync,
        shutdown_event: asyncio.Event,
        tasks: List[asyncio.Task]) -> None:
    """Initialize the IPC task.

    Args:
        logger (logging.Logger): Logger
        web_server (WebServer): Web server
        ipc_sub (IpcSubscriberAsync): Broker subscriber
        dealer (IpcDealerAsync): Router/dealer client
        shutdown_event (asyncio.Event): Event to signal the emit-timer tasks to stop
        tasks (List[asyncio.Task]): List of tasks
    """
    ipc_server = WebIpc(logger, web_server, ipc_sub, dealer, shutdown_event)
    tasks.append(asyncio.create_task(ipc_server.run(), name="IPC Server Task"))
