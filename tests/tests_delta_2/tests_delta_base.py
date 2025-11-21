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

from tests_base import F1TelemetryUnitTestsBase

from lib.delta_new import LapDeltaManager

# ----------------------------------------------------------------------------------------------------------------------

class TestF1DeltaBaseV2(F1TelemetryUnitTestsBase):

    def test_basic_recording_and_forward_only(self):
        mgr = LapDeltaManager()

        mgr.record_data_point(1, 10.0, 1000)
        mgr.record_data_point(1, 20.0, 2000)

        state = mgr._dump_state()

        self.assertEqual(len(state[1]), 2)
        self.assertEqual(state[1][0], (10.0, 1000))
        self.assertEqual(state[1][1], (20.0, 2000))

    def test_backwards_movement_ignored(self):
        mgr = LapDeltaManager()

        mgr.record_data_point(1, 50.0, 3000)
        mgr.record_data_point(1, 49.0, 3100)  # backwards → should be ignored
        mgr.record_data_point(1, 70.0, 3500)

        state = mgr._dump_state()[1]

        self.assertEqual(len(state), 2)
        self.assertEqual(state[0], (50.0, 3000))
        self.assertEqual(state[1], (70.0, 3500))

    def test_start_mid_lap(self):
        mgr = LapDeltaManager()

        # sim starts at distance 300
        mgr.record_data_point(3, 300.0, 45000)
        mgr.record_data_point(3, 310.0, 46000)

        state = mgr._dump_state()[3]

        self.assertEqual(len(state), 2)
        self.assertEqual(state[0], (300.0, 45000))
        self.assertEqual(state[1], (310.0, 46000))

    def test_set_best_lap_without_data(self):
        mgr = LapDeltaManager()
        mgr.set_best_lap(5)

        mgr.record_data_point(6, 100.0, 5000)

        self.assertIsNone(mgr.get_delta())  # because best lap has no data

    def test_delta_exact_distance_match(self):
        mgr = LapDeltaManager()

        # Best lap (lap 1)
        mgr.record_data_point(1, 10.0, 1000)
        mgr.record_data_point(1, 20.0, 2000)
        mgr.set_best_lap(1)

        # Current lap (lap 2)
        mgr.record_data_point(2, 10.0, 1200)

        delta = mgr.get_delta()
        self.assertIsNotNone(delta)
        self.assertEqual(delta.delta_ms, 1200 - 1000)

    def test_delta_interpolation(self):
        mgr = LapDeltaManager()

        # best lap
        mgr.record_data_point(1, 10.0, 1000)
        mgr.record_data_point(1, 20.0, 2000)
        mgr.set_best_lap(1)

        # current lap at distance 15 → halfway between
        mgr.record_data_point(2, 15.0, 1700)

        delta = mgr.get_delta()
        self.assertIsNotNone(delta)

        # expected best time = 1500 ms
        self.assertEqual(delta.best_time_ms_at_distance, 1500)
        self.assertEqual(delta.delta_ms, 1700 - 1500)

    def test_delta_missing_best_coverage(self):
        mgr = LapDeltaManager()

        mgr.record_data_point(1, 10.0, 1000)
        mgr.set_best_lap(1)

        mgr.record_data_point(2, 50.0, 4000)  # beyond best lap's max distance

        self.assertIsNone(mgr.get_delta())

    def test_flashback_same_lap(self):
        mgr = LapDeltaManager()

        mgr.record_data_point(1, 10.0, 1000)
        mgr.record_data_point(1, 20.0, 2000)
        mgr.record_data_point(1, 30.0, 3000)

        # flashback to 18 m — remove >18m
        mgr.handle_flashback(1, 18.0)

        state = mgr._dump_state()[1]

        self.assertEqual(len(state), 2)
        self.assertEqual(state[0], (10.0, 1000))
        self.assertEqual(state[1], (20.0, 2000))

    def test_flashback_to_previous_lap(self):
        mgr = LapDeltaManager()

        # Lap 1
        mgr.record_data_point(1, 10.0, 1000)
        mgr.record_data_point(1, 50.0, 3000)

        # Lap 2
        mgr.record_data_point(2, 10.0, 1200)
        mgr.record_data_point(2, 60.0, 4000)

        # flashback to lap 1 at 20m
        mgr.handle_flashback(1, 20.0)

        state = mgr._dump_state()

        # lap 2 should be wiped entirely
        self.assertNotIn(2, state)

        # lap 1 should be trimmed
        self.assertEqual(state[1], [(10.0, 1000)])

    def test_last_recorded_point_updates_after_flashback(self):
        mgr = LapDeltaManager()

        mgr.record_data_point(1, 10.0, 1000)
        mgr.record_data_point(1, 20.0, 2000)
        mgr.record_data_point(1, 30.0, 3000)

        mgr.handle_flashback(1, 15.0)

        # now only distance 10.0 and 20.0 survive
        self.assertEqual(mgr._last_recorded_point.distance_m, 20.0)
        self.assertEqual(mgr._last_recorded_point.time_ms, 2000)

