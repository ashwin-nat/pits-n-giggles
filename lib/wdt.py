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
import time
from typing import Callable

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WatchDogTimer:
    """
    Monitors incoming telemetry over UDP and infers connection status using a watchdog timer.

    Args:
        status_callback (Callable[[bool], None]): Called when connection state changes.
        timeout (float): Time in seconds after which connection is considered lost.
    """

    def __init__(self, status_callback: Callable[[bool], None], timeout: float = 2.0) -> None:
        self._status_callback: Callable[[bool], None] = status_callback
        self._timeout: float = timeout
        self._last_received_time: float = time.time()
        self.connected: bool = False
        self._stopped: bool = False  # Used to break the run() loop gracefully

    def on_packet_received(self) -> None:
        """
        Call this whenever a UDP telemetry packet is received.

        Updates the watchdog timer and triggers `status_callback(True)` if transitioning to connected.
        """
        self._last_received_time = time.time()
        if not self.connected:
            self.connected = True
            self._status_callback(True)

    async def run(self) -> None:
        """
        Coroutine that should be scheduled using `asyncio.create_task(...)`.

        It checks for telemetry silence and triggers `status_callback(False)` when disconnected.
        """
        try:
            while not self._stopped:
                await asyncio.sleep(0.5)
                time_since_last = time.time() - self._last_received_time
                if self.connected and time_since_last > self._timeout:
                    self.connected = False
                    self._status_callback(False)
        except asyncio.CancelledError:
            # Graceful shutdown on task cancellation
            pass

    def stop(self) -> None:
        """
        Stop the watchdog loop gracefully. Should be called before shutdown.
        """
        self._stopped = True
