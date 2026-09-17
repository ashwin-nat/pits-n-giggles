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

import pytest

from lib.last_corner_stats import LastCornerStats, LastCornerTracker, TelemetrySample
from lib.track_segments_classifier import TrackSegmentsDatabase
from lib.track_segments_classifier.types import (ComplexCornerSegmentInfo,
                                                  CornerSegmentInfo)

# ----------------------------------------------------------------------------------------------------------------------

CIRCUIT_NUM = 12

TRACK_DATA = {
    "circuit_name": "Circuit de Spa-Francorchamps",
    "circuit_number": CIRCUIT_NUM,
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
            "type": "straight",
            "name": "Kemmel Straight",
            "start_m": 200,
            "end_m": 1200,
        },
        {
            "type": "corner",
            "name": "Eau Rouge",
            "start_m": 1200,
            "end_m": 1400,
            "corner_number": 2,
        },
        {
            "type": "straight",
            "name": "Back Straight",
            "start_m": 1400,
            "end_m": 2000,
        },
        {
            "type": "complex_corner",
            "name": "Pouhon",
            "start_m": 2000,
            "end_m": 2400,
            "corner_numbers": [6, 7],
        },
        {
            "type": "straight",
            "name": "Finish Straight",
            "start_m": 2400,
            "end_m": 3000,
        },
    ],
}


@pytest.fixture
def seg_db() -> TrackSegmentsDatabase:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "spa.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(TRACK_DATA, fh)
        yield TrackSegmentsDatabase(tmp_dir)


@pytest.fixture
def tracker(seg_db: TrackSegmentsDatabase) -> LastCornerTracker:
    return LastCornerTracker(seg_db)


def _update(tracker: LastCornerTracker, circuit_pos_m: float, speed_kmph: int, circuit_num: int = CIRCUIT_NUM) -> None:
    tracker.update(TelemetrySample(circuit_num=circuit_num, circuit_pos_m=circuit_pos_m, speed_kmph=speed_kmph))

# ----------------------------------------------------------------------------------------------------------------------

def test_stats_none_before_any_updates(tracker: LastCornerTracker):
    assert tracker.stats() is None


def test_straight_only_samples_never_produce_stats(tracker: LastCornerTracker):
    for pos in (250, 500, 800, 1100):
        _update(tracker, pos, speed_kmph=300)
    assert tracker.stats() is None


def test_corner_completion_publishes_min_speed(tracker: LastCornerTracker):
    # Enter and traverse La Source (0-200m)
    for pos, speed in [(10, 200), (50, 120), (100, 90), (150, 130), (190, 250)]:
        _update(tracker, pos, speed_kmph=speed)
    assert tracker.stats() is None  # still inside corner

    # Leave onto Kemmel Straight
    _update(tracker, 250, speed_kmph=300)

    stats = tracker.stats()
    assert stats is not None
    assert isinstance(stats, LastCornerStats)
    assert isinstance(stats.segment, CornerSegmentInfo)
    assert stats.segment.name == "La Source"
    assert stats.segment.corner_number == 1
    assert stats.min_speed_kmph == 90


def test_stats_none_while_still_inside_corner(tracker: LastCornerTracker):
    _update(tracker, 10, speed_kmph=200)
    _update(tracker, 50, speed_kmph=100)
    assert tracker.stats() is None


def test_stats_available_on_straight_after_corner(tracker: LastCornerTracker):
    _update(tracker, 10, speed_kmph=200)
    _update(tracker, 100, speed_kmph=90)
    _update(tracker, 250, speed_kmph=300)  # leave onto straight
    _update(tracker, 500, speed_kmph=310)  # still on straight
    stats = tracker.stats()
    assert stats is not None
    assert stats.min_speed_kmph == 90


def test_entering_next_corner_clears_previous_stats_immediately(tracker: LastCornerTracker):
    # Complete La Source
    _update(tracker, 10, speed_kmph=200)
    _update(tracker, 100, speed_kmph=90)
    _update(tracker, 250, speed_kmph=300)
    assert tracker.stats() is not None

    # Enter Eau Rouge (next corner) -> published stats clear immediately
    _update(tracker, 1250, speed_kmph=280)
    assert tracker.stats() is None


def test_complex_corner_tracked_like_a_corner(tracker: LastCornerTracker):
    for pos, speed in [(2050, 200), (2200, 150), (2350, 220)]:
        _update(tracker, pos, speed_kmph=speed)
    assert tracker.stats() is None  # still inside complex corner

    _update(tracker, 2450, speed_kmph=300)  # onto finish straight

    stats = tracker.stats()
    assert stats is not None
    assert isinstance(stats.segment, ComplexCornerSegmentInfo)
    assert stats.segment.name == "Pouhon"
    assert stats.segment.corner_numbers == (6, 7)
    assert stats.min_speed_kmph == 150


def test_reset_clears_accumulating_and_published_state(tracker: LastCornerTracker):
    _update(tracker, 10, speed_kmph=200)
    _update(tracker, 100, speed_kmph=90)
    _update(tracker, 250, speed_kmph=300)
    assert tracker.stats() is not None

    tracker.reset()
    assert tracker.stats() is None

    # Resuming mid-corner after reset should still accumulate correctly.
    _update(tracker, 1250, speed_kmph=280)
    _update(tracker, 1300, speed_kmph=200)
    _update(tracker, 1450, speed_kmph=320)
    stats = tracker.stats()
    assert stats is not None
    assert stats.segment.name == "Eau Rouge"
    assert stats.min_speed_kmph == 200


def test_repeated_visits_to_same_corner_are_isolated(tracker: LastCornerTracker):
    # First lap through La Source
    _update(tracker, 10, speed_kmph=200)
    _update(tracker, 100, speed_kmph=90)
    _update(tracker, 250, speed_kmph=300)
    first_stats = tracker.stats()
    assert first_stats.min_speed_kmph == 90

    # Traverse the rest of the lap back to the start (simulating a new lap)
    _update(tracker, 1250, speed_kmph=280)  # Eau Rouge
    _update(tracker, 1450, speed_kmph=300)  # Back Straight, publishes Eau Rouge
    assert tracker.stats().segment.name == "Eau Rouge"

    # Second visit to La Source, different min speed this time
    _update(tracker, 10, speed_kmph=210)
    _update(tracker, 100, speed_kmph=130)
    _update(tracker, 250, speed_kmph=300)
    second_stats = tracker.stats()
    assert second_stats.segment.name == "La Source"
    assert second_stats.min_speed_kmph == 130


def test_circuit_num_is_bound_on_first_update(tracker: LastCornerTracker):
    """circuit_num is inferred from the first sample and does not need to be passed again explicitly."""
    _update(tracker, 10, speed_kmph=200, circuit_num=CIRCUIT_NUM)
    _update(tracker, 100, speed_kmph=90, circuit_num=CIRCUIT_NUM)
    _update(tracker, 250, speed_kmph=300, circuit_num=CIRCUIT_NUM)
    assert tracker.stats().min_speed_kmph == 90


def test_circuit_num_change_raises_assertion_error(tracker: LastCornerTracker):
    """A circuit_num change mid-lifetime is a caller bug (should get a new tracker instead)."""
    _update(tracker, 10, speed_kmph=200, circuit_num=CIRCUIT_NUM)
    with pytest.raises(AssertionError):
        _update(tracker, 100, speed_kmph=90, circuit_num=CIRCUIT_NUM + 1)


def test_reset_does_not_clear_bound_circuit_num(tracker: LastCornerTracker):
    """reset() clears corner-tracking state but not the circuit_num a tracker is bound to."""
    _update(tracker, 10, speed_kmph=200, circuit_num=CIRCUIT_NUM)
    tracker.reset()
    with pytest.raises(AssertionError):
        _update(tracker, 100, speed_kmph=90, circuit_num=CIRCUIT_NUM + 1)


def test_stats_to_dict_uses_segment_to_dict_and_includes_segment_id(tracker: LastCornerTracker):
    """to_dict() must reuse the segment's own to_dict() (not leak all pydantic fields) but still expose segment_id."""
    _update(tracker, 10, speed_kmph=200)
    _update(tracker, 100, speed_kmph=90)
    _update(tracker, 250, speed_kmph=300)

    stats = tracker.stats()
    result = stats.to_dict()

    assert result["min_speed_kmph"] == 90
    assert result["segment"]["type"] == "corner"
    assert result["segment"]["name"] == "La Source"
    assert result["segment"]["corner_number"] == 1
    assert result["segment"]["segment_id"] == stats.segment.segment_id
    # start_m/end_m are internal to the classifier, not part of the curated wire format.
    assert "start_m" not in result["segment"]
    assert "end_m" not in result["segment"]
