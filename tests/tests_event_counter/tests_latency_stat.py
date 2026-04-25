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

import math
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from lib.event_counter.frame_render import FrameTimingStat
from lib.event_counter.latency import LatencyStat, _WINDOW_SIZE, _EWMA_ALPHA
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

def _make_latency_stat(*latencies: int) -> LatencyStat:
    """Helper: build a LatencyStat pre-loaded with the given latency values."""
    stat = LatencyStat()
    for lat in latencies:
        stat.observe_packet(0, lat)
    return stat


class TestFrameTimingStat(F1TelemetryUnitTestsBase):

    def _assert_frame_render_stat_type(self, stat):
        self.assertEqual(stat["type"], "__FRAME_TIMING__")

    def test_frame_render_stat_to_dict_with_zero_count(self):
        stat = FrameTimingStat(frame_budget_ns=16_666_666)
        serialized = stat.to_dict()

        self._assert_frame_render_stat_type(serialized)
        self.assertEqual(serialized["count"], 0)
        self.assertEqual(serialized["interval_ns"]["min"], 0)
        self.assertEqual(serialized["interval_ns"]["max"], 0)
        self.assertEqual(serialized["interval_ns"]["avg"], 0.0)
        self.assertEqual(serialized["interval_ns"]["variance"], 0.0)
        self.assertEqual(serialized["interval_ns"]["stddev"], 0.0)
        self.assertEqual(serialized["fps"]["avg"], 0.0)
        self.assertEqual(serialized["fps"]["min"], 0.0)
        self.assertEqual(serialized["fps"]["max"], 0.0)
        self.assertAlmostEqual(serialized["fps"]["target"], 1e9 / 16_666_666, places=6)
        self.assertEqual(serialized["budget"]["missed_frames"], 0)
        self.assertEqual(serialized["budget"]["miss_ratio"], 0.0)
        self.assertEqual(serialized["budget"]["max_miss_streak"], 0)
        self.assertEqual(serialized["pacing_error_ns"]["avg"], 0.0)
        self.assertEqual(serialized["pacing_error_ns"]["max"], 0)


class TestLatencyStatExtended(F1TelemetryUnitTestsBase):
    """Unit tests for the extended LatencyStat metrics:
    percentiles, jitter, EWMA, tail ratio, and rolling-window behaviour.
    """

    # --------------------------------------------------
    # Regression – existing metrics must remain correct
    # --------------------------------------------------

    def test_regression_existing_fields_unchanged(self):
        stat = _make_latency_stat(10, 30, 50)
        d = stat.to_dict()
        self.assertEqual(d["type"], "__LATENCY__")
        self.assertEqual(d["count"], 3)
        self.assertEqual(d["bad_latency_count"], 0)
        self.assertEqual(d["min_ns"], 10)
        self.assertEqual(d["max_ns"], 50)
        self.assertEqual(d["avg_ns"], 30.0)
        self.assertAlmostEqual(d["variance_ns"], 800 / 3, places=6)
        self.assertAlmostEqual(d["stddev_ns"], math.sqrt(800 / 3), places=6)

    def test_regression_negative_latency_still_counted_as_bad(self):
        stat = LatencyStat()
        stat.observe_packet(200, 150)   # latency = -50
        d = stat.to_dict()
        self.assertEqual(d["count"], 0)
        self.assertEqual(d["bad_latency_count"], 1)
        self.assertEqual(d["min_ns"], 0)
        self.assertEqual(d["max_ns"], 0)

    # --------------------------------------------------
    # Percentiles – known dataset
    # --------------------------------------------------

    def test_percentiles_known_dataset(self):
        # Samples 1..10; sorted = [1,2,3,4,5,6,7,8,9,10]
        # p50: k = int(9 * 0.50) = 4 → sorted[4] = 5
        # p95: k = int(9 * 0.95) = 8 → sorted[8] = 9
        # p99: k = int(9 * 0.99) = 8 → sorted[8] = 9
        stat = _make_latency_stat(*range(1, 11))
        d = stat.to_dict()
        self.assertEqual(d["p50_ns"], 5)
        self.assertEqual(d["p95_ns"], 9)
        self.assertEqual(d["p99_ns"], 9)

    def test_percentiles_single_sample(self):
        stat = _make_latency_stat(42)
        d = stat.to_dict()
        self.assertEqual(d["p50_ns"], 42)
        self.assertEqual(d["p95_ns"], 42)
        self.assertEqual(d["p99_ns"], 42)

    def test_percentiles_all_identical_samples(self):
        stat = _make_latency_stat(*([100] * 50))
        d = stat.to_dict()
        self.assertEqual(d["p50_ns"], 100)
        self.assertEqual(d["p95_ns"], 100)
        self.assertEqual(d["p99_ns"], 100)

    def test_percentiles_zero_samples(self):
        stat = LatencyStat()
        d = stat.to_dict()
        self.assertEqual(d["p50_ns"], 0)
        self.assertEqual(d["p95_ns"], 0)
        self.assertEqual(d["p99_ns"], 0)

    # --------------------------------------------------
    # Rolling window – old samples are discarded
    # --------------------------------------------------

    def test_rolling_window_truncation(self):
        # Feed _WINDOW_SIZE + 88 samples (values 1..600 assuming WINDOW_SIZE=512).
        total = _WINDOW_SIZE + 88
        stat = _make_latency_stat(*range(1, total + 1))

        # Window should contain only the last _WINDOW_SIZE samples.
        self.assertEqual(len(stat.samples), _WINDOW_SIZE)

        # The first discarded value is total - _WINDOW_SIZE + 1 = 89.
        # All retained values are >= 89.
        self.assertGreaterEqual(min(stat.samples), total - _WINDOW_SIZE + 1)

    def test_rolling_window_percentiles_reflect_only_recent_samples(self):
        # Fill window with low values (1), then overwrite entirely with high values (1000).
        stat = LatencyStat()
        for _ in range(_WINDOW_SIZE):
            stat.observe_packet(0, 1)
        for _ in range(_WINDOW_SIZE):
            stat.observe_packet(0, 1000)

        d = stat.to_dict()
        # After full overwrite every percentile must be 1000.
        self.assertEqual(d["p50_ns"], 1000)
        self.assertEqual(d["p95_ns"], 1000)
        self.assertEqual(d["p99_ns"], 1000)

    # --------------------------------------------------
    # Jitter
    # --------------------------------------------------

    def test_jitter_constant_latency(self):
        stat = _make_latency_stat(*([500] * 10))
        d = stat.to_dict()
        self.assertEqual(d["jitter_avg_ns"], 0.0)
        self.assertEqual(d["jitter_max_ns"], 0)

    def test_jitter_alternating_latency(self):
        # Alternating 100 and 200: jitter is always 100.
        stat = _make_latency_stat(100, 200, 100, 200)
        d = stat.to_dict()
        self.assertAlmostEqual(d["jitter_avg_ns"], 100.0, places=6)
        self.assertEqual(d["jitter_max_ns"], 100)

    def test_jitter_single_sample_is_zero(self):
        stat = _make_latency_stat(300)
        d = stat.to_dict()
        self.assertEqual(d["jitter_avg_ns"], 0.0)
        self.assertEqual(d["jitter_max_ns"], 0)

    def test_jitter_max_tracks_largest_gap(self):
        # Gaps: |200-100|=100, |500-200|=300, |510-500|=10
        stat = _make_latency_stat(100, 200, 500, 510)
        d = stat.to_dict()
        self.assertEqual(d["jitter_max_ns"], 300)
        self.assertAlmostEqual(d["jitter_avg_ns"], (100 + 300 + 10) / 3, places=6)

    def test_jitter_zero_samples(self):
        stat = LatencyStat()
        d = stat.to_dict()
        self.assertEqual(d["jitter_avg_ns"], 0.0)
        self.assertEqual(d["jitter_max_ns"], 0)

    # --------------------------------------------------
    # EWMA
    # --------------------------------------------------

    def test_ewma_first_sample_initialised_to_latency(self):
        stat = _make_latency_stat(200)
        self.assertAlmostEqual(stat.to_dict()["ewma_ns"], 200.0, places=6)

    def test_ewma_smoothing_over_sequence(self):
        # Manually compute expected EWMA for [100, 200, 300]
        alpha = _EWMA_ALPHA
        ewma = 100.0
        ewma = alpha * 200 + (1 - alpha) * ewma   # 110.0
        ewma = alpha * 300 + (1 - alpha) * ewma   # 129.0
        stat = _make_latency_stat(100, 200, 300)
        self.assertAlmostEqual(stat.to_dict()["ewma_ns"], ewma, places=6)

    def test_ewma_zero_samples_returns_zero(self):
        stat = LatencyStat()
        self.assertEqual(stat.to_dict()["ewma_ns"], 0.0)

    def test_ewma_converges_toward_constant(self):
        # After many identical samples EWMA should approach that value.
        stat = _make_latency_stat(*([1000] * 200))
        self.assertAlmostEqual(stat.to_dict()["ewma_ns"], 1000.0, places=0)

    # --------------------------------------------------
    # Tail ratio
    # --------------------------------------------------

    def test_tail_ratio_normal_case(self):
        # Dataset where p99 > p50 → ratio > 1
        # samples 1..100; p50: k=int(99*0.5)=49 → 50; p99: k=int(99*0.99)=98 → 99
        stat = _make_latency_stat(*range(1, 101))
        d = stat.to_dict()
        self.assertAlmostEqual(d["tail_ratio"], d["p99_ns"] / d["p50_ns"], places=6)

    def test_tail_ratio_zero_division_when_p50_is_zero(self):
        # All samples are 0 → p50=0 → must not raise, must return 0.0
        stat = _make_latency_stat(*([0] * 10))
        d = stat.to_dict()
        self.assertEqual(d["tail_ratio"], 0.0)

    def test_tail_ratio_zero_samples(self):
        stat = LatencyStat()
        d = stat.to_dict()
        self.assertEqual(d["tail_ratio"], 0.0)
