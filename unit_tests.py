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

    def test_1_gp_p1(self):
        # Test case 1: GP - Check for pole position
        result = _get_adjacent_positions(position=1, total_cars=20, num_adjacent_cars=3)
        expected_result = [1,2,3,4,5,6,7]
        self.assertCountEqual(result, expected_result)

    def test_2_gp_p2(self):
        # Test case 2: Check for P2
        result = _get_adjacent_positions(position=1, total_cars=20, num_adjacent_cars=3)
        expected_result = [1,2,3,4,5,6,7]
        self.assertEqual(result, expected_result)

    def test_3_gp_midfield(self):
        # Test case 3: Check for P10
        result = _get_adjacent_positions(position=10, total_cars=20, num_adjacent_cars=3)
        expected_result = [7,8,9,10,11,12,13]
        self.assertEqual(result, expected_result)

    def test_4_gp_p20(self):
        # Test case 4: Check for P20
        result = _get_adjacent_positions(position=20, total_cars=20, num_adjacent_cars=3)
        expected_result = [14,15,16,17,18,19,20]
        self.assertEqual(result, expected_result)

    def test_5_gp_p19(self):
        # Test case 5: Check for P19
        result = _get_adjacent_positions(position=19, total_cars=20, num_adjacent_cars=3)
        expected_result = [14,15,16,17,18,19,20]
        self.assertEqual(result, expected_result)

    def test_6_tt_1(self):
        # Test case 6: Time Trial - 1 car
        result = _get_adjacent_positions(position=1, total_cars=1, num_adjacent_cars=3)
        expected_result = [1]
        self.assertEqual(result, expected_result)

    def test_7_tt_2(self):
        # Test case 7: Time Trial - 2 cars
        result = _get_adjacent_positions(position=1, total_cars=2, num_adjacent_cars=3)
        expected_result = [1,2]
        self.assertEqual(result, expected_result)

    def test_8_tt_3(self):
        # Test case 8: Time Trial - 3 cars
        result = _get_adjacent_positions(position=1, total_cars=3, num_adjacent_cars=3)
        expected_result = [1,2,3]
        self.assertEqual(result, expected_result)

    def shortDescription(self):
        # Override the shortDescription method to return the test method name
        return self._testMethodName

if __name__ == '__main__':
    runner = unittest.TextTestRunner(resultclass=CustomTestResult, verbosity=1)
    unittest.main(testRunner=runner)