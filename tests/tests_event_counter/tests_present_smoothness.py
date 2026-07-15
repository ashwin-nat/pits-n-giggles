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

import pytest

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from lib.event_counter import EventCounter
from lib.event_counter.present_smoothness import (_BOUNDARY_FACTOR,
                                                  _HITCH_FACTOR,
                                                  _MIN_BOUNDARY_NS,
                                                  _WINDOW_SIZE,
                                                  PresentSmoothnessStat)

# ----------------------------------------------------------------------------------------------------------------------

MS = 1_000_000  # ns per ms
PERIOD_60HZ = 16_666_667
START_TS = 1_000 * MS  # arbitrary nonzero origin (0 is the "no baseline" sentinel)


def feed_intervals(stat: PresentSmoothnessStat, intervals_ns, period_ns, start_ts=START_TS):
    """Observe a burst starting at start_ts followed by one present per interval."""
    ts = start_ts
    stat.observe_present(ts, period_ns)
    for interval in intervals_ns:
        ts += interval
        stat.observe_present(ts, period_ns)
    return ts


# --------------------------------------------------
# Baseline / burst-start behaviour
# --------------------------------------------------

def test_first_present_sets_baseline_only():
    stat = PresentSmoothnessStat()

    stat.observe_present(START_TS, PERIOD_60HZ)

    assert stat.presents == 1
    assert stat.count == 0
    assert stat.boundaries == 0
    assert stat.hitches == 0

    d = stat.to_dict()
    assert d["interval_ns"]["min"] == 0
    assert d["interval_ns"]["max"] == 0
    assert d["interval_ns"]["p50"] == 0


def test_steady_cadence_records_intervals_without_hitches():
    stat = PresentSmoothnessStat()
    period = 10 * MS

    feed_intervals(stat, [period] * 4, period)

    assert stat.presents == 5
    assert stat.count == 4
    assert stat.hitches == 0
    assert stat.boundaries == 0
    assert stat.active_time_ns == 4 * period
    assert stat.min == period
    assert stat.max == period
    assert stat.mean == pytest.approx(period)


# --------------------------------------------------
# Hitch detection
# --------------------------------------------------

def test_hitch_detected_above_threshold():
    stat = PresentSmoothnessStat()
    period = 10 * MS

    hitch_interval = int(period * _HITCH_FACTOR) + 1
    feed_intervals(stat, [period, hitch_interval, period], period)

    assert stat.hitches == 1
    assert stat.count == 3  # the hitch is still an active interval


def test_interval_exactly_at_threshold_is_not_a_hitch():
    stat = PresentSmoothnessStat()
    period = 10 * MS

    feed_intervals(stat, [int(period * _HITCH_FACTOR)], period)

    assert stat.hitches == 0
    assert stat.count == 1


# --------------------------------------------------
# Idle boundaries
# --------------------------------------------------

def test_idle_gap_is_a_boundary_not_an_interval():
    stat = PresentSmoothnessStat()
    period = 10 * MS  # boundary floor (100 ms) dominates 3x period here
    assert max(_BOUNDARY_FACTOR * period, _MIN_BOUNDARY_NS) == _MIN_BOUNDARY_NS

    end_ts = feed_intervals(stat, [period], period)
    stat.observe_present(end_ts + _MIN_BOUNDARY_NS + 1, period)  # idle gap

    assert stat.boundaries == 1
    assert stat.count == 1            # only the pre-gap interval
    assert stat.active_time_ns == period

    # Next present measures from the fresh post-gap baseline
    stat.observe_present(end_ts + _MIN_BOUNDARY_NS + 1 + period, period)
    assert stat.count == 2
    assert stat.active_time_ns == 2 * period
    assert stat.max == period         # the gap itself never entered the stats


def test_boundary_scales_with_slow_displays():
    stat = PresentSmoothnessStat()
    period = 50 * MS  # 3x period (150 ms) dominates the 100 ms floor
    boundary = _BOUNDARY_FACTOR * period
    assert boundary > _MIN_BOUNDARY_NS

    feed_intervals(stat, [boundary - MS], period)   # just inside: active (and a hitch)
    assert stat.boundaries == 0
    assert stat.count == 1
    assert stat.hitches == 1  # 149 ms > 2 x 50 ms

    stat2 = PresentSmoothnessStat()
    feed_intervals(stat2, [boundary + MS], period)  # just beyond: idle boundary
    assert stat2.boundaries == 1
    assert stat2.count == 0


# --------------------------------------------------
# Bad samples
# --------------------------------------------------

def test_non_positive_interval_counted_as_bad_sample():
    stat = PresentSmoothnessStat()

    stat.observe_present(START_TS, PERIOD_60HZ)
    stat.observe_present(START_TS, PERIOD_60HZ)          # zero interval
    stat.observe_present(START_TS - MS, PERIOD_60HZ)     # negative interval

    assert stat.bad_samples == 2
    assert stat.count == 0
    assert stat.presents == 3


def test_invalid_period_counted_as_bad_sample():
    stat = PresentSmoothnessStat()

    stat.observe_present(START_TS, 0)
    stat.observe_present(START_TS, -5)

    assert stat.bad_samples == 2
    assert stat.presents == 0
    assert stat.last_ts_ns == 0  # baseline untouched


# --------------------------------------------------
# Serialization
# --------------------------------------------------

def test_to_dict_schema():
    stat = PresentSmoothnessStat()
    feed_intervals(stat, [10 * MS] * 3, 10 * MS)

    d = stat.to_dict()

    assert d["type"] == "__PRESENT_SMOOTHNESS__"
    assert set(d.keys()) == {
        "type", "count", "presents", "boundaries", "bad_samples",
        "active_time_s", "hitches", "interval_ns",
    }
    assert set(d["hitches"].keys()) == {"count", "ratio", "per_active_min"}
    assert set(d["interval_ns"].keys()) == {
        "avg", "stddev", "variance", "min", "max", "p50", "p95", "p99",
    }


def test_hitch_rate_math():
    stat = PresentSmoothnessStat()
    period = 10 * MS
    hitch_interval = 25 * MS  # > 2x period, < 100 ms boundary

    feed_intervals(stat, [period] * 58 + [hitch_interval] * 2, period)

    d = stat.to_dict()
    active_s = (58 * period + 2 * hitch_interval) / 1e9
    assert d["active_time_s"] == pytest.approx(active_s)
    assert d["hitches"]["count"] == 2
    assert d["hitches"]["ratio"] == pytest.approx(2 / 60)
    assert d["hitches"]["per_active_min"] == pytest.approx(2 / (active_s / 60.0))


def test_empty_stat_to_dict_has_zeroed_ratios():
    d = PresentSmoothnessStat().to_dict()

    assert d["count"] == 0
    assert d["active_time_s"] == 0
    assert d["hitches"] == {"count": 0, "ratio": 0.0, "per_active_min": 0.0}


def test_percentiles_over_rolling_window():
    stat = PresentSmoothnessStat()
    period = 50 * MS
    # 99 distinct active intervals: 1..99 ms (all under the 150 ms boundary)
    intervals = [i * MS for i in range(1, 100)]

    feed_intervals(stat, intervals, period)

    d = stat.to_dict()
    assert d["interval_ns"]["p50"] == 50 * MS
    assert d["interval_ns"]["p99"] == 98 * MS  # index int(98 * .99) = 97 -> value 98 ms
    assert d["interval_ns"]["min"] == 1 * MS
    assert d["interval_ns"]["max"] == 99 * MS


def test_rolling_window_is_bounded():
    stat = PresentSmoothnessStat()
    period = 10 * MS

    feed_intervals(stat, [period] * (_WINDOW_SIZE + 100), period)

    assert stat.count == _WINDOW_SIZE + 100      # totals keep counting
    assert len(stat.samples) == _WINDOW_SIZE     # window stays bounded


# --------------------------------------------------
# EventCounter integration
# --------------------------------------------------

def test_event_counter_track_present_creates_and_accumulates():
    counter = EventCounter()
    period = 10 * MS

    counter.track_present("__PRESENT_SMOOTHNESS__", "__PRESENT__", START_TS, period)
    counter.track_present("__PRESENT_SMOOTHNESS__", "__PRESENT__", START_TS + period, period)

    stats = counter.get_stats()
    s = stats["__PRESENT_SMOOTHNESS__"]["__PRESENT__"]
    assert s["type"] == "__PRESENT_SMOOTHNESS__"
    assert s["presents"] == 2
    assert s["count"] == 1


def test_event_counter_present_coexists_with_other_stat_kinds():
    counter = EventCounter()

    counter.track_present("render", "presents", START_TS, PERIOD_60HZ)
    counter.track_event("render", "pushes")
    counter.track_packet_latency("render", "change_to_present", START_TS, START_TS + 2 * MS)

    stats = counter.get_stats()
    assert stats["render"]["presents"]["type"] == "__PRESENT_SMOOTHNESS__"
    assert stats["render"]["pushes"]["type"] == "__COUNT__"
    assert stats["render"]["change_to_present"]["type"] == "__LATENCY__"
