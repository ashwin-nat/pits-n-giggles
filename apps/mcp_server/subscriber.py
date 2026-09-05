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

from typing import Any, Dict, Optional

from lib.ipc import IpcSubscriberAsync
from lib.wdt import WatchDogTimerAsync

from .state import set_state_data

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class McpSubscriber:
    """Files broker telemetry into the state store, and tracks whether it is still arriving.

    Wraps the subscriber the subsystem base built rather than opening its own, so the socket's
    lifetime stays with the base like every other subsystem's. What is added here is the
    watchdog: the MCP tools need to tell "no data yet" apart from "data, but stale", and only a
    timer can answer that.
    """

    def __init__(self, subscriber: IpcSubscriberAsync, timeout: float) -> None:
        """Attach routes and a watchdog to an existing subscriber.

        Args:
            subscriber (IpcSubscriberAsync): Broker subscriber, built and closed by the base
            timeout (float): Seconds of silence before the stream counts as disconnected
        """
        self.m_ipc_sub = subscriber
        set_state_data("connected", False)
        self.m_wdt = WatchDogTimerAsync(
            status_callback=self._wdt_callback,
            timeout=timeout
        )
        self._init_routes()
        self._init_callbacks()

    def _init_callbacks(self) -> None:
        """Initialize connection callbacks."""
        @self.m_ipc_sub.on_connect
        async def _on_connect() -> None:
            self.m_ipc_sub.logger.silent("IPC Subscriber connected")

        @self.m_ipc_sub.on_disconnect
        async def _on_disconnect(_exc: Optional[Exception]) -> None:
            self.m_ipc_sub.logger.silent("IPC Subscriber disconnected")

    def _init_routes(self) -> None:
        """Initialize the IPC routes."""
        @self.m_ipc_sub.route("race-table-update")
        async def _handle_race_table_update(msg: Dict[str, Any]) -> None:
            """Handle race table update messages."""
            set_state_data("race-table-update", msg)
            self.m_wdt.kick()

    def _wdt_callback(self, active: bool) -> None:
        """Watchdog timer callback to update IPC activity state.

        Args:
            active (bool): True if Subscriptions are active (i.e.) "connected" to producer
        """
        set_state_data("connected", active)
        if active:
            self.m_ipc_sub.logger.info("Connected to data stream")
        else:
            self.m_ipc_sub.logger.warning("Disconnected from data stream")
