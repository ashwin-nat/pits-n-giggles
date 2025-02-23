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

from lib.collisions_analyzer import CollisionRecord, CollisionPairKey, CollisionAnalyzer, CollisionAnalyzerMode
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class CollisionAnalyzerUT(F1TelemetryUnitTestsBase):
    pass

class TestCollisionRecord(CollisionAnalyzerUT):
    def setUp(self):
        self.record1 = CollisionRecord(
            driver_1_name="Hamilton",
            driver_1_lap=1,
            driver_1_index=44,
            driver_2_name="Verstappen",
            driver_2_lap=1,
            driver_2_index=33,
            row_id=1
        )
        self.record2 = CollisionRecord(
            driver_1_name="Hamilton",
            driver_1_lap=1,
            driver_1_index=44,
            driver_2_name="Verstappen",
            driver_2_lap=1,
            driver_2_index=33,
            row_id=1
        )
        self.record3 = CollisionRecord(
            driver_1_name="Leclerc",
            driver_1_lap=2,
            driver_1_index=16,
            driver_2_name="Sainz",
            driver_2_lap=2,
            driver_2_index=55,
            row_id=2
        )

    def test_equality(self):
        self.assertEqual(self.record1, self.record2)
        self.assertNotEqual(self.record1, self.record3)

    def test_comparison_operators(self):
        self.assertTrue(self.record1 <= self.record3)
        self.assertTrue(self.record1 < self.record3)
        self.assertFalse(self.record1 > self.record3)
        self.assertTrue(self.record3 >= self.record1)

    def test_json_conversion(self):
        json_data = self.record1.toJSON()
        self.assertEqual(json_data["driver-1-name"], "Hamilton")
        self.assertEqual(json_data["driver-1-lap"], 1)
        self.assertEqual(json_data["driver-1-index"], 44)
        self.assertEqual(json_data["driver-2-name"], "Verstappen")
        self.assertEqual(json_data["driver-2-lap"], 1)
        self.assertEqual(json_data["driver-2-index"], 33)
        self.assertEqual(json_data["overtake-id"], 1)

        # Test fromJSON
        reconstructed_record = CollisionRecord.fromJSON(json_data)
        self.assertEqual(self.record1, reconstructed_record)

class TestCollisionPairKey(CollisionAnalyzerUT):
    def setUp(self):
        self.pair1 = CollisionPairKey(44, "Hamilton", 33, "Verstappen")
        self.pair2 = CollisionPairKey(33, "Verstappen", 44, "Hamilton")
        self.pair3 = CollisionPairKey(16, "Leclerc", 55, "Sainz")

    def test_equality(self):
        self.assertEqual(self.pair1, self.pair2)  # Order shouldn't matter
        self.assertNotEqual(self.pair1, self.pair3)

    def test_hash(self):
        self.assertEqual(hash(self.pair1), hash(self.pair2))
        self.assertNotEqual(hash(self.pair1), hash(self.pair3))

    def test_contains(self):
        self.assertTrue(44 in self.pair1)
        self.assertTrue(33 in self.pair1)
        self.assertFalse(16 in self.pair1)

class TestCollisionAnalyzer(CollisionAnalyzerUT):
    def setUp(self):
        self.sample_records = [
            CollisionRecord("Hamilton", 1, 44, "Verstappen", 1, 33, 1),
            CollisionRecord("Hamilton", 2, 44, "Verstappen", 2, 33, 2),
            CollisionRecord("Leclerc", 1, 16, "Sainz", 1, 55, 3)
        ]

        self.sample_csv = [
            "Hamilton,44,1,Verstappen,33,1",
            "Hamilton,44,2,Verstappen,33,2",
            "Leclerc,16,1,Sainz,55,1"
        ]

    def test_init_with_records(self):
        analyzer = CollisionAnalyzer(
            CollisionAnalyzerMode.INPUT_MODE_LIST_COLLISION_RECORDS,
            self.sample_records
        )
        self.assertEqual(len(analyzer.m_collision_records), 3)
        self.assertEqual(analyzer.getNumCollisions(), 6)  # Each collision counts for both drivers

    def test_init_with_csv_list(self):
        analyzer = CollisionAnalyzer(
            CollisionAnalyzerMode.INPUT_MODE_LIST_CSV,
            self.sample_csv
        )
        self.assertEqual(len(analyzer.m_collision_records), 3)
        self.assertEqual(analyzer.getNumCollisions(), 6)

    def test_most_collisions(self):
        analyzer = CollisionAnalyzer(
            CollisionAnalyzerMode.INPUT_MODE_LIST_COLLISION_RECORDS,
            self.sample_records
        )
        most_collided_drivers, count = analyzer.getMostCollisions()
        self.assertEqual(count, 2)  # Hamilton and Verstappen each involved in 2 collisions
        self.assertEqual(len(most_collided_drivers), 2)  # Both Hamilton and Verstappen should be returned
        driver_indices = [idx for idx, _ in most_collided_drivers]
        self.assertTrue(44 in driver_indices)  # Hamilton's index
        self.assertTrue(33 in driver_indices)  # Verstappen's index

    def test_most_collided_pairs_json(self):
        analyzer = CollisionAnalyzer(
            CollisionAnalyzerMode.INPUT_MODE_LIST_COLLISION_RECORDS,
            self.sample_records
        )
        result = analyzer.getMostCollidedPairsJSON()
        self.assertEqual(result["count"], 2)  # Hamilton-Verstappen pair has 2 collisions
        self.assertEqual(len(result["collision-pairs"]), 1)  # Only one pair with maximum collisions
        pair = result["collision-pairs"][0]
        self.assertTrue(
            (pair["driver-1-index"] == 44 and pair["driver-2-index"] == 33) or
            (pair["driver-1-index"] == 33 and pair["driver-2-index"] == 44)
        )

    def test_full_json_output(self):
        analyzer = CollisionAnalyzer(
            CollisionAnalyzerMode.INPUT_MODE_LIST_COLLISION_RECORDS,
            self.sample_records
        )
        json_output = analyzer.toJSON()

        self.assertIn("most-collided-pairs", json_output)
        self.assertIn("collision-pairs", json_output)
        self.assertIn("records", json_output)

        self.assertEqual(len(json_output["records"]), 3)
        self.assertEqual(len(json_output["collision-pairs"]), 2)  # Hamilton-Verstappen and Leclerc-Sainz
