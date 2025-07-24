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
        self.status_changes: List[bool] = []
        self.monitor = WatchDogTimer(
            status_callback=self.status_changes.append,
            timeout=0.5  # Use short timeout for faster tests
        )
        self.task = asyncio.create_task(self.monitor.run(), name="UT Monitor Task")

    async def asyncTearDown(self):
        self.monitor.stop()
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    async def test_starts_disconnected(self):
        """Monitor should start in disconnected state with no callback fired."""
        await asyncio.sleep(0.1)
        self.assertEqual(self.status_changes, [])

    async def test_transitions_to_connected_on_packet(self):
        """Receiving a packet should trigger a connected callback."""
        self.monitor.on_packet_received()
        await asyncio.sleep(0.1)
        self.assertEqual(self.status_changes, [True])

    async def test_does_not_fire_duplicate_connected(self):
        """Receiving repeated packets should not fire redundant connected events."""
        for _ in range(3):
            self.monitor.on_packet_received()
            await asyncio.sleep(0.1)
        self.assertEqual(self.status_changes, [True])

    async def test_transitions_to_disconnected_on_timeout(self):
        """No packet for timeout duration should trigger disconnected callback."""
        self.monitor.on_packet_received()
        await asyncio.sleep(0.1)
        self.assertEqual(self.status_changes, [True])

        await asyncio.sleep(0.6)  # Wait beyond the timeout
        self.assertEqual(self.status_changes, [True, False])

    async def test_reconnect_after_disconnection(self):
        """Monitor should detect disconnection and reconnect if packets resume."""
        self.monitor.on_packet_received()
        await asyncio.sleep(0.1)
        self.assertEqual(self.status_changes, [True])

        await asyncio.sleep(0.6)
        self.assertEqual(self.status_changes, [True, False])

        self.monitor.on_packet_received()
        await asyncio.sleep(0.1)
        self.assertEqual(self.status_changes, [True, False, True])
