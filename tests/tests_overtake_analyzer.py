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
from tempfile import NamedTemporaryFile
from colorama import Fore, Style
import sys
import json

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode, OvertakeRecord, OvertakeRivalryKey
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class OvertakeAnalyzerUT(F1TelemetryUnitTestsBase):
    pass

class TestOvertakeAnalyzerListObj(OvertakeAnalyzerUT):
    def setUp(self):
        # Create a sample data set

        # Updated sample data with integer values
        self.sample_data = [
            OvertakeRecord("HAMILTON", 1, "RUSSELL", 1, 0),
            OvertakeRecord("PIASTRI", 1, "ALONSO", 1, 1),
            OvertakeRecord("LECLERC", 2, "STROLL", 2, 2),
            OvertakeRecord("TSUNODA", 2, "GASLY", 2, 3),
            OvertakeRecord("PIASTRI", 3, "NORRIS", 3, 4),
            OvertakeRecord("NORRIS", 3, "PIASTRI", 3, 5),
            OvertakeRecord("HAMILTON", 4, "STROLL", 4, 6),
            OvertakeRecord("RUSSELL", 5, "HAMILTON", 5, 7),
        ]

        # Initialize OvertakeAnalyzer with the temporary file
        self.analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS, self.sample_data)

    def tearDown(self):
        # No Op
        return

    def test_most_overtakes(self):
        drivers, count = self.analyzer.getMostOvertakes()
        expected_drivers = ['HAMILTON', 'PIASTRI']
        self.assertEqual(len(drivers), 2)
        self.assertEqual(count, 2)
        for driver in expected_drivers:
            self.assertIn(driver, drivers)

    def test_most_overtaken(self):
        drivers, count = self.analyzer.getMostOvertaken()
        expected_drivers = ['STROLL']
        self.assertEqual(count, 2)
        for driver in expected_drivers:
            self.assertIn(driver, drivers)

    def assertOvertakeRecordInList(self, record, record_list, message=None):
        record_str = str(record)
        record_list_str = [str(r) for r in record_list]
        error_message = f"{record_str} not found in {record_list_str}"
        if message:
            error_message = f"{message}: {error_message}"
        self.assertIn(record, record_list, error_message)

    def test_most_heated_rivalry(self):
        rivalries_data = self.analyzer.getMostHeatedRivalries()
        expected_rivalries = {
            OvertakeRivalryKey('PIASTRI', 'NORRIS') : [
                OvertakeRecord(
                    overtaking_driver_name='PIASTRI',
                    overtaking_driver_lap=3,
                    overtaken_driver_name='NORRIS',
                    overtaken_driver_lap=3,
                    row_id=4),
                OvertakeRecord(
                    overtaking_driver_name='NORRIS',
                    overtaking_driver_lap=3,
                    overtaken_driver_name='PIASTRI',
                    overtaken_driver_lap=3,
                    row_id=5)
            ],
            OvertakeRivalryKey('HAMILTON', 'RUSSELL') : [
                OvertakeRecord(
                    overtaking_driver_name='HAMILTON',
                    overtaking_driver_lap=1,
                    overtaken_driver_name='RUSSELL',
                    overtaken_driver_lap=1,
                    row_id=0),
                OvertakeRecord(
                    overtaking_driver_name='RUSSELL',
                    overtaking_driver_lap=5,
                    overtaken_driver_name='HAMILTON',
                    overtaken_driver_lap=5,
                    row_id=7)
            ]
        }
        for overtake_key, overtake_data in rivalries_data.items():
            self.assertEqual(len(overtake_data), 2)
            self.assertIn(overtake_key, expected_rivalries.keys())
            for record in overtake_data:
                # self.assertIn(record, expected_rivalries[overtake_key])
                self.assertOvertakeRecordInList(record, expected_rivalries[overtake_key], message=f"Key: {overtake_key}")

    def test_total_overtakes(self):
        total_overtakes = self.analyzer.getTotalNumberOfOvertakes()
        self.assertEqual(total_overtakes, 8)

    def test_format_overtakes_involved(self):
        expected_formatted_overtakes = [
            "HAMILTON overtook RUSSELL in lap 1",
            "PIASTRI overtook ALONSO in lap 1",
            "LECLERC overtook STROLL in lap 2",
            "TSUNODA overtook GASLY in lap 2",
            "PIASTRI overtook NORRIS in lap 3",
            "NORRIS overtook PIASTRI in lap 3",
            "HAMILTON overtook STROLL in lap 4",
            "RUSSELL overtook HAMILTON in lap 5",
        ]

        overtakes_data = [
            OvertakeRecord("HAMILTON", 1, "RUSSELL", 1, 0),
            OvertakeRecord("PIASTRI", 1, "ALONSO", 1, 1),
            OvertakeRecord("LECLERC", 2, "STROLL", 2, 2),
            OvertakeRecord("TSUNODA", 2, "GASLY", 2, 3),
            OvertakeRecord("PIASTRI", 3, "NORRIS", 3, 4),
            OvertakeRecord("NORRIS", 3, "PIASTRI", 3, 5),
            OvertakeRecord("HAMILTON", 4, "STROLL", 4, 6),
            OvertakeRecord("RUSSELL", 5, "HAMILTON", 5, 7),
        ]

        formatted_overtakes = self.analyzer.formatOvertakesInvolved(overtakes_data)
        self.assertEqual(formatted_overtakes, expected_formatted_overtakes)

class TestOvertakeAnalyzerFileCsv(OvertakeAnalyzerUT):
    def setUp(self):
        # Create a temporary CSV file with sample data
        self.sample_data = """
        1, HAMILTON, 1, RUSSELL
        1, PIASTRI, 1, ALONSO
        2, LECLERC, 2, STROLL
        2, TSUNODA, 2, GASLY
        3, PIASTRI, 3, NORRIS
        3, NORRIS, 3, PIASTRI
        4, HAMILTON, 4, STROLL
        5, RUSSELL, 5, HAMILTON
        """
        self.input_json = {
            'overtakes' : {
                'records' : self.sample_data.strip().splitlines()
            }
        }
        self.temp_file = NamedTemporaryFile(mode='w', delete=False)
        json.dump(self.input_json, self.temp_file)
        self.temp_file.close()

        # Initialize OvertakeAnalyzer with the temporary file
        self.analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_FILE_CSV, self.temp_file.name)

    def tearDown(self):
        # Clean up the temporary file
        self.temp_file.close()

    def test_most_overtakes(self):
        drivers, count = self.analyzer.getMostOvertakes()
        expected_drivers = ['HAMILTON', 'PIASTRI']
        self.assertEqual(len(drivers), 2)
        self.assertEqual(count, 2)
        for driver in expected_drivers:
            self.assertIn(driver, drivers)

    def test_most_overtaken(self):
        drivers, count = self.analyzer.getMostOvertaken()
        expected_drivers = ['STROLL']
        self.assertEqual(count, 2)
        for driver in expected_drivers:
            self.assertIn(driver, drivers)

    def assertOvertakeRecordInList(self, record, record_list, message=None):
        record_str = str(record)
        record_list_str = [str(r) for r in record_list]
        error_message = f"{record_str} not found in {record_list_str}"
        if message:
            error_message = f"{message}: {error_message}"
        self.assertIn(record, record_list, error_message)

    def test_most_heated_rivalry(self):
        rivalries_data = self.analyzer.getMostHeatedRivalries()
        expected_rivalries = {
            OvertakeRivalryKey('PIASTRI', 'NORRIS') : [
                OvertakeRecord(
                    overtaking_driver_name='PIASTRI',
                    overtaking_driver_lap=3,
                    overtaken_driver_name='NORRIS',
                    overtaken_driver_lap=3,
                    row_id=4),
                OvertakeRecord(
                    overtaking_driver_name='NORRIS',
                    overtaking_driver_lap=3,
                    overtaken_driver_name='PIASTRI',
                    overtaken_driver_lap=3,
                    row_id=5)
            ],
            OvertakeRivalryKey('HAMILTON', 'RUSSELL') : [
                OvertakeRecord(
                    overtaking_driver_name='HAMILTON',
                    overtaking_driver_lap=1,
                    overtaken_driver_name='RUSSELL',
                    overtaken_driver_lap=1,
                    row_id=0),
                OvertakeRecord(
                    overtaking_driver_name='RUSSELL',
                    overtaking_driver_lap=5,
                    overtaken_driver_name='HAMILTON',
                    overtaken_driver_lap=5,
                    row_id=7)
            ]
        }
        for overtake_key, overtake_data in rivalries_data.items():
            self.assertEqual(len(overtake_data), 2)
            self.assertIn(overtake_key, expected_rivalries.keys())
            for record in overtake_data:
                # self.assertIn(record, expected_rivalries[overtake_key])
                self.assertOvertakeRecordInList(record, expected_rivalries[overtake_key], message=f"Key: {overtake_key}")

    def test_total_overtakes(self):
        total_overtakes = self.analyzer.getTotalNumberOfOvertakes()
        self.assertEqual(total_overtakes, 8)

    def test_format_overtakes_involved(self):
        expected_formatted_overtakes = [
            "HAMILTON overtook RUSSELL in lap 1",
            "PIASTRI overtook ALONSO in lap 1",
            "LECLERC overtook STROLL in lap 2",
            "TSUNODA overtook GASLY in lap 2",
            "PIASTRI overtook NORRIS in lap 3",
            "NORRIS overtook PIASTRI in lap 3",
            "HAMILTON overtook STROLL in lap 4",
            "RUSSELL overtook HAMILTON in lap 5",
        ]

        overtakes_data = [
            OvertakeRecord("HAMILTON", 1, "RUSSELL", 1, 0),
            OvertakeRecord("PIASTRI", 1, "ALONSO", 1, 1),
            OvertakeRecord("LECLERC", 2, "STROLL", 2, 2),
            OvertakeRecord("TSUNODA", 2, "GASLY", 2, 3),
            OvertakeRecord("PIASTRI", 3, "NORRIS", 3, 4),
            OvertakeRecord("NORRIS", 3, "PIASTRI", 3, 5),
            OvertakeRecord("HAMILTON", 4, "STROLL", 4, 6),
            OvertakeRecord("RUSSELL", 5, "HAMILTON", 5, 7),
        ]

        formatted_overtakes = self.analyzer.formatOvertakesInvolved(overtakes_data)
        self.assertEqual(formatted_overtakes, expected_formatted_overtakes)

class TestOvertakeAnalyzerListCsv(OvertakeAnalyzerUT):

    def setUp(self):
        # Create a temporary CSV file with sample data
        self.sample_data = [
            "1, HAMILTON, 1, RUSSELL",
            "1, PIASTRI, 1, ALONSO",
            "2, LECLERC, 2, STROLL",
            "2, TSUNODA, 2, GASLY",
            "3, PIASTRI, 3, NORRIS",
            "3, NORRIS, 3, PIASTRI",
            "4, HAMILTON, 4, STROLL",
            "5, RUSSELL, 5, HAMILTON"
        ]

        # Initialize OvertakeAnalyzer with the temporary file
        self.analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_LIST_CSV, self.sample_data)

    def tearDown(self):
        # Clean up the temporary file
        return

class TestOvertakeAnalyzerEmptyInput(OvertakeAnalyzerUT):
    def test_empty_file_input(self):
        # Create an empty temporary CSV file
        temp_file = NamedTemporaryFile(mode='w', delete=False)
        temp_file.close()

        # Initialize OvertakeAnalyzer with the empty file
        from json.decoder import JSONDecodeError
        with self.assertRaises(JSONDecodeError):
            analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_FILE_CSV, temp_file.name)

    def test_empty_list_input(self):
        # Initialize OvertakeAnalyzer with an empty list
        analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_LIST_CSV, [])

        # Test most overtakes
        drivers, count = analyzer.getMostOvertakes()
        self.assertEqual(drivers, [])
        self.assertEqual(count, 0)

        # Test most overtaken
        drivers, count = analyzer.getMostOvertaken()
        self.assertEqual(drivers, [])
        self.assertEqual(count, 0)

        # Test most heated rivalry
        rivalries_data = analyzer.getMostHeatedRivalries()
        self.assertEqual(rivalries_data, {})

        # Test total overtakes
        total_overtakes = analyzer.getTotalNumberOfOvertakes()
        self.assertEqual(total_overtakes, 0)

        # Test formatted overtakes
        overtakes_data = []
        formatted_overtakes = analyzer.formatOvertakesInvolved(overtakes_data)
        self.assertEqual(formatted_overtakes, [])

class TestOvertakeAnalyzerInvalidData(OvertakeAnalyzerUT):
    def test_invalid_data_handling_list(self):
        # Invalid CSV data with missing values
        invalid_data = [
            "1, HAMILTON, 1, RUSSELL",
            "2, LECLERC, 2",  # Invalid: Missing values
            "3, PIASTRI, 3, NORRIS",
        ]

        # Initializing OvertakeAnalyzer with invalid CSV data should raise a ValueError
        with self.assertRaises(ValueError):
            analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_LIST_CSV, invalid_data)

    def test_invalid_data_handling_file(self):
        # Create a temporary CSV file with invalid data
        invalid_data = "1, HAMILTON, 1, RUSSELL\n2, LECLERC, 2\n3, PIASTRI, 3, NORRIS"

        # Write the invalid data to a temporary file
        temp_file = NamedTemporaryFile(mode='w', delete=False)
        temp_file.write(invalid_data)
        temp_file.close()

        # Initializing OvertakeAnalyzer with invalid CSV file should raise a ValueError
        with self.assertRaises(ValueError):
            analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_FILE_CSV, temp_file.name)

        # Clean up the temporary file
        os.remove(temp_file.name)
