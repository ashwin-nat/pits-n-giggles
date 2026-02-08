# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.rolling_history import RollingHistory

from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestRollingHistory(F1TelemetryUnitTestsBase):
    def test_initially_empty(self) -> None:
        history = RollingHistory[int](maxlen=3)

        self.assertEqual(len(history), 0)
        self.assertIsNone(history.latest())
        self.assertEqual(history.values(), [])

    def test_push_and_latest(self) -> None:
        history = RollingHistory[int](maxlen=3)

        history.push(1)
        history.push(2)

        self.assertEqual(history.latest(), 2)
        self.assertEqual(history.values(), [1, 2])

    def test_respects_maxlen(self) -> None:
        history = RollingHistory[int](maxlen=3)

        history.push(1)
        history.push(2)
        history.push(3)
        history.push(4)

        self.assertEqual(len(history), 3)
        self.assertEqual(history.values(), [2, 3, 4])

    def test_clear(self) -> None:
        history = RollingHistory[int](maxlen=2)

        history.push(10)
        history.push(20)
        history.clear()

        self.assertEqual(len(history), 0)
        self.assertIsNone(history.latest())
        self.assertEqual(history.values(), [])

    def test_iteration_order(self) -> None:
        history = RollingHistory[str](maxlen=3)

        history.push("a")
        history.push("b")
        history.push("c")

        self.assertEqual(list(history), ["a", "b", "c"])

    def test_invalid_maxlen_raises(self) -> None:
        with self.assertRaises(ValueError):
            RollingHistory[int](maxlen=0)
