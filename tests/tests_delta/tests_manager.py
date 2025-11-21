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


from lib.delta import DeltaToBestLapManager
from lib.delta.lap import Lap

from .tests_delta_base import TestF1DeltaBase

# ----------------------------------------------------------------------------------------------------------------------

class TestDeltaToBestLapManager(TestF1DeltaBase):
    """Tests for the DeltaToBestLapManager class"""

    def setUp(self):
        self.manager = DeltaToBestLapManager()

    def test_initialization(self):
        """Test manager initializes correctly"""
        self.assertEqual(len(self.manager.laps), 0)
        self.assertIsNone(self.manager.current_lap_number)
        self.assertIsNone(self.manager.best_lap_number)

    def test_start_lap(self):
        """Test starting a new lap"""
        self.manager.start_lap(1)
        self.assertEqual(self.manager.current_lap_number, 1)
        self.assertIn(1, self.manager.laps)
        self.assertIsInstance(self.manager.laps[1], Lap)

    def test_record_data_point(self):
        """Test recording data through manager"""
        # No need to call start_lap - it's automatic!
        self.assertTrue(self.manager.record_data_point(1, 100, 2.5))
        self.assertTrue(self.manager.record_data_point(1, 200, 5.0))

        lap = self.manager.laps[1]
        self.assertEqual(len(lap.data_points), 2)

    def test_record_data_point_auto_lap_transition(self):
        """Test that lap transitions happen automatically"""
        # Record data for lap 1
        self.manager.record_data_point(1, 100, 2.5)
        self.assertEqual(self.manager.current_lap_number, 1)

        # Record data for lap 2 - should auto-transition
        self.manager.record_data_point(2, 50, 1.2)
        self.assertEqual(self.manager.current_lap_number, 2)
        self.assertIn(2, self.manager.laps)

    def test_record_data_point_no_current_lap(self):
        """Test recording without starting a lap - now auto-starts"""
        # This should now work - auto-starts lap 1
        self.assertTrue(self.manager.record_data_point(1, 100, 2.5))
        self.assertEqual(self.manager.current_lap_number, 1)

    def test_set_best_lap_existing(self):
        """Test setting best lap that exists"""
        self.manager.record_data_point(1, 100, 2.5)
        self.manager.complete_current_lap(10.0)

        self.manager.set_best_lap(1)
        self.assertEqual(self.manager.best_lap_number, 1)
        self.assertIsNotNone(self.manager.get_best_lap())

    def test_set_best_lap_not_yet_available(self):
        """Test setting best lap that doesn't exist yet (tool started late)"""
        self.manager.set_best_lap(5)
        self.assertEqual(self.manager.best_lap_number, 5)
        self.assertIsNone(self.manager.get_best_lap())  # Lap 5 doesn't exist

    def test_get_delta_no_best_lap(self):
        """Test delta calculation with no best lap"""
        self.manager.record_data_point(1, 100, 2.5)

        delta = self.manager.get_delta(1, 100, 2.5)
        self.assertIsNone(delta)

    def test_get_delta_basic(self):
        """Test basic delta calculation"""
        # Create best lap
        self.manager.record_data_point(1, 0, 0.0)
        self.manager.record_data_point(1, 100, 2.5)
        self.manager.record_data_point(1, 200, 5.0)
        self.manager.complete_current_lap(5.0)
        self.manager.set_best_lap(1)

        # Start new lap (auto-starts on first data point)
        # Test faster
        delta = self.manager.get_delta(2, 100, 2.3)
        self.assertAlmostEqual(delta, -0.2, places=6)

        # Test slower
        delta = self.manager.get_delta(2, 200, 5.3)
        self.assertAlmostEqual(delta, 0.3, places=6)

    def test_get_delta_caching(self):
        """Test that caching improves performance with monotonic queries"""
        # Create best lap with many points
        for i in range(100):
            self.manager.record_data_point(1, i * 10, i * 0.25)
        self.manager.set_best_lap(1)

        # First query should set cache
        delta1 = self.manager.get_delta(2, 100, 2.5)
        cached_idx_1 = self.manager._cached_search_idx

        # Second query with higher distance should use cache
        delta2 = self.manager.get_delta(2, 200, 5.0)
        cached_idx_2 = self.manager._cached_search_idx

        # Cache index should have advanced
        self.assertGreater(cached_idx_2, cached_idx_1)

        # Starting new lap (via get_delta with new lap number) should reset cache
        delta3 = self.manager.get_delta(3, 50, 1.0)
        self.assertEqual(self.manager._cached_search_idx, 0)

    def test_handle_flashback(self):
        """Test flashback handling through manager"""
        self.manager.record_data_point(1, 100, 2.5)
        self.manager.record_data_point(1, 200, 5.0)
        self.manager.record_data_point(1, 300, 7.5)

        self.manager.handle_flashback(150)

        lap = self.manager.laps[1]
        self.assertEqual(len(lap.data_points), 1)
        self.assertFalse(lap.is_valid)

    def test_complete_current_lap(self):
        """Test completing current lap"""
        self.manager.record_data_point(1, 100, 2.5)
        self.manager.complete_current_lap(10.5)

        lap = self.manager.laps[1]
        self.assertEqual(lap.lap_time, 10.5)

    def test_invalidate_lap(self):
        """Test invalidating a specific lap"""
        self.manager.record_data_point(1, 100, 2.5)

        self.assertTrue(self.manager.laps[1].is_valid)
        self.manager.invalidate_lap(1)
        self.assertFalse(self.manager.laps[1].is_valid)

    def test_get_status(self):
        """Test status reporting"""
        self.manager.record_data_point(1, 100, 2.5)
        self.manager.complete_current_lap(10.0)
        self.manager.set_best_lap(1)

        status = self.manager.get_status()

        self.assertEqual(status['current_lap_number'], 1)
        self.assertEqual(status['best_lap_number'], 1)
        self.assertTrue(status['best_lap_available'])
        self.assertEqual(status['best_lap_time'], 10.0)
        self.assertEqual(status['total_laps'], 1)
