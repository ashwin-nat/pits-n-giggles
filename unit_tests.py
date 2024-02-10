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

import unittest
from telemetry_data import _get_adjacent_positions

class CustomTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        print(f"\nRunning test: {test.shortDescription()}")

class TestTelemetryData(unittest.TestCase):

    def test_gp_p1(self):
        # GP - Check for pole position
        result = _get_adjacent_positions(position=1, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(1, 8)]
        self.assertCountEqual(result, expected_result)

    def test_gp_p2(self):
        # Check for P2
        result = _get_adjacent_positions(position=1, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(1, 8)]
        self.assertEqual(result, expected_result)

    def test_gp_midfield(self):
        # Check for P10
        result = _get_adjacent_positions(position=10, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(7, 14)]
        self.assertEqual(result, expected_result)

    def test_gp_p20(self):
        # Check for P20
        result = _get_adjacent_positions(position=20, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(14, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_p19(self):
        # Check for P19
        result = _get_adjacent_positions(position=19, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(14, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p1(self):
        # Check for P1 in full table output
        result = _get_adjacent_positions(position=1, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p2(self):
        # Check for P2 in full table output
        result = _get_adjacent_positions(position=2, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p10(self):
        # Check for P10 in full table output
        result = _get_adjacent_positions(position=10, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p19(self):
        # Check for P19 in full table output
        result = _get_adjacent_positions(position=19, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p20(self):
        # Check for P20 in full table output
        result = _get_adjacent_positions(position=20, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_tt_1(self):
        # Time Trial - 1 car
        result = _get_adjacent_positions(position=1, total_cars=1, num_adjacent_cars=3)
        expected_result = [1]
        self.assertEqual(result, expected_result)

    def test_tt_2(self):
        # Time Trial - 2 cars
        result = _get_adjacent_positions(position=1, total_cars=2, num_adjacent_cars=3)
        expected_result = [1,2]
        self.assertEqual(result, expected_result)

    def test_tt_3(self):
        # Time Trial - 3 cars
        result = _get_adjacent_positions(position=1, total_cars=3, num_adjacent_cars=3)
        expected_result = [1,2,3]
        self.assertEqual(result, expected_result)

    def shortDescription(self):
        # Override the shortDescription method to return the test method name
        return self._testMethodName

if __name__ == '__main__':
    runner = unittest.TextTestRunner(resultclass=CustomTestResult, verbosity=1)
    unittest.main(testRunner=runner)