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

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from lib.delta.lap import Lap

from .tests_delta_base import TestF1DeltaBase

# ----------------------------------------------------------------------------------------------------------------------

class TestDeltaLap(TestF1DeltaBase):
    """Tests for the Lap class"""

    def setUp(self):
        self.lap = Lap(lap_number=1)

    def test_initialization(self):
        """Test lap initializes correctly"""
        self.assertEqual(self.lap.lap_number, 1)
        self.assertEqual(len(self.lap.data_points), 0)
        self.assertIsNone(self.lap.lap_time)
        self.assertTrue(self.lap.is_valid)
        self.assertEqual(self.lap._last_distance, -1.0)

    def test_record_data_point_success(self):
        """Test recording valid data points"""
        self.assertTrue(self.lap.record_data_point(100, 2.5))
        self.assertTrue(self.lap.record_data_point(200, 5.0))
        self.assertEqual(len(self.lap.data_points), 2)
        self.assertEqual(self.lap._last_distance, 200)

    def test_record_data_point_reject_non_increasing(self):
        """Test that non-increasing distances are rejected"""
        self.assertTrue(self.lap.record_data_point(100, 2.5))
        self.assertTrue(self.lap.record_data_point(200, 5.0))

        # Try to record same distance
        self.assertFalse(self.lap.record_data_point(200, 5.5))

        # Try to record lower distance
        self.assertFalse(self.lap.record_data_point(150, 4.0))

        # Should still only have 2 points
        self.assertEqual(len(self.lap.data_points), 2)

    def test_handle_flashback_removes_data(self):
        """Test flashback removes future data points"""
        self.lap.record_data_point(100, 2.5)
        self.lap.record_data_point(200, 5.0)
        self.lap.record_data_point(300, 7.5)
        self.lap.record_data_point(400, 10.0)

        self.lap.handle_flashback(250)

        # Should only keep points up to 250m
        self.assertEqual(len(self.lap.data_points), 2)
        self.assertEqual(self.lap.data_points[-1].distance, 200)
        self.assertFalse(self.lap.is_valid)
        self.assertEqual(self.lap._last_distance, 200)

    def test_handle_flashback_empty_result(self):
        """Test flashback to before all data points"""
        self.lap.record_data_point(100, 2.5)
        self.lap.record_data_point(200, 5.0)

        self.lap.handle_flashback(50)

        self.assertEqual(len(self.lap.data_points), 0)
        self.assertFalse(self.lap.is_valid)
        self.assertEqual(self.lap._last_distance, -1.0)

    def test_complete_lap(self):
        """Test completing a lap"""
        self.lap.complete_lap(65.432)
        self.assertEqual(self.lap.lap_time, 65.432)

    def test_get_time_at_distance_interpolation(self):
        """Test time interpolation at specific distance"""
        self.lap.record_data_point(0, 0.0)
        self.lap.record_data_point(100, 2.5)
        self.lap.record_data_point(200, 5.0)

        # Test exact point
        time, idx = self.lap.get_time_at_distance(100)
        self.assertAlmostEqual(time, 2.5, places=6)

        # Test interpolation (50m should be 1.25s)
        time, idx = self.lap.get_time_at_distance(50)
        self.assertAlmostEqual(time, 1.25, places=6)

        # Test interpolation (150m should be 3.75s)
        time, idx = self.lap.get_time_at_distance(150)
        self.assertAlmostEqual(time, 3.75, places=6)

    def test_get_time_at_distance_out_of_range(self):
        """Test querying distance beyond recorded data"""
        self.lap.record_data_point(100, 2.5)
        self.lap.record_data_point(200, 5.0)

        time, idx = self.lap.get_time_at_distance(300)
        self.assertIsNone(time)

    def test_get_time_at_distance_insufficient_data(self):
        """Test with insufficient data points"""
        time, idx = self.lap.get_time_at_distance(100)
        self.assertIsNone(time)

        self.lap.record_data_point(100, 2.5)
        time, idx = self.lap.get_time_at_distance(100)
        self.assertIsNone(time)  # Need at least 2 points

    def test_invalidate(self):
        """Test manual invalidation"""
        self.assertTrue(self.lap.is_valid)
        self.lap.invalidate()
        self.assertFalse(self.lap.is_valid)

