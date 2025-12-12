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

from lib.rate_limiter import RateLimiter

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

class FakeClock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def advance(self, seconds: float):
        self.t += seconds

class TestRateLimiter(F1TelemetryUnitTestsBase):

    def setUp(self):
        self.clock = FakeClock()
        self.rl = RateLimiter(interval_ms=200, time_fn=self.clock.now)

    def test_first_call_is_allowed(self):
        self.assertTrue(self.rl.allows("evt"))

    def test_immediate_second_call_is_blocked(self):
        self.assertTrue(self.rl.allows("evt"))
        self.assertFalse(self.rl.allows("evt"))

    def test_allows_after_interval(self):
        self.assertTrue(self.rl.allows("evt"))
        self.clock.advance(0.2)
        self.assertTrue(self.rl.allows("evt"))

    def test_blocks_before_interval(self):
        self.assertTrue(self.rl.allows("evt"))
        self.clock.advance(0.199)
        self.assertFalse(self.rl.allows("evt"))

    def test_independent_event_ids(self):
        self.assertTrue(self.rl.allows("evt1"))
        self.assertTrue(self.rl.allows("evt2"))

        self.clock.advance(0.1)
        self.assertFalse(self.rl.allows("evt1"))
        self.assertFalse(self.rl.allows("evt2"))

        self.clock.advance(0.1)
        self.assertTrue(self.rl.allows("evt1"))
        self.assertTrue(self.rl.allows("evt2"))

    def test_does_not_update_last_time_when_blocked(self):
        self.assertTrue(self.rl.allows("evt"))
        self.clock.advance(0.1)
        self.assertFalse(self.rl.allows("evt"))

        self.clock.advance(0.1)
        self.assertTrue(self.rl.allows("evt"))
