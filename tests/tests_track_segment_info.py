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

from lib.track_segment_info import TrackSegments
from lib.track_segment_info.types import SegmentInfo

from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestTrackSegments(F1TelemetryUnitTestsBase):

    def setUp(self):
        self.track_data = {
            "track_length": 7000,
            "segments": [
                {
                    "id": 1,
                    "name": "La Source",
                    "start_m": 0,
                    "end_m": 200,
                    "is_corner": True,
                    "corner_type": "hairpin_left"
                },
                {
                    "id": 2,
                    "name": "Eau Rouge",
                    "start_m": 200,
                    "end_m": 400,
                    "is_corner": True,
                    "corner_type": "high_speed"
                },
                {
                    "id": 3,
                    "name": "Kemmel Straight",
                    "start_m": 400,
                    "end_m": 1200,
                    "is_corner": False
                }
            ]
        }

        self.tracker = TrackSegments()
        self.tracker.load_track_data(self.track_data)

    def test_corner_segment_lookup(self):
        """Position inside a corner should return correct SegmentInfo."""
        info = self.tracker.get_segment_info(100)

        self.assertIsInstance(info, SegmentInfo)
        self.assertEqual(info.segment_id, 1)
        self.assertEqual(info.name, "La Source")
        self.assertTrue(info.is_corner)
        self.assertEqual(info.corner_type, "hairpin_left")

    def test_straight_segment_lookup(self):
        """Position inside a straight should return correct info."""
        info = self.tracker.get_segment_info(600)

        self.assertEqual(info.segment_id, 3)
        self.assertEqual(info.name, "Kemmel Straight")
        self.assertFalse(info.is_corner)
        self.assertIsNone(info.corner_type)

    def test_segment_boundary_start(self):
        """Segment should include its start boundary."""
        info = self.tracker.get_segment_info(200)

        self.assertEqual(info.segment_id, 2)

    def test_segment_boundary_end_exclusive(self):
        """Segment should exclude its end boundary."""
        info = self.tracker.get_segment_info(399)

        self.assertEqual(info.segment_id, 2)

    def test_position_outside_segments(self):
        """Position outside defined segments should return None."""
        info = self.tracker.get_segment_info(5000)

        self.assertIsNone(info)

    def test_no_track_loaded(self):
        """Calling lookup without loading data should return None."""
        tracker = TrackSegments()

        info = tracker.get_segment_info(100)

        self.assertIsNone(info)

    def test_malformed_segment_skipped(self):
        """Segments missing required fields should be ignored."""
        bad_data = {
            "track_length": 5000,
            "segments": [
                {
                    "id": 1,
                    "name": "Bad Segment",
                    "is_corner": True
                }
            ]
        }

        tracker = TrackSegments()
        tracker.load_track_data(bad_data)

        info = tracker.get_segment_info(50)

        self.assertIsNone(info)
