# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
from unittest.mock import patch
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.button_debouncer import ButtonDebouncer
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestMultiButtonDebouncer(F1TelemetryUnitTestsBase):
    def setUp(self):
        self.debouncer = ButtonDebouncer(debounce_time=0.3)

    @patch("time.time", side_effect=[1.0])
    def test_single_button_press(self, mock_time):
        result = self.debouncer.onButtonPress("Button1")
        self.assertTrue(result)

    @patch("time.time", side_effect=[1.0, 1.001])
    def test_different_buttons(self, mock_time):
        result1 = self.debouncer.onButtonPress("Button1")  # time=1.0
        result2 = self.debouncer.onButtonPress("Button2")  # time=1.001
        self.assertTrue(result1)
        self.assertTrue(result2)

    @patch("time.time", side_effect=[1.0, 1.1])
    def test_debounce_same_button(self, mock_time):
        self.debouncer.onButtonPress("Button1")  # time=1.0
        result = self.debouncer.onButtonPress("Button1")  # time=1.1
        self.assertFalse(result)

    @patch("time.time", side_effect=[1.0, 1.4])
    def test_debounce_respects_time(self, mock_time):
        self.debouncer.onButtonPress("Button1")  # time=1.0
        result = self.debouncer.onButtonPress("Button1")  # time=1.4
        self.assertTrue(result)

    @patch("time.time", side_effect=[1.0, 1.2])
    def test_no_event_after_close_press(self, mock_time):
        self.debouncer.onButtonPress("Button1")  # time=1.0
        result = self.debouncer.onButtonPress("Button1")  # time=1.2
        self.assertFalse(result)
