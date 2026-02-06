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
# pylint: skip-file

import asyncio
import os
import sys
import time
from typing import List

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.wdt import WatchDogTimerAsync

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class TestWatchDogTimer(F1TelemetryUnitTestsBase):
    async def asyncSetUp(self):
        self.state_changes: List[bool] = []
        self.fake_time: float = 0.0

        def fake_clock() -> float:
            return self.fake_time

        self.wdt = WatchDogTimerAsync(
            status_callback=self.state_changes.append,
            timeout=0.5,
            clock=fake_clock,
            check_interval=0.01
        )
        self.task = asyncio.create_task(self.wdt.run(), name="UT Watchdog Task")

    async def asyncTearDown(self):
        self.wdt.stop()
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    async def tick_time(self, seconds: float = 0.1):
        """
        Advance fake time and yield to the event loop once so
        the watchdog run loop can process.
        """
        self.fake_time += seconds
        # Use a tiny non-zero sleep to guarantee scheduling across platforms
        await asyncio.sleep(0.001)

    async def wait_for_state(self, expected: bool, timeout: float = 1.0):
        """Wait until the last observed state matches `expected` using fake_time as deadline."""
        deadline = self.fake_time + timeout
        while self.fake_time < deadline:
            if self.state_changes and self.state_changes[-1] == expected:
                return
            await self.tick_time(0.01)
        self.fail(f"Expected state {expected} not received within {timeout:.1f} seconds")

    async def test_initial_state_idle(self):
        """Watchdog should start idle with no state change callback triggered."""
        await self.tick_time(0.1)
        self.assertEqual(self.state_changes, [])

    async def test_transitions_to_active(self):
        """Kicking the watchdog should trigger an active state."""
        self.wdt.kick()
        await self.wait_for_state(True)
        self.assertEqual(self.state_changes, [True])

    async def test_ignores_duplicate_active_kicks(self):
        """Repeated kicks should not cause duplicate active callbacks."""
        self.wdt.kick()
        await self.wait_for_state(True)

        for _ in range(2):
            await self.tick_time(0.1)
            self.wdt.kick()

        self.assertEqual(self.state_changes, [True])

    async def test_times_out_to_inactive(self):
        """No kick for timeout period should mark it inactive."""
        self.wdt.kick()
        await self.wait_for_state(True)

        await self.tick_time(1.0)  # advance beyond timeout
        await self.wait_for_state(False)
        self.assertEqual(self.state_changes, [True, False])

    async def test_recovers_after_timeout(self):
        """Watchdog should become active again after a timeout if kicked again."""
        self.wdt.kick()
        await self.wait_for_state(True)

        await self.tick_time(1.0)  # advance beyond timeout
        await self.wait_for_state(False)
        self.wdt.kick()
        await self.wait_for_state(True)

        self.assertEqual(self.state_changes, [True, False, True])
