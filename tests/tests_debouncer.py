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
import time
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.button_debouncer import ButtonDebouncer
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestMultiButtonDebouncer(F1TelemetryUnitTestsBase):
    def setUp(self):
        self.debouncer = ButtonDebouncer(debounce_time=0.3)

    def test_single_button_press(self):
        result = self.debouncer.onButtonPress("Button1")
        self.assertTrue(result, "The first button press should be processed.")

    def test_debounce_same_button(self):
        self.debouncer.onButtonPress("Button1")
        result = self.debouncer.onButtonPress("Button1")  # Within debounce time
        self.assertFalse(result, "A button press within debounce time should not be processed.")

    def test_different_buttons(self):
        result1 = self.debouncer.onButtonPress("Button1")
        result2 = self.debouncer.onButtonPress("Button2")
        self.assertTrue(result1, "The first button press should be processed.")
        self.assertTrue(result2, "A different button's press should be processed.")

    def test_debounce_respects_time(self):
        self.debouncer.onButtonPress("Button1")
        time.sleep(0.4)  # Wait longer than debounce time
        result = self.debouncer.onButtonPress("Button1")  # After debounce time
        self.assertTrue(result, "A button press after debounce time should be processed.")

    def test_no_event_after_close_press(self):
        self.debouncer.onButtonPress("Button1")
        time.sleep(0.2)  # Less than debounce time
        result = self.debouncer.onButtonPress("Button1")  # Within debounce time
        self.assertFalse(result, "A button press within debounce time should not be processed.")
