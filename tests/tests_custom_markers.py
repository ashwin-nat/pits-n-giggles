# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

from apps.lib.custom_marker_tracker import CustomMarkerEntry, CustomMarkersHistory
from apps.lib.f1_types import LapData
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class CustomMarkersUT(F1TelemetryUnitTestsBase):
    pass

class TestCustomMarkerEntry(CustomMarkersUT):
    def setUp(self):
        self.marker = CustomMarkerEntry(
            track="Monaco",
            event_type="Overtake",
            lap=5,
            sector=LapData.Sector.SECTOR1,
            curr_lap_time="1:23.456",
            curr_lap_perc="45.67"
        )

    def test_initialization(self):
        self.assertEqual(self.marker.m_track, "Monaco")
        self.assertEqual(self.marker.m_event_type, "Overtake")
        self.assertEqual(self.marker.m_lap, 5)
        self.assertEqual(self.marker.m_sector, LapData.Sector.SECTOR1)
        self.assertEqual(self.marker.m_curr_lap_time, "1:23.456")
        self.assertEqual(self.marker.m_curr_lap_percent, "45.67")

    def test_json_conversion(self):
        json_data = self.marker.toJSON()
        self.assertEqual(json_data["track"], "Monaco")
        self.assertEqual(json_data["event-type"], "Overtake")
        self.assertEqual(json_data["lap"], "5")
        self.assertEqual(json_data["sector"], str(LapData.Sector.SECTOR1))
        self.assertEqual(json_data["curr-lap-time"], "1:23.456")
        self.assertEqual(json_data["curr-lap-percentage"], "45.67")

    def test_csv_conversion(self):
        csv_str = self.marker.toCSV()
        expected = "Monaco, Overtake, 5, SECTOR1, 1:23.456, 45.67"
        self.assertEqual(csv_str, expected)

    def test_string_representation(self):
        str_repr = str(self.marker)
        self.assertEqual(str_repr, self.marker.toCSV())

class TestCustomMarkersHistory(CustomMarkersUT):
    def setUp(self):
        self.history = CustomMarkersHistory()
        self.sample_marker = CustomMarkerEntry(
            track="Monaco",
            event_type="Overtake",
            lap=5,
            sector=LapData.Sector.SECTOR1,
            curr_lap_time="1:23.456",
            curr_lap_perc="45.67"
        )

    def test_initialization(self):
        self.assertEqual(len(self.history.m_custom_markers_history), 0)

    def test_insert_and_count(self):
        self.history.insert(self.sample_marker)
        self.assertEqual(self.history.getCount(), 1)

    def test_clear(self):
        self.history.insert(self.sample_marker)
        self.history.clear()
        self.assertEqual(self.history.getCount(), 0)

    def test_get_json_list(self):
        self.history.insert(self.sample_marker)
        json_list = self.history.getJSONList()
        self.assertEqual(len(json_list), 1)
        self.assertEqual(json_list[0]["track"], "Monaco")
        self.assertEqual(json_list[0]["event-type"], "Overtake")

    def test_get_markers_generator(self):
        self.history.insert(self.sample_marker)
        markers = self.history.getMarkers()
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0], self.sample_marker)
