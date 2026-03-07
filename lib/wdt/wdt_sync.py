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

import threading
import time
from typing import Callable, Optional

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WatchDogTimerSync:
    """
    Generic watchdog timer that monitors activity and triggers a status callback
    when input becomes inactive for a configured timeout.

    This is the synchronous (thread-based) equivalent of the asyncio version.
    """

    def __init__(
        self,
        status_callback: Callable[[bool], None],
        timeout: float = 2.0,
        clock: Callable[[], float] = time.time,
        check_interval: float = 0.5,
    ) -> None:
        self._status_callback = status_callback
        self._timeout = timeout
        self._clock = clock
        self._check_interval = check_interval

        self._last_kick_time = self._clock()
        self.active = False

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def kick(self) -> None:
        """
        Kick the watchdog timer.

        Updates the internal timer and triggers `status_callback(True)`
        if transitioning to active state.
        """
        self._last_kick_time = self._clock()
        if not self.active:
            self.active = True
            self._status_callback(True)

    def start(self) -> None:
        """
        Start the watchdog monitoring loop in a background thread.
        """
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="WatchDogTimer",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        """
        Blocking watchdog loop (thread target).
        """
        while not self._stop_event.is_set():
            time.sleep(self._check_interval)

            elapsed = self._clock() - self._last_kick_time
            if self.active and elapsed > self._timeout:
                self.active = False
                self._status_callback(False)

    def stop(self) -> None:
        """
        Stop the watchdog loop and wait for the thread to exit.
        """
        self._stop_event.set()
        if self._thread:
            self._thread.join()
