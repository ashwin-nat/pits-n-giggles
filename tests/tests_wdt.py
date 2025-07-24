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
import sys
import os
from typing import List

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase

from lib.wdt import WatchDogTimer

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class TestWatchDogTimer(F1TelemetryUnitTestsBase):
    async def asyncSetUp(self):
        self.state_changes: List[bool] = []
        self.wdt = WatchDogTimer(
            status_callback=self.state_changes.append,
            timeout=0.5  # Short timeout for test speed
        )
        self.task = asyncio.create_task(self.wdt.run(), name="UT Watchdog Task")

    async def asyncTearDown(self):
        self.wdt.stop()
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    async def test_initial_state_idle(self):
        """Watchdog should start idle with no state change callback triggered."""
        await asyncio.sleep(0.1)
        self.assertEqual(self.state_changes, [])

    async def test_transitions_to_active(self):
        """Kicking the watchdog should trigger an active state."""
        self.wdt.kick()
        await asyncio.sleep(0.1)
        self.assertEqual(self.state_changes, [True])

    async def test_ignores_duplicate_active_kicks(self):
        """Repeated kicks should not cause duplicate active callbacks."""
        for _ in range(3):
            self.wdt.kick()
            await asyncio.sleep(0.1)
        self.assertEqual(self.state_changes, [True])

    async def test_times_out_to_inactive(self):
        """No kick for timeout period should mark it inactive."""
        self.wdt.kick()
        await asyncio.sleep(0.1)
        self.assertEqual(self.state_changes, [True])

        await asyncio.sleep(0.6)
        self.assertEqual(self.state_changes, [True, False])

    async def test_recovers_after_timeout(self):
        """Watchdog should become active again after a timeout if kicked again."""
        self.wdt.kick()
        await asyncio.sleep(0.1)
        self.assertEqual(self.state_changes, [True])

        await asyncio.sleep(0.6)
        self.assertEqual(self.state_changes, [True, False])

        self.wdt.kick()
        await asyncio.sleep(0.1)
        self.assertEqual(self.state_changes, [True, False, True])
