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
    Generic watchdog timer that monitors activity and triggers a status callback
    when input becomes inactive for a configured timeout.

    Args:
        status_callback (Callable[[bool], None]): Called when activity status changes.
            True indicates active, False indicates inactive.
        timeout (float): Time in seconds after which inactivity is assumed.
    """

    def __init__(self, status_callback: Callable[[bool], None], timeout: float = 2.0) -> None:
        self._status_callback: Callable[[bool], None] = status_callback
        self._timeout: float = timeout
        self._last_kick_time: float = time.time()
        self.active: bool = False
        self._stopped: bool = False  # Used to break the run() loop gracefully

    def kick(self) -> None:
        """
        Kick the watchdog timer

        Updates the internal timer and triggers `status_callback(True)`
        if transitioning to active state.
        """
        self._last_kick_time = time.time()
        if not self.active:
            self.active = True
            self._status_callback(True)

    async def run(self) -> None:
        """
        Coroutine that runs the watchdog monitoring loop.

        Should be scheduled as a background task using `asyncio.create_task(...)`.
        Checks for prolonged inactivity and triggers `status_callback(False)` when detected.
        """
        try:
            while not self._stopped:
                await asyncio.sleep(0.5)
                elapsed = time.time() - self._last_kick_time
                if self.active and elapsed > self._timeout:
                    self.active = False
                    self._status_callback(False)
        except asyncio.CancelledError:
            # Graceful exit on task cancellation
            pass

    def stop(self) -> None:
        """
        Request the watchdog loop to stop on the next cycle.
        """
        self._stopped = True
