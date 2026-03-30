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

import json
import os
import sys
import tempfile

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic import ValidationError

from lib.f1_types.packet_2_lap_data import LapData
from lib.track_segment_info import TrackSegments, TrackSegmentsDatabase
from lib.track_segment_info.types import (BaseSegmentInfo,
                                           ComplexCornerSegmentInfo,
                                           CornerSegmentInfo,
                                           StraightSegmentInfo)

from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestTrackSegments(F1TelemetryUnitTestsBase):

    @staticmethod
    def _track(segments: list) -> dict:
        """Wrap segments in a minimal valid top-level track dict."""
        return {"circuit_name": "Test Circuit", "circuit_number": 99, "track_length": 7000, "segments": segments}

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
                    "corner_number": 5,
                },
                {
                    "type": "complex_corner",
                    "name": "Pouhon",
                    "start_m": 1400,
                    "end_m": 1800,
                    "corner_numbers": [6, 7],
                },
            ]
        }

        self.tracker = TrackSegments()
        self.tracker.load_track_data(self.track_data)

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
        self.assertEqual(info.corner_number, 5)
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
        self.assertEqual(info.corner_numbers[0], 6)
        self.assertEqual(info.corner_numbers[1], 7)

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
        self.assertEqual(info.corner_number, 5)

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

    def test_no_track_loaded(self):
        """Calling lookup without loading data returns None."""
        tracker = TrackSegments()
        info = tracker.get_segment_info(100)
        self.assertIsNone(info)

    # --- Validation: missing required base fields -----------------------------------------

    def test_validation_missing_type(self):
        """Missing 'type' field raises ValueError."""
        bad = {"name": "X", "start_m": 0, "end_m": 100}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track([bad]))

    def test_validation_missing_name(self):
        """Missing 'name' field raises ValueError."""
        bad = {"type": "straight", "start_m": 0, "end_m": 100}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track([bad]))

    def test_validation_missing_start_m(self):
        """Missing 'start_m' field raises ValueError."""
        bad = {"type": "straight", "name": "X", "end_m": 100}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track([bad]))

    def test_validation_missing_end_m(self):
        """Missing 'end_m' field raises ValueError."""
        bad = {"type": "straight", "name": "X", "start_m": 0}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track([bad]))

    def test_validation_corner_missing_corner_number(self):
        """Corner segment without 'corner_number' raises ValueError."""
        bad = {"type": "corner", "name": "X", "start_m": 0, "end_m": 100}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track([bad]))

    def test_validation_complex_corner_missing_corners(self):
        """Complex corner without 'corner_numbers' raises ValueError."""
        bad = {"type": "complex_corner", "name": "X", "start_m": 0, "end_m": 100}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track([bad]))

    def test_validation_unknown_type(self):
        """Unknown segment type raises ValidationError."""
        bad = {"type": "chicane", "name": "X", "start_m": 0, "end_m": 100}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track([bad]))

    def test_validation_start_m_equal_to_end_m(self):
        """start_m == end_m raises ValidationError."""
        bad = {"type": "straight", "name": "X", "start_m": 100, "end_m": 100}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track([bad]))

    def test_validation_start_m_greater_than_end_m(self):
        """start_m > end_m raises ValidationError."""
        bad = {"type": "straight", "name": "X", "start_m": 200, "end_m": 100}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track([bad]))

    # --- Ordering and overlap validation --------------------------------------------------

    def test_validation_segments_out_of_order(self):
        """Segments with decreasing start_m raise ValidationError."""
        segments = [
            {"type": "straight", "name": "B", "start_m": 500, "end_m": 1000},
            {"type": "straight", "name": "A", "start_m": 0,   "end_m": 500},
        ]
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track(segments))

    def test_validation_segments_overlapping(self):
        """Segment whose start_m falls inside the previous segment raises ValidationError."""
        segments = [
            {"type": "straight", "name": "A", "start_m": 0,   "end_m": 600},
            {"type": "straight", "name": "B", "start_m": 400, "end_m": 1000},
        ]
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track(segments))

    def test_validation_adjacent_segments_exact_boundary(self):
        """Segments where start_m of next == end_m of previous are valid (no gap, no overlap)."""
        segments = [
            {"type": "straight", "name": "A", "start_m": 0,   "end_m": 500},
            {"type": "straight", "name": "B", "start_m": 500, "end_m": 1000},
        ]
        tracker = TrackSegments()
        tracker.load_track_data(self._track(segments))  # must not raise

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
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(data)

    def test_top_level_missing_circuit_number(self):
        """Missing circuit_number raises ValidationError."""
        data = {"circuit_name": "X", "track_length": 1000, "segments": []}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(data)

    def test_top_level_missing_track_length(self):
        """Missing track_length raises ValidationError."""
        data = {"circuit_name": "X", "circuit_number": 1, "segments": []}
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(data)

    def test_properties_return_none_before_load(self):
        """Top-level properties return None before load_track_data is called."""
        tracker = TrackSegments()
        self.assertIsNone(tracker.circuit_name)
        self.assertIsNone(tracker.circuit_number)

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


# ----------------------------------------------------------------------------------------------------------------------

class TestSegmentRender(F1TelemetryUnitTestsBase):

    def test_straight_named_render(self):
        """Named straight renders with type=straight and name set."""
        seg = StraightSegmentInfo(name="Kemmel Straight", start_m=400, end_m=1200)
        self.assertEqual(seg.render(), {"type": "straight", "name": "Kemmel Straight", "turns": ""})

    def test_straight_empty_name_raises(self):
        """Empty name on a straight raises ValidationError."""
        with self.assertRaises(ValidationError):
            StraightSegmentInfo(name="", start_m=0, end_m=100)

    def test_straight_missing_name_raises(self):
        """Missing name on a straight raises ValidationError."""
        with self.assertRaises(ValidationError):
            StraightSegmentInfo(start_m=0, end_m=100)

    def test_corner_named_render(self):
        """Named corner renders with type=corner, name, and turn number."""
        seg = CornerSegmentInfo(name="La Source", start_m=0, end_m=200, corner_number=1)
        self.assertEqual(seg.render(), {"type": "corner", "name": "La Source", "turns": "T1"})

    def test_corner_unnamed_render(self):
        """Unnamed corner renders with empty name and full 'Turn N' label."""
        seg = CornerSegmentInfo(name="", start_m=0, end_m=200, corner_number=3)
        self.assertEqual(seg.render(), {"type": "corner", "name": "", "turns": "Turn 3"})

    def test_complex_corner_named_render(self):
        """Named complex corner renders with type=corner, name, and spaced turn numbers."""
        seg = ComplexCornerSegmentInfo(name="Pouhon", start_m=1400, end_m=1800, corner_numbers=(6, 7))
        self.assertEqual(seg.render(), {"type": "corner", "name": "Pouhon", "turns": "T6 / T7"})

    def test_complex_corner_unnamed_render(self):
        """Unnamed complex corner with >2 turns renders with 'Turns' range format."""
        seg = ComplexCornerSegmentInfo(name="", start_m=0, end_m=500, corner_numbers=(1, 2, 3))
        self.assertEqual(seg.render(), {"type": "corner", "name": "", "turns": "Turns 1-3"})

    def test_complex_corner_unnamed_two_turns_render(self):
        """Unnamed complex corner with 2 turns renders with 'Turn' slash format."""
        seg = ComplexCornerSegmentInfo(name="", start_m=0, end_m=500, corner_numbers=(3, 4))
        self.assertEqual(seg.render(), {"type": "corner", "name": "", "turns": "Turn 3 / Turn 4"})

    def test_complex_corner_two_turns_render(self):
        """Complex corner with exactly 2 turns renders with slash format."""
        seg = ComplexCornerSegmentInfo(name="Esses", start_m=0, end_m=500, corner_numbers=(3, 4))
        self.assertEqual(seg.render(), {"type": "corner", "name": "Esses", "turns": "T3 / T4"})

    def test_complex_corner_many_turns_render(self):
        """Complex corner with >2 turns renders with range format."""
        seg = ComplexCornerSegmentInfo(name="Maggotts-Becketts", start_m=0, end_m=800, corner_numbers=(5, 6, 7, 8))
        self.assertEqual(seg.render(), {"type": "corner", "name": "Maggotts-Becketts", "turns": "T5-T8"})

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

class TestGetSector(F1TelemetryUnitTestsBase):

    _S1 = 500
    _S2 = 1500
    _TRACK_LENGTH = 3000

    @staticmethod
    def _track_with_sectors(sectors=None, track_length=3000):
        data = {
            "circuit_name": "Sector Test Circuit",
            "circuit_number": 1,
            "track_length": track_length,
            "segments": [],
        }
        if sectors is not None:
            data["sectors"] = sectors
        return data

    def setUp(self):
        self.tracker = TrackSegments()
        self.tracker.load_track_data(
            self._track_with_sectors({"s1": self._S1, "s2": self._S2}, self._TRACK_LENGTH)
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

    def test_at_track_length_returns_none(self):
        """Position exactly at track_length returns None."""
        self.assertIsNone(self.tracker.get_sector(3000))

    def test_beyond_track_length_returns_none(self):
        """Position beyond track_length returns None."""
        self.assertIsNone(self.tracker.get_sector(5000))

    def test_negative_position_returns_none(self):
        """Negative position returns None."""
        self.assertIsNone(self.tracker.get_sector(-1))

    # --- No data --------------------------------------------------------------------------

    def test_no_sectors_key_returns_none(self):
        """get_sector returns None when sectors key is absent from track data."""
        tracker = TrackSegments()
        tracker.load_track_data(self._track_with_sectors(sectors=None))
        self.assertIsNone(tracker.get_sector(100))

    def test_no_track_loaded_returns_none(self):
        """get_sector returns None when no track data has been loaded."""
        tracker = TrackSegments()
        self.assertIsNone(tracker.get_sector(100))

    # --- Validation -----------------------------------------------------------------------

    def test_sectors_s1_equal_s2_raises(self):
        """s1 == s2 raises ValidationError."""
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track_with_sectors({"s1": 500, "s2": 500}))

    def test_sectors_s1_greater_than_s2_raises(self):
        """s1 > s2 raises ValidationError."""
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track_with_sectors({"s1": 1500, "s2": 500}))

    def test_sectors_missing_s1_raises(self):
        """sectors without s1 raises ValidationError."""
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track_with_sectors({"s2": 1500}))

    def test_sectors_missing_s2_raises(self):
        """sectors without s2 raises ValidationError."""
        tracker = TrackSegments()
        with self.assertRaises(ValidationError):
            tracker.load_track_data(self._track_with_sectors({"s1": 500}))


# ----------------------------------------------------------------------------------------------------------------------

_CIRCUIT_A = {
    "circuit_name": "Alpha Circuit",
    "circuit_number": 1,
    "track_length": 1000,
    "segments": [
        {"type": "straight", "name": "Main Straight", "start_m": 0,   "end_m": 500},
        {"type": "corner",   "name": "Turn One",      "start_m": 500, "end_m": 700, "corner_number": 1},
    ],
}

_CIRCUIT_B = {
    "circuit_name": "Beta Circuit",
    "circuit_number": 2,
    "track_length": 400,
    "segments": [
        {"type": "corner", "name": "Hairpin", "start_m": 0, "end_m": 300, "corner_number": 1},
    ],
}


class TestTrackSegmentsDatabase(F1TelemetryUnitTestsBase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        for circuit in (_CIRCUIT_A, _CIRCUIT_B):
            path = os.path.join(self._tmp.name, f"{circuit['circuit_name']}.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(circuit, fh)
        self.db = TrackSegmentsDatabase(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # --- Presence and counts ------------------------------------------------------------------

    def test_len_equals_number_of_files(self):
        """Database length equals the number of JSON files loaded."""
        self.assertEqual(len(self.db), 2)

    def test_contains_known_circuit(self):
        """Known circuit name is found via 'in'."""
        self.assertIn("Alpha Circuit", self.db)

    def test_not_contains_unknown_circuit(self):
        """Unknown circuit name is not found via 'in'."""
        self.assertNotIn("Unknown Circuit", self.db)

    def test_iter_yields_all_circuit_names(self):
        """Iterating the database yields all circuit names."""
        self.assertEqual(set(self.db), {"Alpha Circuit", "Beta Circuit"})

    # --- get() --------------------------------------------------------------------------------

    def test_get_returns_track_segments_instance(self):
        """get() returns a TrackSegments instance for a known circuit."""
        ts = self.db.get("Alpha Circuit")
        self.assertIsInstance(ts, TrackSegments)

    def test_get_unknown_returns_none(self):
        """get() returns None for an unknown circuit."""
        self.assertIsNone(self.db.get("No Such Circuit"))

    # --- __getitem__ --------------------------------------------------------------------------

    def test_getitem_known_circuit(self):
        """__getitem__ returns the TrackSegments for a known circuit."""
        ts = self.db["Beta Circuit"]
        self.assertIsInstance(ts, TrackSegments)
        self.assertEqual(ts.circuit_name, "Beta Circuit")

    def test_getitem_unknown_raises_key_error(self):
        """__getitem__ raises KeyError for an unknown circuit."""
        with self.assertRaises(KeyError):
            _ = self.db["No Such Circuit"]

    # --- get_segment_info() -------------------------------------------------------------------

    def test_get_segment_info_returns_correct_segment(self):
        """get_segment_info returns the right segment for a known circuit and position."""
        seg = self.db.get_segment_info("Alpha Circuit", 250)
        self.assertIsInstance(seg, StraightSegmentInfo)
        self.assertEqual(seg.name, "Main Straight")

    def test_get_segment_info_corner(self):
        """get_segment_info returns a corner segment at the right position."""
        seg = self.db.get_segment_info("Alpha Circuit", 600)
        self.assertIsInstance(seg, CornerSegmentInfo)
        self.assertEqual(seg.corner_number, 1)

    def test_get_segment_info_outside_range_returns_none(self):
        """get_segment_info returns None for a position outside all segments."""
        seg = self.db.get_segment_info("Alpha Circuit", 9999)
        self.assertIsNone(seg)

    def test_get_segment_info_unknown_circuit_returns_none(self):
        """get_segment_info returns None for an unknown circuit."""
        seg = self.db.get_segment_info("Unknown Circuit", 100)
        self.assertIsNone(seg)

    # --- Empty directory ----------------------------------------------------------------------

    def test_empty_directory_has_zero_circuits(self):
        """Database built from an empty directory has length 0."""
        with tempfile.TemporaryDirectory() as empty:
            db = TrackSegmentsDatabase(empty)
            self.assertEqual(len(db), 0)

    # --- Error handling -----------------------------------------------------------------------

    def test_invalid_directory_raises_file_not_found(self):
        """Non-existent directory should fail fast."""
        missing = os.path.join(self._tmp.name, "does_not_exist")
        with self.assertRaises(FileNotFoundError):
            TrackSegmentsDatabase(missing)

    def test_invalid_json_raises_decode_error(self):
        """Malformed JSON should bubble up as a decode error."""
        bad_json = os.path.join(self._tmp.name, "bad.json")
        with open(bad_json, "w", encoding="utf-8") as fh:
            fh.write("{ not-valid-json }")
        with self.assertRaises(json.JSONDecodeError):
            TrackSegmentsDatabase(self._tmp.name)
