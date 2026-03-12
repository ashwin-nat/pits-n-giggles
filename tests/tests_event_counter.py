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

from lib.event_counter import EventCounter
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestEventCounter(F1TelemetryUnitTestsBase):
    def _assert_packet_stat_type(self, stat):
        self.assertEqual(stat["type"], "__PACKET__")

    def _assert_event_stat_type(self, stat):
        self.assertEqual(stat["type"], "__COUNT__")

    def _assert_latency_stat_type(self, stat):
        self.assertEqual(stat["type"], "__LATENCY__")

    # --------------------------------------------------
    # Basic Behavior - Packet Tracking
    # --------------------------------------------------

    def test_empty_counter(self):
        counter = EventCounter()
        stats = counter.get_stats()
        self.assertEqual(stats, {})

    def test_single_packet_track(self):
        counter = EventCounter()

        counter.track_packet("udp", "raw", 1200)

        stats = counter.get_stats()

        self._assert_packet_stat_type(stats["udp"]["raw"])
        self.assertEqual(stats["udp"]["raw"]["count"], 1)
        self.assertEqual(stats["udp"]["raw"]["bytes"], 1200)

    def test_multiple_packet_tracks_accumulate(self):
        counter = EventCounter()

        counter.track_packet("udp", "raw", 100)
        counter.track_packet("udp", "raw", 200)
        counter.track_packet("udp", "raw", 300)

        stats = counter.get_stats()

        self._assert_packet_stat_type(stats["udp"]["raw"])
        self.assertEqual(stats["udp"]["raw"]["count"], 3)
        self.assertEqual(stats["udp"]["raw"]["bytes"], 600)

    def test_multiple_subcategories_same_category_packet(self):
        counter = EventCounter()

        counter.track_packet("udp", "raw", 100)
        counter.track_packet("udp", "parsed", 200)

        stats = counter.get_stats()

        self._assert_packet_stat_type(stats["udp"]["raw"])
        self._assert_packet_stat_type(stats["udp"]["parsed"])
        self.assertEqual(stats["udp"]["raw"]["count"], 1)
        self.assertEqual(stats["udp"]["parsed"]["count"], 1)

    def test_multiple_categories_packet(self):
        counter = EventCounter()

        counter.track_packet("udp", "raw", 100)
        counter.track_packet("zmq", "forwarded", 200)

        stats = counter.get_stats()

        self.assertIn("udp", stats)
        self.assertIn("zmq", stats)
        self._assert_packet_stat_type(stats["udp"]["raw"])
        self._assert_packet_stat_type(stats["zmq"]["forwarded"])

    # --------------------------------------------------
    # Basic Behavior - Event Tracking
    # --------------------------------------------------

    def test_single_event_track(self):
        counter = EventCounter()

        counter.track_event("lifecycle", "startup")

        stats = counter.get_stats()

        self._assert_event_stat_type(stats["lifecycle"]["startup"])
        self.assertEqual(stats["lifecycle"]["startup"]["count"], 1)
        self.assertNotIn("bytes", stats["lifecycle"]["startup"])

    def test_multiple_event_tracks_accumulate(self):
        counter = EventCounter()

        counter.track_event("ui", "window_open")
        counter.track_event("ui", "window_open")

        stats = counter.get_stats()

        self._assert_event_stat_type(stats["ui"]["window_open"])
        self.assertEqual(stats["ui"]["window_open"]["count"], 2)
        self.assertNotIn("bytes", stats["ui"]["window_open"])

    def test_event_and_packet_same_category_different_subcategories(self):
        counter = EventCounter()

        counter.track_event("udp", "socket_open")
        counter.track_packet("udp", "raw", 100)

        stats = counter.get_stats()

        self._assert_event_stat_type(stats["udp"]["socket_open"])
        self.assertEqual(stats["udp"]["socket_open"]["count"], 1)
        self.assertNotIn("bytes", stats["udp"]["socket_open"])

        self._assert_packet_stat_type(stats["udp"]["raw"])
        self.assertEqual(stats["udp"]["raw"]["count"], 1)
        self.assertEqual(stats["udp"]["raw"]["bytes"], 100)

    # --------------------------------------------------
    # Basic Behavior - Latency Tracking
    # --------------------------------------------------

    def test_single_packet_latency_track(self):
        counter = EventCounter()

        counter.track_packet_latency("udp", "ingest", 10, 25)

        stats = counter.get_stats()

        self._assert_latency_stat_type(stats["udp"]["ingest"])
        self.assertEqual(stats["udp"]["ingest"]["count"], 1)
        self.assertEqual(stats["udp"]["ingest"]["bad_latency_count"], 0)
        self.assertEqual(stats["udp"]["ingest"]["min"], 15)
        self.assertEqual(stats["udp"]["ingest"]["max"], 15)
        self.assertEqual(stats["udp"]["ingest"]["avg"], 15.0)
        self.assertEqual(stats["udp"]["ingest"]["variance"], 0.0)

    def test_multiple_packet_latency_tracks_accumulate(self):
        counter = EventCounter()

        # Latencies: 10, 30, 50
        counter.track_packet_latency("udp", "ingest", 100, 110)
        counter.track_packet_latency("udp", "ingest", 100, 130)
        counter.track_packet_latency("udp", "ingest", 100, 150)

        stats = counter.get_stats()

        self._assert_latency_stat_type(stats["udp"]["ingest"])
        self.assertEqual(stats["udp"]["ingest"]["count"], 3)
        self.assertEqual(stats["udp"]["ingest"]["bad_latency_count"], 0)
        self.assertEqual(stats["udp"]["ingest"]["min"], 10)
        self.assertEqual(stats["udp"]["ingest"]["max"], 50)
        self.assertEqual(stats["udp"]["ingest"]["avg"], 30.0)
        self.assertAlmostEqual(stats["udp"]["ingest"]["variance"], 800 / 3, places=6)

    def test_negative_packet_latency_is_not_used_in_model(self):
        counter = EventCounter()

        counter.track_packet_latency("udp", "ingest", 200, 150)

        stats = counter.get_stats()

        self._assert_latency_stat_type(stats["udp"]["ingest"])
        self.assertEqual(stats["udp"]["ingest"]["count"], 0)
        self.assertEqual(stats["udp"]["ingest"]["bad_latency_count"], 1)
        self.assertEqual(stats["udp"]["ingest"]["min"], 0)
        self.assertEqual(stats["udp"]["ingest"]["max"], 0)
        self.assertEqual(stats["udp"]["ingest"]["avg"], 0.0)
        self.assertEqual(stats["udp"]["ingest"]["variance"], 0.0)

    def test_one_negative_latency_among_five_packets(self):
        counter = EventCounter()

        # Valid latencies used in model: [30, 40, 60, 20]
        counter.track_packet_latency("udp", "ingest", 100, 130)
        counter.track_packet_latency("udp", "ingest", 100, 90)   # negative -> ignored
        counter.track_packet_latency("udp", "ingest", 100, 140)
        counter.track_packet_latency("udp", "ingest", 100, 160)
        counter.track_packet_latency("udp", "ingest", 100, 120)

        stats = counter.get_stats()

        self._assert_latency_stat_type(stats["udp"]["ingest"])
        self.assertEqual(stats["udp"]["ingest"]["count"], 4)
        self.assertEqual(stats["udp"]["ingest"]["bad_latency_count"], 1)
        self.assertEqual(stats["udp"]["ingest"]["min"], 20)
        self.assertEqual(stats["udp"]["ingest"]["max"], 60)
        self.assertEqual(stats["udp"]["ingest"]["avg"], 37.5)
        self.assertAlmostEqual(stats["udp"]["ingest"]["variance"], 218.75, places=6)

    # --------------------------------------------------
    # Edge Cases - Packet
    # --------------------------------------------------

    def test_zero_size_packet_tracking(self):
        counter = EventCounter()

        counter.track_packet("udp", "raw", 0)

        stats = counter.get_stats()

        self._assert_packet_stat_type(stats["udp"]["raw"])
        self.assertEqual(stats["udp"]["raw"]["count"], 1)
        self.assertEqual(stats["udp"]["raw"]["bytes"], 0)

    def test_negative_size_packet_tracking(self):
        """
        If your implementation allows negatives, ensure it behaves predictably.
        If you later decide to forbid negatives, update this test.
        """
        counter = EventCounter()

        counter.track_packet("udp", "raw", -100)

        stats = counter.get_stats()

        self._assert_packet_stat_type(stats["udp"]["raw"])
        self.assertEqual(stats["udp"]["raw"]["count"], 1)
        self.assertEqual(stats["udp"]["raw"]["bytes"], -100)

    def test_large_packet_values(self):
        counter = EventCounter()

        large_size = 10**9

        counter.track_packet("udp", "raw", large_size)
        counter.track_packet("udp", "raw", large_size)

        stats = counter.get_stats()

        self._assert_packet_stat_type(stats["udp"]["raw"])
        self.assertEqual(stats["udp"]["raw"]["bytes"], 2 * large_size)

    def test_many_unique_categories_packet(self):
        counter = EventCounter()

        for i in range(50):
            counter.track_packet(f"cat_{i}", "sub", i)

        stats = counter.get_stats()

        self.assertEqual(len(stats), 50)
        for i in range(50):
            self._assert_packet_stat_type(stats[f"cat_{i}"]["sub"])

    def test_many_unique_subcategories_packet(self):
        counter = EventCounter()

        for i in range(50):
            counter.track_packet("udp", f"sub_{i}", i)

        stats = counter.get_stats()

        self.assertEqual(len(stats["udp"]), 50)
        for i in range(50):
            self._assert_packet_stat_type(stats["udp"][f"sub_{i}"])

    # --------------------------------------------------
    # Structural Integrity
    # --------------------------------------------------

    def test_get_stats_returns_new_dict(self):
        counter = EventCounter()
        counter.track_packet("udp", "raw", 100)

        stats1 = counter.get_stats()
        stats2 = counter.get_stats()

        self.assertIsNot(stats1, stats2)
        self.assertIsNot(stats1["udp"], stats2["udp"])
        self._assert_packet_stat_type(stats1["udp"]["raw"])
        self._assert_packet_stat_type(stats2["udp"]["raw"])

    def test_mutating_returned_stats_does_not_affect_internal(self):
        counter = EventCounter()
        counter.track_packet("udp", "raw", 100)

        stats = counter.get_stats()
        stats["udp"]["raw"]["count"] = 999

        fresh_stats = counter.get_stats()
        self._assert_packet_stat_type(fresh_stats["udp"]["raw"])
        self.assertEqual(fresh_stats["udp"]["raw"]["count"], 1)

    # --------------------------------------------------
    # Stability
    # --------------------------------------------------

    def test_repeated_get_stats_calls_stable(self):
        counter = EventCounter()

        counter.track_packet("udp", "raw", 100)

        stats1 = counter.get_stats()
        stats2 = counter.get_stats()

        self.assertEqual(stats1, stats2)
        self._assert_packet_stat_type(stats1["udp"]["raw"])
        self._assert_packet_stat_type(stats2["udp"]["raw"])

    def test_tracking_after_get_stats(self):
        counter = EventCounter()

        counter.track_packet("udp", "raw", 100)
        counter.get_stats()
        counter.track_packet("udp", "raw", 200)

        stats = counter.get_stats()

        self._assert_packet_stat_type(stats["udp"]["raw"])
        self.assertEqual(stats["udp"]["raw"]["count"], 2)
        self.assertEqual(stats["udp"]["raw"]["bytes"], 300)
