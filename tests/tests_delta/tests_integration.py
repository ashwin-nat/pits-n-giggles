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

from .tests_delta_base import TestF1DeltaBase

# ----------------------------------------------------------------------------------------------------------------------

class TestIntegrationScenarios(TestF1DeltaBase):
    """Integration tests for real-world scenarios"""

    def test_spin_out_scenario(self):
        """Test complete spin-out scenario"""
        manager = DeltaToBestLapManager()

        # Establish best lap
        for dist in [0, 100, 200, 300, 400, 500]:
            manager.record_data_point(1, dist, dist * 0.025)
        manager.complete_current_lap(12.5)
        manager.set_best_lap(1)

        # New lap with spin
        manager.record_data_point(2, 100, 2.4)  # Faster
        delta = manager.get_delta(2, 100, 2.4)
        self.assertLess(delta, 0)  # Ahead

        manager.record_data_point(2, 200, 5.0)

        # Spin - try to go backwards
        self.assertFalse(manager.record_data_point(2, 180, 6.0))
        self.assertFalse(manager.record_data_point(2, 190, 6.5))

        # Continue forward
        manager.record_data_point(2, 250, 7.0)
        delta = manager.get_delta(2, 250, 7.0)
        self.assertIsNotNone(delta)
        # Should be behind due to time lost in spin
        self.assertGreater(delta, 0)

    def test_flashback_scenario(self):
        """Test complete flashback scenario"""
        manager = DeltaToBestLapManager()

        # Establish best lap
        for dist in [0, 100, 200, 300, 400]:
            manager.record_data_point(1, dist, dist * 0.025)
        manager.complete_current_lap(10.0)
        manager.set_best_lap(1)

        # New lap with flashback
        manager.record_data_point(2, 100, 2.5)
        manager.record_data_point(2, 200, 5.0)
        manager.record_data_point(2, 300, 7.5)

        # Flashback to 150m
        manager.handle_flashback(150)

        lap = manager.laps[2]
        self.assertFalse(lap.is_valid)
        self.assertEqual(len(lap.data_points), 1)  # Only 100m point remains

        # Continue after flashback
        manager.record_data_point(2, 200, 5.2)
        delta = manager.get_delta(2, 200, 5.2)
        self.assertIsNotNone(delta)

        # Lap should not be eligible as best lap
        manager.complete_current_lap(9.9)  # Even though faster
        # Best lap should still be lap 1
        self.assertEqual(manager.best_lap_number, 1)

    def test_tool_started_late(self):
        """Test scenario where tool starts after best lap"""
        manager = DeltaToBestLapManager()

        # Sim says best lap is lap 3, but we don't have data
        manager.set_best_lap(3)

        # Start recording from lap 5
        manager.record_data_point(5, 100, 2.5)

        # Should return None since best lap data not available
        delta = manager.get_delta(5, 100, 2.5)
        self.assertIsNone(delta)

        # Now record lap 6 with enough data points and set it as best
        manager.complete_current_lap(10.0)
        manager.record_data_point(6, 0, 0.0)  # Need at least 2 points
        manager.record_data_point(6, 100, 2.4)
        manager.record_data_point(6, 200, 5.0)
        manager.complete_current_lap(9.8)
        manager.set_best_lap(6)

        # Now delta should work on lap 7
        manager.record_data_point(7, 100, 2.6)
        delta = manager.get_delta(7, 100, 2.6)
        self.assertIsNotNone(delta)
        self.assertGreater(delta, 0)  # Slower than best

    def test_30_lap_race(self):
        """Test realistic 30-lap race scenario"""
        manager = DeltaToBestLapManager()

        # Simulate 30 laps with varying performance
        for lap_num in range(1, 31):
            # Simulate realistic telemetry (sparse for test speed)
            base_time = 60.0 + (lap_num * 0.1)  # Slight tire degradation
            for dist in range(0, 1001, 100):
                time = (dist / 1000) * base_time
                manager.record_data_point(lap_num, dist, time)

            manager.complete_current_lap(base_time)

            # Lap 5 is fastest
            if lap_num == 5:
                manager.set_best_lap(5)

        # Verify all laps recorded
        self.assertEqual(len(manager.laps), 30)

        # Start lap 31 and check delta works
        manager.record_data_point(31, 500, 30.5)
        delta = manager.get_delta(31, 500, 30.5)
        self.assertIsNotNone(delta)
