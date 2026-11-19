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

import copy
import json
import os
import sys
import tempfile

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import allure
import pytest
from pydantic import ValidationError

from lib.f1_types.packet_2_lap_data import LapData
from lib.track_segments_classifier import TrackSegmentsDatabase
from lib.track_segments_classifier.classifier import TrackSegmentsClassifier
from lib.track_segments_classifier.types import (BaseSegmentInfo,
                                           BrakeBoardInfo,
                                           ComplexCornerSegmentInfo,
                                           CornerSegmentInfo,
                                           StraightSegmentInfo)

from tests_base import F1TelemetryUnitTestsBase

pytestmark = [allure.epic("Track data"), allure.feature("Track segments")]

# ----------------------------------------------------------------------------------------------------------------------

def load(data: dict, *, use_cache: bool) -> TrackSegmentsClassifier:
    return TrackSegmentsClassifier.model_validate({**data, "use_cache": use_cache})


@allure.story("Segment lookup")
class TestTrackSegments(F1TelemetryUnitTestsBase):

    @staticmethod
    def _track(segments: list) -> dict:
        """Wrap segments in a minimal valid top-level track dict."""
        return {
            "circuit_name": "Test Circuit", "circuit_number": 99, "track_length": 7000,
            "segments": segments, "sectors": {"s1": 2300, "s2": 5000},
        }

    def setUp(self):
        self.track_data = {
            "circuit_name": "Circuit de Spa-Francorchamps",
            "circuit_number": 12,
            "track_length": 7004,
            "segments": [
                {
                    "type": "corner",
                    "name": "La Source",
                    "start_m": 0,
                    "end_m": 200,
                    "corner_number": 1,
                },
                {
                    "type": "corner",
                    "name": "Eau Rouge",
                    "start_m": 200,
                    "end_m": 400,
                    "corner_number": 2,
                },
                {
                    "type": "straight",
                    "name": "Kemmel Straight",
                    "start_m": 400,
                    "end_m": 1200,
                },
                {
                    "type": "corner",
                    "name": "",
                    "start_m": 1200,
                    "end_m": 1400,
                    "corner_number": 3,
                },
                {
                    "type": "complex_corner",
                    "name": "Pouhon",
                    "start_m": 1400,
                    "end_m": 1800,
                    "corner_numbers": [4, 5],
                },
            ],
            "sectors": {"s1": 2332, "s2": 5011},
        }

        self.tracker = load(self.track_data, use_cache=False)

    # --- Regression: straight and corner lookups ------------------------------------------

    def test_corner_segment_lookup(self):
        """Position inside a named corner returns CornerSegmentInfo with correct fields."""
        info = self.tracker.get_segment_info(100)

        self.assertIsInstance(info, CornerSegmentInfo)
        self.assertIsInstance(info, BaseSegmentInfo)
        self.assertEqual(info.type, "corner")
        self.assertEqual(info.name, "La Source")
        self.assertEqual(info.start_m, 0)
        self.assertEqual(info.end_m, 200)
        self.assertEqual(info.corner_number, 1)

    def test_second_corner_segment_lookup(self):
        """Second named corner returns correct CornerSegmentInfo."""
        info = self.tracker.get_segment_info(300)

        self.assertIsInstance(info, CornerSegmentInfo)
        self.assertEqual(info.type, "corner")
        self.assertEqual(info.name, "Eau Rouge")
        self.assertEqual(info.corner_number, 2)

    def test_unnamed_corner_has_empty_name(self):
        """Corner with empty name string is stored correctly."""
        info = self.tracker.get_segment_info(1300)

        self.assertIsInstance(info, CornerSegmentInfo)
        self.assertEqual(info.corner_number, 3)
        self.assertEqual(info.name, "")

    def test_straight_segment_lookup(self):
        """Position inside a straight returns StraightSegmentInfo with correct fields."""
        info = self.tracker.get_segment_info(600)

        self.assertIsInstance(info, StraightSegmentInfo)
        self.assertIsInstance(info, BaseSegmentInfo)
        self.assertEqual(info.type, "straight")
        self.assertEqual(info.name, "Kemmel Straight")
        self.assertEqual(info.start_m, 400)
        self.assertEqual(info.end_m, 1200)

    def test_corner_is_not_straight(self):
        """A corner should not be an instance of StraightSegmentInfo."""
        info = self.tracker.get_segment_info(100)
        self.assertNotIsInstance(info, StraightSegmentInfo)

    def test_straight_is_not_corner(self):
        """A straight should not be an instance of CornerSegmentInfo."""
        info = self.tracker.get_segment_info(600)
        self.assertNotIsInstance(info, CornerSegmentInfo)

    # --- Complex corner parsing -----------------------------------------------------------

    def test_complex_corner_lookup(self):
        """Position inside a complex corner returns ComplexCornerSegmentInfo."""
        info = self.tracker.get_segment_info(1600)

        self.assertIsInstance(info, ComplexCornerSegmentInfo)
        self.assertIsInstance(info, BaseSegmentInfo)
        self.assertEqual(info.type, "complex_corner")
        self.assertEqual(info.name, "Pouhon")
        self.assertEqual(info.start_m, 1400)
        self.assertEqual(info.end_m, 1800)

    def test_complex_corner_corner_numbers_parsed(self):
        """corner_numbers parsed into a tuple of ints."""
        info = self.tracker.get_segment_info(1600)

        self.assertEqual(len(info.corner_numbers), 2)
        self.assertEqual(info.corner_numbers[0], 4)
        self.assertEqual(info.corner_numbers[1], 5)

    def test_complex_corner_corner_numbers_is_tuple(self):
        """corner_numbers must be an immutable tuple."""
        info = self.tracker.get_segment_info(1600)
        self.assertIsInstance(info.corner_numbers, tuple)

    def test_complex_corner_is_not_corner_or_straight(self):
        """A complex_corner must not be an instance of CornerSegmentInfo or StraightSegmentInfo."""
        info = self.tracker.get_segment_info(1600)
        self.assertNotIsInstance(info, CornerSegmentInfo)
        self.assertNotIsInstance(info, StraightSegmentInfo)

    # --- Boundary conditions --------------------------------------------------------------

    def test_segment_boundary_start_inclusive(self):
        """Exactly at start_m should be inside the segment."""
        info = self.tracker.get_segment_info(200)
        self.assertIsInstance(info, CornerSegmentInfo)
        self.assertEqual(info.corner_number, 2)

    def test_segment_boundary_end_exclusive(self):
        """Exactly at end_m should NOT be inside the segment."""
        info = self.tracker.get_segment_info(1200)
        # 1200 is start of the unnamed corner (id 4), not end of straight
        self.assertIsInstance(info, CornerSegmentInfo)
        self.assertEqual(info.corner_number, 3)

    def test_position_just_before_end_is_inside(self):
        """One meter before end_m should still be inside the segment."""
        info = self.tracker.get_segment_info(399)
        self.assertIsInstance(info, CornerSegmentInfo)
        self.assertEqual(info.corner_number, 2)

    def test_position_outside_segments_returns_none(self):
        """Position beyond all segments returns None."""
        info = self.tracker.get_segment_info(5000)
        self.assertIsNone(info)

    def test_negative_position_returns_none(self):
        """Negative position returns None."""
        info = self.tracker.get_segment_info(-1)
        self.assertIsNone(info)

    def test_pre_start_position_returns_none(self):
        """Position just before the first segment start returns None."""
        info = self.tracker.get_segment_info(-0.1)
        self.assertIsNone(info)

    # --- Lap wraparound (sim outlap negatives / start-finish line) -------------------------

    def test_negative_position_wraps_onto_last_segment(self):
        """Sim-emitted negative lap_distance (e.g. during an outlap) wraps onto the end of the lap."""
        segments = [
            {"type": "straight", "name": "A", "start_m": 0,    "end_m": 6900},
            {"type": "corner",   "name": "B", "start_m": 6900, "end_m": 7000, "corner_number": 1},
        ]
        tracker = load(self._track(segments), use_cache=False)

        info = tracker.get_segment_info(-1)  # -1 % 7000 == 6999
        self.assertIsInstance(info, CornerSegmentInfo)
        self.assertEqual(info.name, "B")

    def test_position_at_exactly_track_length_wraps_to_zero(self):
        """Position exactly at track_length wraps to the start of the lap (0)."""
        segments = [
            {"type": "corner", "name": "Start Corner", "start_m": 0, "end_m": 200, "corner_number": 1},
        ]
        tracker = load(self._track(segments), use_cache=False)

        info = tracker.get_segment_info(7000)  # == track_length -> wraps to 0
        self.assertIsInstance(info, CornerSegmentInfo)
        self.assertEqual(info.name, "Start Corner")

    # --- Validation: missing required base fields -----------------------------------------

    def test_validation_missing_type(self):
        """Missing 'type' field raises ValueError."""
        bad = {"name": "X", "start_m": 0, "end_m": 100}
        with self.assertRaises(ValidationError):
            load(self._track([bad]), use_cache=False)

    def test_validation_missing_name(self):
        """Missing 'name' field raises ValueError."""
        bad = {"type": "straight", "start_m": 0, "end_m": 100}
        with self.assertRaises(ValidationError):
            load(self._track([bad]), use_cache=False)

    def test_validation_missing_start_m(self):
        """Missing 'start_m' field raises ValueError."""
        bad = {"type": "straight", "name": "X", "end_m": 100}
        with self.assertRaises(ValidationError):
            load(self._track([bad]), use_cache=False)

    def test_validation_missing_end_m(self):
        """Missing 'end_m' field raises ValueError."""
        bad = {"type": "straight", "name": "X", "start_m": 0}
        with self.assertRaises(ValidationError):
            load(self._track([bad]), use_cache=False)

    def test_validation_corner_missing_corner_number(self):
        """Corner segment without 'corner_number' raises ValueError."""
        bad = {"type": "corner", "name": "X", "start_m": 0, "end_m": 100}
        with self.assertRaises(ValidationError):
            load(self._track([bad]), use_cache=False)

    def test_validation_complex_corner_missing_corners(self):
        """Complex corner without 'corner_numbers' raises ValueError."""
        bad = {"type": "complex_corner", "name": "X", "start_m": 0, "end_m": 100}
        with self.assertRaises(ValidationError):
            load(self._track([bad]), use_cache=False)

    def test_validation_unknown_type(self):
        """Unknown segment type raises ValidationError."""
        bad = {"type": "chicane", "name": "X", "start_m": 0, "end_m": 100}
        with self.assertRaises(ValidationError):
            load(self._track([bad]), use_cache=False)

    def test_validation_start_m_equal_to_end_m(self):
        """start_m == end_m raises ValidationError."""
        bad = {"type": "straight", "name": "X", "start_m": 100, "end_m": 100}
        with self.assertRaises(ValidationError):
            load(self._track([bad]), use_cache=False)

    def test_validation_start_m_greater_than_end_m(self):
        """start_m > end_m raises ValidationError."""
        bad = {"type": "straight", "name": "X", "start_m": 200, "end_m": 100}
        with self.assertRaises(ValidationError):
            load(self._track([bad]), use_cache=False)

    # --- Ordering and overlap validation --------------------------------------------------

    def test_validation_segments_out_of_order(self):
        """Segments with decreasing start_m raise ValidationError."""
        segments = [
            {"type": "straight", "name": "B", "start_m": 500, "end_m": 1000},
            {"type": "straight", "name": "A", "start_m": 0,   "end_m": 500},
        ]
        with self.assertRaises(ValidationError):
            load(self._track(segments), use_cache=False)

    def test_validation_segments_overlapping(self):
        """Segment whose start_m falls inside the previous segment raises ValidationError."""
        segments = [
            {"type": "straight", "name": "A", "start_m": 0,   "end_m": 600},
            {"type": "straight", "name": "B", "start_m": 400, "end_m": 1000},
        ]
        with self.assertRaises(ValidationError):
            load(self._track(segments), use_cache=False)

    def test_validation_adjacent_segments_exact_boundary(self):
        """Segments where start_m of next == end_m of previous are valid (no gap, no overlap)."""
        segments = [
            {"type": "straight", "name": "A", "start_m": 0,   "end_m": 500},
            {"type": "straight", "name": "B", "start_m": 500, "end_m": 1000},
        ]
        tracker = load(self._track(segments), use_cache=False)  # must not raise

    # --- Top-level schema fields ----------------------------------------------------------

    def test_top_level_circuit_name(self):
        """circuit_name is accessible on the tracker after loading."""
        self.assertEqual(self.tracker.circuit_name, "Circuit de Spa-Francorchamps")

    def test_top_level_circuit_number(self):
        """circuit_number is accessible on the tracker after loading."""
        self.assertEqual(self.tracker.circuit_number, 12)

    def test_top_level_missing_circuit_name(self):
        """Missing circuit_name raises ValidationError."""
        data = {"circuit_number": 1, "track_length": 1000, "segments": []}
        with self.assertRaises(ValidationError):
            load(data, use_cache=False)

    def test_top_level_missing_circuit_number(self):
        """Missing circuit_number raises ValidationError."""
        data = {"circuit_name": "X", "track_length": 1000, "segments": []}
        with self.assertRaises(ValidationError):
            load(data, use_cache=False)

    def test_top_level_missing_track_length(self):
        """Missing track_length raises ValidationError."""
        data = {"circuit_name": "X", "circuit_number": 1, "segments": []}
        with self.assertRaises(ValidationError):
            load(data, use_cache=False)

    # --- Lookup correctness for all three segment types -----------------------------------

    def test_lookup_returns_straight_type(self):
        """Lookup inside a straight returns type == 'straight'."""
        info = self.tracker.get_segment_info(800)
        self.assertEqual(info.type, "straight")

    def test_lookup_returns_corner_type(self):
        """Lookup inside a corner returns type == 'corner'."""
        info = self.tracker.get_segment_info(50)
        self.assertEqual(info.type, "corner")

    def test_lookup_returns_complex_corner_type(self):
        """Lookup inside a complex_corner returns type == 'complex_corner'."""
        info = self.tracker.get_segment_info(1500)
        self.assertEqual(info.type, "complex_corner")

    # --- segment_id ------------------------------------------------------------------------

    def test_segment_id_matches_array_position(self):
        """segment_id reflects the segment's position in the loaded segment array."""
        self.assertEqual(self.tracker.get_segment_info(100).segment_id, 0)    # La Source
        self.assertEqual(self.tracker.get_segment_info(300).segment_id, 1)    # Eau Rouge
        self.assertEqual(self.tracker.get_segment_info(600).segment_id, 2)    # Kemmel Straight
        self.assertEqual(self.tracker.get_segment_info(1300).segment_id, 3)   # unnamed corner
        self.assertEqual(self.tracker.get_segment_info(1600).segment_id, 4)   # Pouhon

    def test_segment_id_stable_across_repeated_lookups(self):
        """Repeated lookups of the same position return the same segment_id."""
        first = self.tracker.get_segment_info(100).segment_id
        second = self.tracker.get_segment_info(100).segment_id
        self.assertEqual(first, second)

    def test_segment_id_stamped_in_array_order(self):
        """segment_id is stamped from the position in the segment array, not taken from the input."""
        reordered = self._track([
            {"type": "straight", "name": "New Straight", "start_m": 0, "end_m": 500},
            {"type": "corner", "name": "New Corner", "start_m": 500, "end_m": 700, "corner_number": 1},
        ])
        tracker = load(reordered, use_cache=False)

        self.assertEqual(tracker.get_segment_info(100).segment_id, 0)
        self.assertEqual(tracker.get_segment_info(600).segment_id, 1)


# ----------------------------------------------------------------------------------------------------------------------

@allure.story("Lookup cache")
class TestLastSegmentCache(F1TelemetryUnitTestsBase):
    """Exercises the last-segment cache of TrackSegmentsClassifier.get_segment_info."""

    def setUp(self):
        self.track_data = {
            "circuit_name": "Cache Test Circuit",
            "circuit_number": 1,
            "track_length": 1000,
            "sectors": {"s1": 400, "s2": 700},
            "segments": [
                {"type": "straight", "name": "Start Straight", "start_m": 0,   "end_m": 400},
                {"type": "corner",   "name": "Turn One",       "start_m": 400, "end_m": 600, "corner_number": 1},
                {"type": "straight", "name": "Back Straight",  "start_m": 600, "end_m": 900},
                # 900-1000 is an intentional gap: with lap-distance wraparound, a track that
                # covers its full length has no "outside all segments" position left to test.
            ],
        }
        self.tracker = load(self.track_data, use_cache=True)

    def test_repeated_lookup_same_segment_returns_same_object(self):
        """Consecutive lookups within the same segment hit the cache and return the same instance."""
        first = self.tracker.get_segment_info(50)
        second = self.tracker.get_segment_info(60)
        self.assertIsNotNone(first)
        self.assertIs(first, second)

    def test_lookup_advancing_to_next_segment_updates_cache(self):
        """Moving lap_distance forward into a new segment returns the new segment, not the cached one."""
        first = self.tracker.get_segment_info(100)
        second = self.tracker.get_segment_info(450)
        self.assertEqual(first.name, "Start Straight")
        self.assertEqual(second.name, "Turn One")
        self.assertIsNot(first, second)

    def test_lookup_moving_backward_updates_cache(self):
        """Lap distance moving backward (e.g. new lap) still resolves to the correct segment."""
        self.tracker.get_segment_info(700)
        info = self.tracker.get_segment_info(50)
        self.assertEqual(info.name, "Start Straight")

    def test_cache_miss_after_segment_then_gap_returns_none(self):
        """Moving from a cached segment into a gap position returns None, not the stale segment."""
        self.tracker.get_segment_info(100)
        info = self.tracker.get_segment_info(950)  # falls in the intentional 900-1000 gap
        self.assertIsNone(info)

    def test_lookup_after_none_recovers_correct_segment(self):
        """A lookup that misses (returns None) does not poison later lookups that should hit."""
        self.tracker.get_segment_info(950)  # falls in the intentional 900-1000 gap
        info = self.tracker.get_segment_info(450)
        self.assertEqual(info.name, "Turn One")

    def test_boundary_transition_end_exclusive_via_cache(self):
        """Landing exactly on a segment's end_m must not be served by the stale cached segment."""
        first = self.tracker.get_segment_info(300)
        self.assertEqual(first.name, "Start Straight")
        second = self.tracker.get_segment_info(400)
        self.assertEqual(second.name, "Turn One")


# ----------------------------------------------------------------------------------------------------------------------

@allure.story("Segment validation")
class TestSegmentValidation(F1TelemetryUnitTestsBase):
    """Cross-segment checks: lap bounds and corner numbering."""

    @staticmethod
    def _track(segments: list, track_length: float = 1000) -> dict:
        return {"circuit_name": "Validation Circuit", "circuit_number": 1, "track_length": track_length,
                "sectors": {"s1": 300, "s2": 700}, "segments": segments}

    @staticmethod
    def _corner(start: float, end: float, number: int) -> dict:
        return {"type": "corner", "name": "", "start_m": start, "end_m": end, "corner_number": number}

    @staticmethod
    def _complex(start: float, end: float, numbers: list) -> dict:
        return {"type": "complex_corner", "name": "", "start_m": start, "end_m": end, "corner_numbers": numbers}

    @staticmethod
    def _straight(start: float, end: float) -> dict:
        return {"type": "straight", "name": "S", "start_m": start, "end_m": end}

    def _assert_invalid(self, segments: list, message: str, track_length: float = 1000) -> None:
        with self.assertRaisesRegex(ValidationError, message):
            load(self._track(segments, track_length), use_cache=False)

    # --- Corner numbering -----------------------------------------------------------------

    def test_first_corner_not_one_raises(self):
        """Numbering that starts above 1 is rejected and names the missing numbers."""
        self._assert_invalid([self._corner(0, 100, 2)], "missing 1 before corner 2")

    def test_duplicate_corner_number_raises(self):
        """The same corner number on two segments is rejected."""
        self._assert_invalid([self._corner(0, 100, 1), self._corner(200, 300, 1)], "duplicate or out of order")

    def test_out_of_order_corner_numbers_raise(self):
        """A corner number lower than one already seen is rejected."""
        self._assert_invalid(
            [self._corner(0, 100, 1), self._corner(200, 300, 3), self._corner(400, 500, 2)],
            "missing 2 before corner 3",
        )

    def test_gap_between_corners_raises(self):
        """A skipped corner number between two corner segments is rejected, listing every missing number."""
        self._assert_invalid([self._corner(0, 100, 1), self._corner(200, 300, 4)], "missing 2, 3 before corner 4")

    def test_gap_between_corner_and_complex_corner_raises(self):
        """Corner and complex_corner numbers are counted together."""
        self._assert_invalid([self._corner(0, 100, 1), self._complex(200, 400, [3, 4])], "missing 2 before corner 3")

    def test_duplicate_across_corner_and_complex_corner_raises(self):
        """A corner number repeated between a corner and a complex_corner is rejected."""
        self._assert_invalid(
            [self._corner(0, 100, 1), self._complex(200, 400, [1, 2])], "duplicate or out of order"
        )

    def test_complex_corner_first_not_one_raises(self):
        """A complex_corner that opens the lap must start at 1."""
        self._assert_invalid([self._complex(0, 200, [2, 3])], "missing 1 before corner 2")

    def test_valid_numbering_with_straights_and_complex_corners(self):
        """Contiguous 1..N across corners, complex corners and straights loads."""
        track = load(self._track([
            self._corner(0, 100, 1),
            self._straight(100, 200),
            self._complex(200, 400, [2, 3]),
            self._straight(400, 500),
            self._corner(500, 600, 4),
        ]), use_cache=False)
        self.assertEqual(len(track.segments), 5)

    def test_track_without_corners_is_valid(self):
        """A track with no corner segments has nothing to number and loads."""
        load(self._track([self._straight(0, 500)]), use_cache=False)

    # --- Lap bounds -----------------------------------------------------------------------

    def test_segment_starting_below_zero_raises(self):
        """A segment with start_m below 0 is rejected."""
        self._assert_invalid([self._straight(-10, 100)], "starts before the lap")

    def test_segment_ending_past_track_length_raises(self):
        """A segment with end_m past track_length is rejected."""
        self._assert_invalid([self._straight(900, 1001)], "ends past the lap")

    def test_segment_ending_exactly_at_track_length_is_valid(self):
        """end_m equal to track_length is allowed (end is exclusive)."""
        load(self._track([self._straight(900, 1000)]), use_cache=False)


    # --- Track length and non-finite values -----------------------------------------------

    def test_zero_track_length_raises(self):
        """track_length of 0 is rejected at load rather than dividing by zero in lookups."""
        self._assert_invalid([], "track_length", track_length=0)

    def test_negative_track_length_raises(self):
        """A negative track_length is rejected."""
        self._assert_invalid([], "track_length", track_length=-100)

    def test_non_finite_track_length_raises(self):
        """NaN and infinite track_length are rejected."""
        for value in (float("nan"), float("inf")):
            with self.subTest(value=value):
                self._assert_invalid([], "track_length", track_length=value)

    def test_non_finite_segment_bounds_raise(self):
        """NaN and infinite start_m / end_m are rejected, since NaN slips past the ordering comparisons."""
        for field in ("start_m", "end_m"):
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(field=field, value=value):
                    seg = self._straight(0, 100)
                    seg[field] = value
                    self._assert_invalid([seg], field)

    # --- Immutability ---------------------------------------------------------------------

    def test_segments_are_immutable(self):
        """segments is a tuple, so callers cannot change it behind the cached start positions."""
        track = load(self._track([self._straight(0, 500)]), use_cache=False)
        self.assertIsInstance(track.segments, tuple)
        self.assertIsInstance(track.starts, tuple)
        with self.assertRaises(AttributeError):
            track.segments.append(self._straight(500, 900))

# ----------------------------------------------------------------------------------------------------------------------

@allure.story("Lookup cache")
class TestClassifierCacheToggle(F1TelemetryUnitTestsBase):

    _DATA = {
        "circuit_name": "Toggle Circuit",
        "circuit_number": 1,
        "track_length": 1000,
        "sectors": {"s1": 300, "s2": 700},
        "segments": [
            {"type": "straight", "name": "A", "start_m": 0,   "end_m": 400},
            {"type": "corner",   "name": "B", "start_m": 400, "end_m": 600, "corner_number": 1},
            {"type": "straight", "name": "C", "start_m": 600, "end_m": 900},
        ],
    }

    def test_use_cache_is_required(self):
        """Constructing without use_cache raises ValidationError."""
        with self.assertRaises(ValidationError):
            TrackSegmentsClassifier.model_validate(self._DATA)

    def test_cache_on_and_off_agree(self):
        """Cached and uncached classifiers return identical segments for the same positions."""
        on = load(self._DATA, use_cache=True)
        off = load(self._DATA, use_cache=False)
        positions = [0, 399, 400, 399, 599.9, 600, 899, 900, 950, 100, -1, 1000, 2450, 450, 50]
        for pos in positions:
            self.assertEqual(on.get_segment_info(pos), off.get_segment_info(pos), pos)

    def test_cache_not_populated_when_disabled(self):
        """With use_cache=False the cache state is never written."""
        off = load(self._DATA, use_cache=False)
        off.get_segment_info(100)
        self.assertIsNone(off.cache.last)

    def test_cache_excluded_from_model_dump(self):
        """The cache is internal state and does not appear in model_dump()."""
        on = load(self._DATA, use_cache=True)
        on.get_segment_info(100)
        self.assertNotIn("cache", on.model_dump())

    def test_model_is_frozen(self):
        """Assigning to a field raises ValidationError."""
        on = load(self._DATA, use_cache=True)
        with self.assertRaises(ValidationError):
            on.track_length = 5


# ----------------------------------------------------------------------------------------------------------------------

@allure.story("Segment dict")
class TestSegmentDict(F1TelemetryUnitTestsBase):

    def test_straight_named_Dict(self):
        """Named straight dict contains type and name."""
        seg = StraightSegmentInfo(name="Kemmel Straight", start_m=400, end_m=1200)
        self.assertEqual(seg.to_dict(), {"type": "straight", "name": "Kemmel Straight"})

    def test_straight_empty_name_raises(self):
        """Empty name on a straight raises ValidationError."""
        with self.assertRaises(ValidationError):
            StraightSegmentInfo(name="", start_m=0, end_m=100)

    def test_straight_missing_name_raises(self):
        """Missing name on a straight raises ValidationError."""
        with self.assertRaises(ValidationError):
            StraightSegmentInfo(start_m=0, end_m=100)

    def test_corner_named_dict(self):
        """Named corner dict contains type, name, and corner_number."""
        seg = CornerSegmentInfo(name="La Source", start_m=0, end_m=200, corner_number=1)
        self.assertEqual(seg.to_dict(), {"type": "corner", "name": "La Source", "corner_number": 1})

    def test_corner_unnamed_dict(self):
        """Unnamed corner dict contains with type, empty name, and corner_number."""
        seg = CornerSegmentInfo(name="", start_m=0, end_m=200, corner_number=3)
        self.assertEqual(seg.to_dict(), {"type": "corner", "name": "", "corner_number": 3})

    def test_complex_corner_named_dict(self):
        """Named complex corner dict contains type=complex_corner, name, and corner_numbers list."""
        seg = ComplexCornerSegmentInfo(name="Pouhon", start_m=1400, end_m=1800, corner_numbers=(6, 7))
        self.assertEqual(seg.to_dict(), {"type": "complex_corner", "name": "Pouhon", "corner_numbers": [6, 7]})

    def test_complex_corner_unnamed_dict(self):
        """Unnamed complex corner dict contains with type=complex_corner, empty name, and corner_numbers list."""
        seg = ComplexCornerSegmentInfo(name="", start_m=0, end_m=500, corner_numbers=(1, 2, 3))
        self.assertEqual(seg.to_dict(), {"type": "complex_corner", "name": "", "corner_numbers": [1, 2, 3]})

    def test_complex_corner_unnamed_two_turns_dict(self):
        """Unnamed complex corner with 2 turns dict contains corner_numbers list."""
        seg = ComplexCornerSegmentInfo(name="", start_m=0, end_m=500, corner_numbers=(3, 4))
        self.assertEqual(seg.to_dict(), {"type": "complex_corner", "name": "", "corner_numbers": [3, 4]})

    def test_complex_corner_two_turns_dict(self):
        """Complex corner with exactly 2 turns dict contains corner_numbers list."""
        seg = ComplexCornerSegmentInfo(name="Esses", start_m=0, end_m=500, corner_numbers=(3, 4))
        self.assertEqual(seg.to_dict(), {"type": "complex_corner", "name": "Esses", "corner_numbers": [3, 4]})

    def test_complex_corner_many_turns_dict(self):
        """Complex corner with >2 turns dict contains corner_numbers list."""
        seg = ComplexCornerSegmentInfo(name="Maggotts-Becketts", start_m=0, end_m=800, corner_numbers=(5, 6, 7, 8))
        self.assertEqual(seg.to_dict(), {"type": "complex_corner", "name": "Maggotts-Becketts", "corner_numbers": [5, 6, 7, 8]})

    # --- name optionality rules -------------------------------------------------------

    def test_corner_name_defaults_to_empty(self):
        """CornerSegmentInfo is valid without a name field."""
        seg = CornerSegmentInfo(start_m=0, end_m=100, corner_number=1)
        self.assertEqual(seg.name, "")

    def test_corner_empty_name_is_valid(self):
        """CornerSegmentInfo with explicit empty name is valid."""
        seg = CornerSegmentInfo(name="", start_m=0, end_m=100, corner_number=1)
        self.assertEqual(seg.name, "")

    def test_complex_corner_name_defaults_to_empty(self):
        """ComplexCornerSegmentInfo is valid without a name field."""
        seg = ComplexCornerSegmentInfo(start_m=0, end_m=100, corner_numbers=(1, 2))
        self.assertEqual(seg.name, "")

    def test_complex_corner_empty_name_is_valid(self):
        """ComplexCornerSegmentInfo with explicit empty name is valid."""
        seg = ComplexCornerSegmentInfo(name="", start_m=0, end_m=100, corner_numbers=(1, 2))
        self.assertEqual(seg.name, "")

    def test_complex_corner_non_continuous_raises(self):
        """Non-continuous corner_numbers raises ValidationError."""
        with self.assertRaises(ValidationError):
            ComplexCornerSegmentInfo(name="X", start_m=0, end_m=100, corner_numbers=(1, 3, 5))

    def test_complex_corner_non_increasing_raises(self):
        """Non-increasing corner_numbers raises ValidationError."""
        with self.assertRaises(ValidationError):
            ComplexCornerSegmentInfo(name="X", start_m=0, end_m=100, corner_numbers=(3, 2, 1))

    def test_complex_corner_single_number_raises(self):
        """Single corner_number raises ValidationError (need at least 2)."""
        with self.assertRaises(ValidationError):
            ComplexCornerSegmentInfo(name="X", start_m=0, end_m=100, corner_numbers=(1,))


# ----------------------------------------------------------------------------------------------------------------------

@allure.story("Sectors")
class TestGetSector(F1TelemetryUnitTestsBase):

    _S1 = 500
    _S2 = 1500
    _TRACK_LENGTH = 3000

    @staticmethod
    def _track_with_sectors(sectors, track_length=3000):
        return {
            "circuit_name": "Sector Test Circuit",
            "circuit_number": 1,
            "track_length": track_length,
            "segments": [],
            "sectors": sectors,
        }

    def setUp(self):
        self.tracker = load(
            self._track_with_sectors({"s1": self._S1, "s2": self._S2}, self._TRACK_LENGTH),
            use_cache=False,
        )

    # --- Sector 1 -------------------------------------------------------------------------

    def test_sector_1_at_zero(self):
        """Position 0 is in SECTOR1."""
        self.assertEqual(self.tracker.get_sector(0), LapData.Sector.SECTOR1)

    def test_sector_1_mid(self):
        """Position in the middle of S1 returns SECTOR1."""
        self.assertEqual(self.tracker.get_sector(250), LapData.Sector.SECTOR1)

    def test_sector_1_just_before_s1(self):
        """Position just before s1 is still in SECTOR1."""
        self.assertEqual(self.tracker.get_sector(499), LapData.Sector.SECTOR1)

    # --- Sector 2 -------------------------------------------------------------------------

    def test_sector_2_at_s1(self):
        """Position exactly at s1 is in SECTOR2."""
        self.assertEqual(self.tracker.get_sector(500), LapData.Sector.SECTOR2)

    def test_sector_2_mid(self):
        """Position in the middle of S2 returns SECTOR2."""
        self.assertEqual(self.tracker.get_sector(1000), LapData.Sector.SECTOR2)

    def test_sector_2_just_before_s2(self):
        """Position just before s2 is still in SECTOR2."""
        self.assertEqual(self.tracker.get_sector(1499), LapData.Sector.SECTOR2)

    # --- Sector 3 -------------------------------------------------------------------------

    def test_sector_3_at_s2(self):
        """Position exactly at s2 is in SECTOR3."""
        self.assertEqual(self.tracker.get_sector(1500), LapData.Sector.SECTOR3)

    def test_sector_3_mid(self):
        """Position in the middle of S3 returns SECTOR3."""
        self.assertEqual(self.tracker.get_sector(2500), LapData.Sector.SECTOR3)

    def test_sector_3_just_before_track_length(self):
        """Position just before track_length is still in SECTOR3."""
        self.assertEqual(self.tracker.get_sector(2999), LapData.Sector.SECTOR3)

    # --- Out of range ---------------------------------------------------------------------

    def test_at_track_length_returns_sector_1(self):
        """Position exactly at track_length wraps to lap start and returns SECTOR1."""
        self.assertEqual(self.tracker.get_sector(3000), LapData.Sector.SECTOR1)

    def test_beyond_track_length_wraps_to_correct_sector(self):
        """Position beyond track_length wraps onto the lap and returns the corresponding sector."""
        self.assertEqual(self.tracker.get_sector(5000), LapData.Sector.SECTOR3)  # 5000 % 3000 == 2000

    def test_negative_position_wraps_to_correct_sector(self):
        """Negative position (e.g. sim outlap) wraps onto the end of the lap and returns the correct sector."""
        self.assertEqual(self.tracker.get_sector(-1), LapData.Sector.SECTOR3)  # -1 % 3000 == 2999

    # --- No data --------------------------------------------------------------------------

    def test_sectors_missing_key_raises(self):
        """sectors is a required field -- a track with no sectors key fails validation."""
        data = self._track_with_sectors({"s1": self._S1, "s2": self._S2})
        del data["sectors"]
        with self.assertRaises(ValidationError):
            load(data, use_cache=False)

    # --- Validation -----------------------------------------------------------------------

    def test_sectors_s1_equal_s2_raises(self):
        """s1 == s2 raises ValidationError."""
        with self.assertRaises(ValidationError):
            load(self._track_with_sectors({"s1": 500, "s2": 500}), use_cache=False)

    def test_sectors_s1_greater_than_s2_raises(self):
        """s1 > s2 raises ValidationError."""
        with self.assertRaises(ValidationError):
            load(self._track_with_sectors({"s1": 1500, "s2": 500}), use_cache=False)

    def test_sectors_missing_s1_raises(self):
        """sectors without s1 raises ValidationError."""
        with self.assertRaises(ValidationError):
            load(self._track_with_sectors({"s2": 1500}), use_cache=False)

    def test_sectors_missing_s2_raises(self):
        """sectors without s2 raises ValidationError."""
        with self.assertRaises(ValidationError):
            load(self._track_with_sectors({"s1": 500}), use_cache=False)

    def test_sectors_s1_zero_raises(self):
        """s1 == 0 raises ValidationError (SECTOR1 would be unreachable)."""
        with self.assertRaises(ValidationError):
            load(self._track_with_sectors({"s1": 0, "s2": 500}), use_cache=False)

    def test_sectors_s1_negative_raises(self):
        """Negative s1 raises ValidationError."""
        with self.assertRaises(ValidationError):
            load(self._track_with_sectors({"s1": -100, "s2": 500}), use_cache=False)

    def test_sectors_s2_equal_track_length_raises(self):
        """s2 == track_length raises ValidationError (SECTOR3 would be unreachable)."""
        with self.assertRaises(ValidationError):
            load(self._track_with_sectors({"s1": 500, "s2": 3000}, track_length=3000), use_cache=False)

    def test_sectors_s2_greater_than_track_length_raises(self):
        """s2 > track_length raises ValidationError."""
        with self.assertRaises(ValidationError):
            load(self._track_with_sectors({"s1": 500, "s2": 4000}, track_length=3000), use_cache=False)


# ----------------------------------------------------------------------------------------------------------------------

_CIRCUIT_A = {
    "circuit_name": "Alpha Circuit",
    "circuit_number": 1,
    "track_length": 1000,
    "segments": [
        {"type": "straight", "name": "Main Straight", "start_m": 0,   "end_m": 500},
        {"type": "corner",   "name": "Turn One",      "start_m": 500, "end_m": 700, "corner_number": 1},
    ],
    "sectors": {"s1": 300, "s2": 700},
}

_CIRCUIT_B = {
    "circuit_name": "Beta Circuit",
    "circuit_number": 2,
    "track_length": 400,
    "segments": [
        {"type": "corner", "name": "Hairpin", "start_m": 0, "end_m": 300, "corner_number": 1},
    ],
    "sectors": {"s1": 100, "s2": 250},
}

_CIRCUIT_C = {
    "circuit_name": "Gamma Circuit",
    "circuit_number": 3,
    "track_length": 1000,
    "segments": [],
    "sectors": {"s1": 300, "s2": 700},
}


@allure.story("Database")
class TestTrackSegmentsDatabase(F1TelemetryUnitTestsBase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        for circuit in (_CIRCUIT_A, _CIRCUIT_B, _CIRCUIT_C):
            path = os.path.join(self._tmp.name, f"{circuit['circuit_name']}.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(circuit, fh)
        self.db = TrackSegmentsDatabase(self._tmp.name, cache=False)

    def tearDown(self):
        self._tmp.cleanup()

    # --- Presence and counts ------------------------------------------------------------------

    def test_len_equals_number_of_files(self):
        """Database length equals the number of JSON files loaded."""
        self.assertEqual(len(self.db), 3)

    def test_contains_known_circuit(self):
        """Known circuit number is found via 'in'."""
        self.assertIn(1, self.db)

    def test_not_contains_unknown_circuit(self):
        """Unknown circuit number is not found via 'in'."""
        self.assertNotIn(999, self.db)

    def test_iter_yields_all_circuit_numbers(self):
        """Iterating the database yields all circuit numbers."""
        self.assertEqual(set(self.db), {1, 2, 3})

    # --- get() --------------------------------------------------------------------------------

    def test_get_returns_track_segments_instance(self):
        """get() returns a TrackSegments instance for a known circuit number."""
        ts = self.db.get(1)
        self.assertIsInstance(ts, TrackSegmentsClassifier)

    def test_get_unknown_returns_none(self):
        """get() returns None for an unknown circuit number."""
        self.assertIsNone(self.db.get(999))

    # --- __getitem__ --------------------------------------------------------------------------

    def test_getitem_known_circuit(self):
        """__getitem__ returns the TrackSegments for a known circuit number."""
        ts = self.db[2]
        self.assertIsInstance(ts, TrackSegmentsClassifier)
        self.assertEqual(ts.circuit_name, "Beta Circuit")

    def test_getitem_unknown_raises_key_error(self):
        """__getitem__ raises KeyError for an unknown circuit number."""
        with self.assertRaises(KeyError):
            _ = self.db[999]

    # --- get_segment_info() -------------------------------------------------------------------

    def test_get_segment_info_returns_correct_segment(self):
        """get_segment_info returns the right segment for a known circuit number and position."""
        seg = self.db.get_segment_info(1, 250)
        self.assertIsInstance(seg, StraightSegmentInfo)
        self.assertEqual(seg.name, "Main Straight")

    def test_get_segment_info_corner(self):
        """get_segment_info returns a corner segment at the right position."""
        seg = self.db.get_segment_info(1, 600)
        self.assertIsInstance(seg, CornerSegmentInfo)
        self.assertEqual(seg.corner_number, 1)

    def test_get_segment_info_outside_range_returns_none(self):
        """get_segment_info returns None for a position outside all segments."""
        seg = self.db.get_segment_info(1, 9999)
        self.assertIsNone(seg)

    def test_get_segment_info_unknown_circuit_returns_none(self):
        """get_segment_info returns None for an unknown circuit number."""
        seg = self.db.get_segment_info(999, 100)
        self.assertIsNone(seg)

    # --- Empty directory ----------------------------------------------------------------------

    def test_empty_directory_has_zero_circuits(self):
        """Database built from an empty directory has length 0."""
        with tempfile.TemporaryDirectory() as empty:
            db = TrackSegmentsDatabase(empty, cache=False)
            self.assertEqual(len(db), 0)

    # --- Error handling -----------------------------------------------------------------------

    def test_invalid_directory_raises_file_not_found(self):
        """Non-existent directory should fail fast."""
        missing = os.path.join(self._tmp.name, "does_not_exist")
        with self.assertRaises(FileNotFoundError):
            TrackSegmentsDatabase(missing, cache=False)

    def test_invalid_json_raises_decode_error(self):
        """Malformed JSON should bubble up as a decode error. Track files are
        repo-controlled assets, not untrusted runtime input -- a bad one should fail
        loudly at startup/dev time, not be silently skipped."""
        bad_json = os.path.join(self._tmp.name, "bad.json")
        with open(bad_json, "w", encoding="utf-8") as fh:
            fh.write("{ not-valid-json }")
        with self.assertRaises(json.JSONDecodeError):
            TrackSegmentsDatabase(self._tmp.name, cache=False)

    def _write(self, name: str, circuit: dict) -> None:
        with open(os.path.join(self._tmp.name, name), "w", encoding="utf-8") as fh:
            json.dump(circuit, fh)

    def test_duplicate_circuit_number_raises(self):
        """Two files with the same circuit_number fail construction and name both files."""
        self._write("zz_dup.json", {**_CIRCUIT_A, "circuit_name": "Duplicate of Alpha"})
        with self.assertRaises(ValueError) as ctx:
            TrackSegmentsDatabase(self._tmp.name, cache=False)
        message = str(ctx.exception)
        self.assertIn("zz_dup.json", message)
        self.assertIn(f"{_CIRCUIT_A['circuit_name']}.json", message)

    def test_invalid_file_fails_construction(self):
        """A file that fails validation fails the whole database and the error names the file."""
        bad = {"circuit_name": "Bad", "circuit_number": 50, "track_length": 1000, "segments": [
            {"type": "corner", "name": "", "start_m": 0, "end_m": 100, "corner_number": 2},  # numbering skips 1
        ]}
        self._write("bad_circuit.json", bad)
        with self.assertRaises(ValidationError) as ctx:
            TrackSegmentsDatabase(self._tmp.name, cache=False)
        self.assertIn("bad_circuit.json", " ".join(ctx.exception.__notes__))

    def test_missing_sectors_raises_validation_error(self):
        """`sectors` is a mandatory field -- a file missing it should fail fast at
        startup, same reasoning as test_invalid_json_raises_decode_error."""
        missing_sectors = {
            "circuit_name": "Delta Circuit",
            "circuit_number": 4,
            "track_length": 1000,
            "segments": [],
        }
        path = os.path.join(self._tmp.name, "Delta Circuit.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(missing_sectors, fh)
        with self.assertRaises(ValidationError):
            TrackSegmentsDatabase(self._tmp.name, cache=False)

    # --- get_sector() -------------------------------------------------------------------------

    def test_get_sector_sector_1(self):
        """get_sector returns SECTOR1 for a position in the first sector."""
        sector = self.db.get_sector(3, 100)
        self.assertEqual(sector, LapData.Sector.SECTOR1)

    def test_get_sector_sector_2(self):
        """get_sector returns SECTOR2 for a position in the second sector."""
        sector = self.db.get_sector(3, 500)
        self.assertEqual(sector, LapData.Sector.SECTOR2)

    def test_get_sector_sector_3(self):
        """get_sector returns SECTOR3 for a position in the third sector."""
        sector = self.db.get_sector(3, 800)
        self.assertEqual(sector, LapData.Sector.SECTOR3)

    def test_get_sector_beyond_track_length_wraps_to_correct_sector(self):
        """get_sector wraps a position beyond track_length onto the lap."""
        self.assertEqual(self.db.get_sector(3, 9999), LapData.Sector.SECTOR3)  # 9999 % 1000 == 999

    def test_get_sector_unknown_circuit_returns_none(self):
        """get_sector returns None for an unknown circuit number."""
        self.assertIsNone(self.db.get_sector(999, 100))

    def test_get_sector_circuit_a_sector_1(self):
        """sectors is now mandatory -- every loaded circuit has real sector data."""
        self.assertEqual(self.db.get_sector(1, 100), LapData.Sector.SECTOR1)


@allure.story("Shipped files")
class TestShippedTrackSegments(F1TelemetryUnitTestsBase):
    """Checks on the track files shipped in assets/track-segments."""

    ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'track-segments'))

    def _track_files(self) -> list:
        return sorted(name for name in os.listdir(self.ASSETS_DIR) if name.endswith('.json'))

    def test_every_shipped_track_loads(self):
        """Every shipped track file validates and has its own circuit number."""
        db = TrackSegmentsDatabase(self.ASSETS_DIR, cache=False)
        self.assertEqual(len(db), len(self._track_files()))


# -------------------------------------- SCHEMA V2 ---------------------------------------------------------------------

_V2_LENGTH = 5798

# Trimmed from the generated Monza prototype; DRS 2 and the last aero zone cross the start line
_V2_TRACK = {
    "schema_version": 2,
    "circuit_name": "Monza",
    "circuit_number": 11,
    "track_length": _V2_LENGTH,
    "sectors": {"s1": 1898, "s2": 3727},
    "speed_trap_m": 716.3,
    "drs_zones": [
        {"id": 1, "detection_m": 2757.6, "activation": [{"start_m": 3055.8, "end_m": 3889.1}]},
        {"id": 2, "detection_m": 5502.6, "activation": [{"start_m": 9.2, "end_m": 881.3}]},
    ],
    "overtake_zones": [{"id": 1, "detection_m": 5154.4, "activation_m": 5253.6}],
    "active_aero_zones": [
        {"mode": "full", "start_m": 1158.3, "end_m": 2113.1},
        {"mode": "full", "start_m": 5529.7, "end_m": 881.3},
        {"mode": "partial", "start_m": 5595.5, "end_m": 881.3},
    ],
    "segments": [
        {"type": "straight", "name": "Rettifilo Tribune", "start_m": 0, "end_m": 770},
        {
            "type": "complex_corner", "name": "Variante del Rettifilo", "start_m": 770, "end_m": 1015,
            "corner_numbers": [1, 2],
            "corners": [
                {
                    "corner_number": 1, "start_m": 770, "end_m": 952,
                    "brake_boards": [
                        {"distance_m": 150, "at_m": 776.3, "side": "both"},
                        {"distance_m": 50, "at_m": 851.5, "side": "left"},
                    ],
                },
                {"corner_number": 2, "start_m": 952, "end_m": 1015},
            ],
        },
        {
            "type": "corner", "name": "Curva Grande", "start_m": 1060, "end_m": 1860, "corner_number": 3,
            "brake_boards": [{"distance_m": 100, "at_m": 1030.0, "side": "right"}],
        },
        {"type": "straight", "name": "Back", "start_m": 1860, "end_m": _V2_LENGTH},
    ],
}

_V2_KEYS = ("schema_version", "speed_trap_m", "drs_zones", "overtake_zones", "active_aero_zones")


def _v2() -> dict:
    return copy.deepcopy(_V2_TRACK)


def _as_v1(track: dict) -> dict:
    """The same track with every schema v2 field removed."""
    v1 = {k: v for k, v in copy.deepcopy(track).items() if k not in _V2_KEYS}
    for seg in v1["segments"]:
        seg.pop("brake_boards", None)
        seg.pop("corners", None)
    return v1


def _rettifilo(track: dict) -> dict:
    return track["segments"][1]


def _assert_rejected(track: dict, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        load(track, use_cache=False)


# --- v1 compatibility -------------------------------------------------------------------------------------------------

@allure.story("Schema v2: v1 compatibility")
@allure.title("A v1 file loads with every v2 field at its default")
def test_v1_file_gets_v2_defaults():
    """Alpha Circuit, a v1 file with no v2 keys.

    Expected: schema_version 1, no speed trap, no zones, and no brake boards on its corner."""
    ts = load(_CIRCUIT_A, use_cache=False)
    assert ts.schema_version == 1
    assert ts.speed_trap_m is None
    assert ts.drs_zones == ts.overtake_zones == ts.active_aero_zones == ()
    assert ts.segments[1].brake_boards == ()


@allure.story("Schema v2: v1 compatibility")
@allure.title("v2 fields do not change segment or sector lookups")
def test_v2_fields_leave_lookups_unchanged():
    """The v2 Monza track against the same track with its v2 fields stripped, probed every 50 m.

    Expected: identical segment dicts and sectors at every probe."""
    v2 = load(_v2(), use_cache=False)
    v1 = load(_as_v1(_V2_TRACK), use_cache=False)
    for dist in range(0, _V2_LENGTH, 50):
        seg_v1, seg_v2 = v1.get_segment_info(dist), v2.get_segment_info(dist)
        assert (seg_v1 and seg_v1.to_dict()) == (seg_v2 and seg_v2.to_dict()), dist
        assert v1.get_sector(dist) == v2.get_sector(dist), dist


@allure.story("Schema v2: v1 compatibility")
@allure.title("to_dict() of the {seg_type} segment carries no v2 fields")
@pytest.mark.parametrize("seg_type, index", [("corner", 2), ("complex_corner", 1)])
def test_to_dict_unchanged(seg_type, index):
    """A corner with brake boards, and a complex corner with sub-corners, from the v2 Monza track.

    Expected: to_dict() returns exactly the v1 keys, so IPC payloads do not grow."""
    seg = load(_v2(), use_cache=False).segments[index]
    assert seg.type == seg_type
    expected = {"corner": {"type", "name", "corner_number"},
                "complex_corner": {"type", "name", "corner_numbers"}}[seg_type]
    assert set(seg.to_dict()) == expected


@allure.story("Schema v2: v1 compatibility")
@allure.title("schema_version {version} is rejected")
@pytest.mark.parametrize("version", [0, 3])
def test_unknown_schema_version_rejected(version):
    """The v2 Monza track with an unsupported schema_version.

    Expected: rejected, so a newer file cannot load half-understood."""
    track = _v2()
    track["schema_version"] = version
    _assert_rejected(track, "schema_version")


@allure.story("Schema v2: v1 compatibility")
@allure.title("A v2 file loads through TrackSegmentsDatabase")
def test_v2_file_loads_through_database(tmp_path):
    """The v2 Monza track written to a JSON file in an otherwise empty directory.

    Expected: the database loads it, keeping its zones and sub-corners."""
    (tmp_path / "Monza.json").write_text(json.dumps(_V2_TRACK), encoding="utf-8")
    ts = TrackSegmentsDatabase(tmp_path, cache=False)[11]
    assert ts.schema_version == 2
    assert len(ts.drs_zones) == 2
    assert len(ts.segments[1].corners) == 2


# --- Brake boards -----------------------------------------------------------------------------------------------------

@allure.story("Schema v2: brake boards")
@allure.title("A {distance_m} m board on the {side} is valid")
@pytest.mark.parametrize("side", ["left", "right", "both"])
@pytest.mark.parametrize("distance_m", [50, 100, 150, 200, 250, 300])
def test_brake_board_valid(distance_m, side):
    """Every label from 50 to 300 m, on each side.

    Expected: the board parses with its values intact."""
    board = BrakeBoardInfo(distance_m=distance_m, at_m=1000.5, side=side)
    assert (board.distance_m, board.at_m, board.side) == (distance_m, 1000.5, side)


@allure.story("Schema v2: brake boards")
@allure.title("A board labelled {distance_m} m is rejected")
@pytest.mark.parametrize("distance_m", [0, 75, 350])
def test_brake_board_bad_distance_rejected(distance_m):
    """Labels off the 50 m grid or past 300 m.

    Expected: rejected."""
    with pytest.raises(ValidationError, match="distance_m"):
        BrakeBoardInfo(distance_m=distance_m, at_m=100, side="left")


@allure.story("Schema v2: brake boards")
@allure.title("A board on side {side!r} is rejected")
@pytest.mark.parametrize("side", ["Left", "centre", ""])
def test_brake_board_bad_side_rejected(side):
    """Spelling variants and unknown sides.

    Expected: rejected, since side is a fixed enum."""
    with pytest.raises(ValidationError, match="side"):
        BrakeBoardInfo(distance_m=100, at_m=100, side=side)


@allure.story("Schema v2: brake boards")
@allure.title("A board in the segment before its corner is valid")
def test_brake_board_before_its_corner_valid():
    """Curva Grande starts at 1060 m; its 100 m board is at 1030 m, in the gap before it.

    Expected: loads, because boards normally sit before the corner they warn about."""
    seg = load(_v2(), use_cache=False).segments[2]
    assert seg.brake_boards[0].at_m < seg.start_m


# --- Sub-corners ------------------------------------------------------------------------------------------------------

@allure.story("Schema v2: sub-corners")
@allure.title("Sub-corners parse, with names defaulting to empty")
def test_sub_corners_parse():
    """Variante del Rettifilo, split into corners 1 and 2 at 952 m.

    Expected: two sub-corners with their ranges, unnamed, boards only on corner 1."""
    corners = load(_v2(), use_cache=False).segments[1].corners
    assert [(c.corner_number, c.start_m, c.end_m) for c in corners] == [(1, 770, 952), (2, 952, 1015)]
    assert [c.name for c in corners] == ["", ""]
    assert len(corners[0].brake_boards) == 2
    assert corners[1].brake_boards == ()


@allure.story("Schema v2: sub-corners")
@allure.title("A complex corner without sub-corners is valid")
def test_complex_corner_without_sub_corners_valid():
    """Variante del Rettifilo with its corners key removed.

    Expected: loads with an empty corners tuple, as every v1 file does."""
    track = _v2()
    del _rettifilo(track)["corners"]
    assert load(track, use_cache=False).segments[1].corners == ()


def _sub_corner_case(track: dict, case: str) -> None:
    corners = _rettifilo(track)["corners"]
    if case == "renumbered":
        corners[1]["corner_number"] = 3
    elif case == "missing-one":
        corners[0]["end_m"] = 1015
        del corners[1]
    elif case == "late-start":
        corners[0]["start_m"] = 780
    elif case == "early-end":
        corners[1]["end_m"] = 1010
    elif case == "gap":
        corners[1]["start_m"] = 960
    elif case == "overlap":
        corners[1]["start_m"] = 940
    elif case == "empty-range":
        corners[1]["start_m"] = corners[1]["end_m"] = corners[0]["end_m"] = 1015
    else:
        raise AssertionError(case)


@allure.story("Schema v2: sub-corners")
@allure.title("Sub-corners that are {case} are rejected")
@pytest.mark.parametrize("case, message", [
    ("renumbered", "must match corner_numbers"),
    ("missing-one", "must match corner_numbers"),
    ("late-start", "not at the segment start"),
    ("early-end", "not at the segment end"),
    ("gap", "not where corner 1 ends"),
    ("overlap", "not where corner 1 ends"),
    ("empty-range", "must be less than end_m"),
])
def test_sub_corners_bad_coverage_rejected(case, message):
    """Variante del Rettifilo's sub-corners, broken one way per case.

    Expected: rejected with a message naming the rule broken."""
    track = _v2()
    _sub_corner_case(track, case)
    _assert_rejected(track, message)


# --- Zones ------------------------------------------------------------------------------------------------------------

@allure.story("Schema v2: zones")
@allure.title("Zones that cross the start line are valid")
def test_wrapped_zones_valid():
    """DRS 2 activates 9.2 to 881.3 m after detection at 5502.6 m; an aero zone runs 5529.7 to 881.3 m.

    Expected: both load as given, with end_m below start_m on the aero zone."""
    ts = load(_v2(), use_cache=False)
    assert ts.drs_zones[1].detection_m > ts.drs_zones[1].activation[0].end_m
    aero = ts.active_aero_zones[1]
    assert (aero.mode, aero.start_m, aero.end_m) == ("full", 5529.7, 881.3)


@allure.story("Schema v2: zones")
@allure.title("A DRS zone with two activations is valid")
def test_drs_zone_with_two_activations_valid():
    """One detection point opening two activation ranges, as at Melbourne.

    Expected: both activations are kept, in order."""
    track = _v2()
    track["drs_zones"][0]["activation"].append({"start_m": 4000, "end_m": 4500})
    activations = load(track, use_cache=False).drs_zones[0].activation
    assert [(a.start_m, a.end_m) for a in activations] == [(3055.8, 3889.1), (4000, 4500)]


@allure.story("Schema v2: zones")
@allure.title("A DRS zone with no activation is rejected")
def test_drs_zone_without_activation_rejected():
    """DRS 1 with an empty activation list.

    Expected: rejected."""
    track = _v2()
    track["drs_zones"][0]["activation"] = []
    _assert_rejected(track, "activation")


@allure.story("Schema v2: zones")
@allure.title("An empty {kind} zone is rejected")
@pytest.mark.parametrize("kind", ["drs", "active_aero"])
def test_empty_zone_rejected(kind):
    """A zone whose start_m equals its end_m.

    Expected: rejected, since it is neither a range nor a wrap."""
    track = _v2()
    zone = track["drs_zones"][0]["activation"][0] if kind == "drs" else track["active_aero_zones"][0]
    zone["end_m"] = zone["start_m"]
    _assert_rejected(track, "zone is empty")


@allure.story("Schema v2: zones")
@allure.title("Active aero mode {mode!r} is rejected")
@pytest.mark.parametrize("mode", ["Full", "none", ""])
def test_active_aero_bad_mode_rejected(mode):
    """Spelling variants and unknown modes.

    Expected: rejected, since mode is a fixed enum."""
    track = _v2()
    track["active_aero_zones"][0]["mode"] = mode
    _assert_rejected(track, "mode")


@allure.story("Schema v2: zones")
@allure.title("Duplicate {kind} ids are rejected")
@pytest.mark.parametrize("kind", ["drs_zones", "overtake_zones"])
def test_duplicate_zone_ids_rejected(kind):
    """Two zones of one kind sharing id 1.

    Expected: rejected, naming the kind and the id."""
    track = _v2()
    track[kind].append(copy.deepcopy(track[kind][0]))
    track[kind][-1]["id"] = 1
    _assert_rejected(track, f"{kind}: duplicate id 1")


# --- Lap positions ----------------------------------------------------------------------------------------------------

def _set_position(track: dict, field: str, value: float) -> None:
    if field == "speed_trap_m":
        track["speed_trap_m"] = value
    elif field == "drs detection_m":
        track["drs_zones"][0]["detection_m"] = value
    elif field == "drs activation end_m":
        track["drs_zones"][0]["activation"][0]["end_m"] = value
    elif field == "overtake activation_m":
        track["overtake_zones"][0]["activation_m"] = value
    elif field == "active aero start_m":
        track["active_aero_zones"][0]["start_m"] = value
    elif field == "corner board at_m":
        track["segments"][2]["brake_boards"][0]["at_m"] = value
    elif field == "sub-corner board at_m":
        _rettifilo(track)["corners"][0]["brake_boards"][0]["at_m"] = value
    else:
        raise AssertionError(field)


_POSITION_FIELDS = ["speed_trap_m", "drs detection_m", "drs activation end_m", "overtake activation_m",
                    "active aero start_m", "corner board at_m", "sub-corner board at_m"]


@allure.story("Schema v2: lap positions")
@allure.title("{field} at {value} m is rejected")
@pytest.mark.parametrize("value", [-0.1, _V2_LENGTH, 9000])
@pytest.mark.parametrize("field", _POSITION_FIELDS)
def test_lap_position_out_of_range_rejected(field, value):
    """Each kind of v2 lap distance set below 0, at track_length, and past it.

    Expected: rejected, with the value and track_length in the message."""
    track = _v2()
    _set_position(track, field, value)
    _assert_rejected(track, rf"\({float(value)}\) must be in \[0, track_length={float(_V2_LENGTH)}\)")


@allure.story("Schema v2: lap positions")
@allure.title("{field} at 0 m is valid")
@pytest.mark.parametrize("field", ["speed_trap_m", "drs detection_m", "active aero start_m", "corner board at_m"])
def test_lap_position_at_zero_valid(field):
    """Lap distances on the start line itself.

    Expected: loads, since the range is [0, track_length)."""
    track = _v2()
    _set_position(track, field, 0)
    load(track, use_cache=False)

