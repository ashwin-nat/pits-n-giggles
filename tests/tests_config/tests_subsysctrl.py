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

import os
import sys

from pydantic import ValidationError

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from lib.config import SubSysCtrl

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestSubSysCtrl(TestF1ConfigBase):
    """Test SubSysCtrl model"""

    def test_default_values(self):
        """Test default values"""
        settings = SubSysCtrl()
        self.assertEqual(settings.num_missable_heartbeats, 3)
        self.assertEqual(settings.heartbeat_interval, 5.0)

    def test_num_missable_heartbeats(self):
        # Accept explicit True
        settings = SubSysCtrl(num_missable_heartbeats=5)
        self.assertEqual(settings.num_missable_heartbeats, 5)

        # Boundary values
        settings_min = SubSysCtrl(num_missable_heartbeats=1)
        self.assertEqual(settings_min.num_missable_heartbeats, 1)

        settings_max = SubSysCtrl(num_missable_heartbeats=19)
        self.assertEqual(settings_max.num_missable_heartbeats, 19)

        # Invalid types should raise validation errors
        with self.assertRaises(ValidationError):
            SubSysCtrl(num_missable_heartbeats="notanumber")

        # Invalid range
        with self.assertRaises(ValidationError):
            SubSysCtrl(num_missable_heartbeats=0)
        with self.assertRaises(ValidationError):
            SubSysCtrl(num_missable_heartbeats=50)

        # Default values for the other fields
        self.assertEqual(settings.heartbeat_interval, 5.0)
    def test_heartbeat_interval(self):
        settings = SubSysCtrl(heartbeat_interval=10.0)
        self.assertEqual(settings.heartbeat_interval, 10.0)

        # Boundary values
        settings_min = SubSysCtrl(heartbeat_interval=1.0)
        self.assertEqual(settings_min.heartbeat_interval, 1.0)

        settings_max = SubSysCtrl(heartbeat_interval=60.0)
        self.assertEqual(settings_max.heartbeat_interval, 60.0)

        with self.assertRaises(ValidationError):
            SubSysCtrl(heartbeat_interval="notanumber")

        # Invalid range
        with self.assertRaises(ValidationError):
            SubSysCtrl(heartbeat_interval=0.0)
        with self.assertRaises(ValidationError):
            SubSysCtrl(heartbeat_interval=60.1)
