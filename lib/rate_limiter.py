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

import time
from typing import Callable, Dict, Optional

# -------------------------------------- FUNCTIONS --------------------------------------------------------------------

class RateLimiter:
    def __init__(self, interval_ms: int, time_fn: Callable[[], float] = time.monotonic):
        """
        interval_ms : minimum time between allowed calls per event
        time_fn     : injectable time source for testability (default: time.monotonic)
        """
        self.interval = interval_ms / 1000.0
        self._time_fn: Callable[[], float] = time_fn
        self._last_time: Dict[str, Optional[float]] = {}

    def allows(self, event_id: str) -> bool:
        """Return True if enough time has passed since last allowed call."""
        now = self._time_fn()
        last = self._last_time.get(event_id)

        # First call must always be allowed
        if last is None:
            self._last_time[event_id] = now
            return True

        if now - last >= self.interval:
            self._last_time[event_id] = now
            return True

        return False
