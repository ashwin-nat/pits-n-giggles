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

import random
from typing import Optional, List
from unittest.mock import MagicMock

from lib.f1_types import ActualTyreCompound, VisualTyreCompound
from lib.tyre_wear_extrapolator import TyreWearPerLap
from src.data_per_driver import TyreSetInfo, TyreSetHistoryEntry
from .tests_data_per_driver_base import F1DataPerDriverTest

# Assuming the classes have been defined above or imported as TyreSetInfo and TyreSetHistoryEntry.

class TestTyreSetInfo(F1DataPerDriverTest):

    def test_initialization(self):
        actual_tyre_compound = random.choice(list(ActualTyreCompound))
        visual_tyre_compound = random.choice(list(VisualTyreCompound))
        tyre_set_id = 1
        tyre_age_laps = 10

        tyre_set = TyreSetInfo(actual_tyre_compound, visual_tyre_compound, tyre_set_id, tyre_age_laps)

        self.assertEqual(tyre_set.m_actual_tyre_compound, actual_tyre_compound)
        self.assertEqual(tyre_set.m_visual_tyre_compound, visual_tyre_compound)
        self.assertEqual(tyre_set.m_tyre_set_id, tyre_set_id)
        self.assertEqual(tyre_set.m_tyre_age_laps, tyre_age_laps)

    def test_toJSON(self):
        actual_tyre_compound = random.choice(list(ActualTyreCompound))
        visual_tyre_compound = random.choice(list(VisualTyreCompound))
        tyre_set_id = 1
        tyre_age_laps = 10

        tyre_set = TyreSetInfo(actual_tyre_compound, visual_tyre_compound, tyre_set_id, tyre_age_laps)

        expected_json = {
            'actual-tyre-compound': str(actual_tyre_compound),
            'visual-tyre-compound': str(visual_tyre_compound),
            'tyre-set-id': 1,
            'tyre-age-laps': 10
        }

        self.assertEqual(tyre_set.toJSON(), expected_json)

    def test_repr(self):
        actual_tyre_compound = random.choice(list(ActualTyreCompound))
        visual_tyre_compound = random.choice(list(VisualTyreCompound))
        tyre_set_id = 1
        tyre_age_laps = 10

        tyre_set = TyreSetInfo(actual_tyre_compound, visual_tyre_compound, tyre_set_id, tyre_age_laps)

        expected_repr = f"TyreSetInfo(actual_tyre_compound={str(actual_tyre_compound)}, "\
                        f"visual_tyre_compound={str(visual_tyre_compound)}, tyre_set_id=1, tyre_age_laps=10)"
        self.assertEqual(repr(tyre_set), expected_repr)

    def test_str(self):
        actual_tyre_compound = random.choice(list(ActualTyreCompound))
        visual_tyre_compound = random.choice(list(VisualTyreCompound))
        tyre_set_id = 1
        tyre_age_laps = 10

        tyre_set = TyreSetInfo(actual_tyre_compound, visual_tyre_compound, tyre_set_id, tyre_age_laps)

        expected_str =  f"Tyre Set ID: 1, Actual Compound: {str(actual_tyre_compound)}, "\
                        f"Visual Compound: {str(visual_tyre_compound)}, Tyre Age (laps): 10"
        self.assertEqual(str(tyre_set), expected_str)


class TestTyreSetHistoryEntry(F1DataPerDriverTest):

    def test_initialization(self):
        start_lap = 5
        index = 2
        tyre_set_key = "key_1"
        initial_tyre_wear = MagicMock()  # Mocking TyreWearPerLap

        history_entry = TyreSetHistoryEntry(start_lap, index, tyre_set_key, initial_tyre_wear)

        self.assertEqual(history_entry.m_start_lap, start_lap)
        self.assertEqual(history_entry.m_fitted_index, index)
        self.assertEqual(history_entry.m_tyre_set_key, tyre_set_key)
        self.assertIsNone(history_entry.m_end_lap)
        self.assertEqual(len(history_entry.m_tyre_wear_history), 1)
        self.assertEqual(history_entry.m_tyre_wear_history[0], initial_tyre_wear)

    def test_toJSON_without_tyre_wear(self):
        start_lap = 5
        index = 2
        tyre_set_key = "key_1"

        history_entry = TyreSetHistoryEntry(start_lap, index, tyre_set_key)

        expected_json = {
            "start-lap": 5,
            "end-lap": None,
            "stint-length": None,
            "fitted-index": 2,
            "tyre-set-key": "key_1",
            "tyre-wear-history": None
        }

        self.jsonComparisionUtil(history_entry.toJSON(include_tyre_wear_history=False), expected_json)

    def test_toJSON_with_tyre_wear(self):
        # Create TyreWearPerLap mock object with specific wear values
        tyre_wear_entry = TyreWearPerLap(
            fl_tyre_wear=10.5,
            fr_tyre_wear=12.3,
            rl_tyre_wear=11.2,
            rr_tyre_wear=9.8,
            lap_number=5,
            is_racing_lap=True,
            desc="Test lap"
        )

        # Start lap, fitted index, and tyre set key
        start_lap = 5
        index = 2
        tyre_set_key = "key_1"

        # Create TyreSetHistoryEntry with the tyre wear entry
        history_entry = TyreSetHistoryEntry(start_lap, index, tyre_set_key, tyre_wear_entry)
        history_entry.m_end_lap = 6

        # Expected JSON with tyre wear history included
        expected_json = {
            "start-lap": 5,
            "end-lap": 6,
            "stint-length": 2,
            "fitted-index": 2,
            "tyre-set-key": "key_1",
            "tyre-wear-history": [
                tyre_wear_entry.toJSON()
            ]
        }

        # Assert that the JSON dump with tyre wear history is correct
        self.jsonComparisionUtil(expected_json, history_entry.toJSON())

    def test_repr(self):
        start_lap = 5
        index = 2
        tyre_set_key = "key_1"

        history_entry = TyreSetHistoryEntry(start_lap, index, tyre_set_key)

        expected_repr = "start_lap: 5 end_lap: None key: key_1 tyre_wear_history_len: 0"
        self.assertEqual(repr(history_entry), expected_repr)

    def test_str(self):
        start_lap = 5
        index = 2
        tyre_set_key = "key_1"

        history_entry = TyreSetHistoryEntry(start_lap, index, tyre_set_key)

        expected_str = "start_lap: 5 end_lap: None key: key_1 tyre_wear_history_len: 0"
        self.assertEqual(str(history_entry), expected_str)
