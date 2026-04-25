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
import threading
from typing import List

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .tests_wdt_base import TestF1Wdt

from lib.wdt import WatchDogTimerSync

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class FakeClock:
    """
    Controllable clock for deterministic testing.
    """

    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeSleep:
    """
    Fake sleep that unblocks immediately when woken, or after a real short cap.
    Call wake() to unblock a sleeping watchdog thread without wall-clock delay.
    """

    def __init__(self):
        self._event = threading.Event()

    def __call__(self, seconds: float) -> None:
        # Wake immediately if signalled, otherwise cap real wait to avoid test hangs
        self._event.wait(timeout=min(seconds, 1.0))
        self._event.clear()

    def wake(self) -> None:
        self._event.set()


class TestWatchDogTimerSync(TestF1Wdt):

    def setUp(self):
        super().setUp()

        self.clock = FakeClock()
        self.fake_sleep = FakeSleep()
        self.status_events: List[bool] = []

        def status_callback(active: bool):
            self.status_events.append(active)

        self.wdt = WatchDogTimerSync(
            status_callback=status_callback,
            timeout=2.0,
            clock=self.clock,
            check_interval=0.01,
            sleep=self.fake_sleep,
        )

        self.wdt.start()

    def tearDown(self):
        self.fake_sleep.wake()
        self.wdt.stop()
        super().tearDown()

    def _wait_for_events(self, count: int, timeout: float = 2.0) -> None:
        """Poll until status_events reaches `count` entries or timeout."""
        deadline = time.monotonic() + timeout
        while len(self.status_events) < count:
            if time.monotonic() >= deadline:
                break
            time.sleep(0.001)

    # -------------------------------------------------------------

    def test_initial_state_is_inactive(self):
        self.assertFalse(self.wdt.active)
        self.assertEqual(self.status_events, [])

    def test_kick_transitions_to_active(self):
        self.wdt.kick()

        self.assertTrue(self.wdt.active)
        self.assertEqual(self.status_events, [True])

    def test_multiple_kicks_do_not_repeat_active_callback(self):
        self.wdt.kick()
        self.wdt.kick()
        self.wdt.kick()

        self.assertTrue(self.wdt.active)
        self.assertEqual(self.status_events, [True])

    def test_timeout_transitions_to_inactive(self):
        self.wdt.kick()

        self.clock.advance(2.1)
        self.fake_sleep.wake()
        self._wait_for_events(2)

        self.assertFalse(self.wdt.active)
        self.assertEqual(self.status_events, [True, False])

    def test_no_inactive_callback_if_never_activated(self):
        self.clock.advance(5.0)
        self.fake_sleep.wake()
        self._wait_for_events(1)  # should never arrive

        self.assertFalse(self.wdt.active)
        self.assertEqual(self.status_events, [])

    def test_kick_after_timeout_reactivates(self):
        self.wdt.kick()
        self.clock.advance(2.1)
        self.fake_sleep.wake()
        self._wait_for_events(2)

        self.wdt.kick()

        self.assertTrue(self.wdt.active)
        self.assertEqual(self.status_events, [True, False, True])

    def test_stop_stops_watchdog(self):
        self.wdt.kick()
        self.wdt.stop()

        self.clock.advance(10.0)
        self.fake_sleep.wake()
        self._wait_for_events(2)  # should never arrive

        self.assertEqual(self.status_events, [True])
