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
import os
from tempfile import NamedTemporaryFile
from colorama import Fore, Style
import random
import cProfile
import sys
import json

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.packet_cap import F1PacketCapture, F1PktCapFileHeader
from src.telemetry_data import _getAdjacentPositions
from lib.overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode, OvertakeRecord, OvertakeRivalryKey

# Initialize colorama
from colorama import init
init(autoreset=True)

# ----------------------------------------------------------------------------------------------------------------------

class CustomTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        test_class_name = test.getFullTestName()
        test_description = test.shortDescription()
        print(f"{Fore.MAGENTA}{Style.BRIGHT}Running test: {Fore.CYAN}{Style.BRIGHT}{test_class_name}.{Fore.YELLOW}{Style.BRIGHT}{test_description}", end="")

    def addSuccess(self, test):
        super().addSuccess(test)
        print(f" {Fore.GREEN}[PASS]{Style.RESET_ALL}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f" {Fore.RED}[FAIL]{Style.RESET_ALL}")

    def addError(self, test, err):
        super().addError(test, err)
        print(f" {Fore.RED}[ERROR]{Style.RESET_ALL}")

class F1TelemetryUnitTestsBase(unittest.TestCase):

    def shortDescription(self):
        return self._testMethodName

    def getFullTestName(self):
        test_class = self.__class__
        test_hierarchy = [test_class.__name__]

        while issubclass(test_class, unittest.TestCase):
            parent_class = test_class.__bases__[0]
            if issubclass(parent_class, unittest.TestCase):
                if parent_class.__name__ == 'F1TelemetryUnitTestsBase':
                    break
                test_hierarchy.insert(0, parent_class.__name__)
            test_class = parent_class

        return '.'.join(test_hierarchy)

# -----------------------------------------ADJACENT-POSITIONS-----------------------------------------------------------

class TestAdjacentPositions(F1TelemetryUnitTestsBase):

    def test_gp_p1(self):
        # GP - Check for pole position
        result = _getAdjacentPositions(position=1, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(1, 8)]
        self.assertCountEqual(result, expected_result)

    def test_gp_p2(self):
        # Check for P2
        result = _getAdjacentPositions(position=1, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(1, 8)]
        self.assertEqual(result, expected_result)

    def test_gp_midfield(self):
        # Check for P10
        result = _getAdjacentPositions(position=10, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(7, 14)]
        self.assertEqual(result, expected_result)

    def test_gp_p20(self):
        # Check for P20
        result = _getAdjacentPositions(position=20, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(14, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_p19(self):
        # Check for P19
        result = _getAdjacentPositions(position=19, total_cars=20, num_adjacent_cars=3)
        expected_result = [i for i in range(14, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p1(self):
        # Check for P1 in full table output
        result = _getAdjacentPositions(position=1, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p2(self):
        # Check for P2 in full table output
        result = _getAdjacentPositions(position=2, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p10(self):
        # Check for P10 in full table output
        result = _getAdjacentPositions(position=10, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p19(self):
        # Check for P19 in full table output
        result = _getAdjacentPositions(position=19, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p20(self):
        # Check for P20 in full table output
        result = _getAdjacentPositions(position=20, total_cars=20, num_adjacent_cars=20)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_gp_full_table_p20_huge_num_adj_cars(self):
        # Check for P20 in full table output
        result = _getAdjacentPositions(position=20, total_cars=20, num_adjacent_cars=50)
        expected_result = [i for i in range(1, 21)]
        self.assertEqual(result, expected_result)

    def test_tt_1(self):
        # Time Trial - 1 car
        result = _getAdjacentPositions(position=1, total_cars=1, num_adjacent_cars=3)
        expected_result = [1]
        self.assertEqual(result, expected_result)

    def test_tt_2(self):
        # Time Trial - 2 cars
        result = _getAdjacentPositions(position=1, total_cars=2, num_adjacent_cars=3)
        expected_result = [1,2]
        self.assertEqual(result, expected_result)

    def test_tt_3(self):
        # Time Trial - 3 cars
        result = _getAdjacentPositions(position=1, total_cars=3, num_adjacent_cars=3)
        expected_result = [1,2,3]
        self.assertEqual(result, expected_result)

# ------------------------------------------PACKET-CAPTURE--------------------------------------------------------------

class TestF1PacketCapture(F1TelemetryUnitTestsBase):
    pass

class FullPCapTests(TestF1PacketCapture):
    # Configurable max_packet_len value
    max_packet_len = 1250
    max_num_packets = 5000

    def setUp(self):
        # Create an instance of F1PacketCapture for each test
        self.capture = F1PacketCapture()
        self.m_created_files = []

    def dumpToFileHelper(self, file_name=None):
        file_name, packets_count, bytes_count = self.capture.dumpToFile(file_name)
        self.m_created_files.append(file_name)  # Keep track of created files
        return file_name, packets_count, bytes_count

    def test_add_data(self):
        """Test adding data to F1PacketCapture."""
        entry_data = b'\x01\x02\x03\x04'
        self.capture.add(entry_data)

        # Ensure that the entry has been added to the packet history
        self.assertEqual(len(self.capture.m_packet_history), 1)
        self.assertEqual(self.capture.m_packet_history[0].m_data, entry_data)

    def test_dump_to_file(self):
        """Test dumping F1PacketCapture to a file."""
        entry_data_1 = b'\x01\x02\x03\x04'
        entry_data_2 = b'\x05\x06\x07\x08'
        self.capture.add(entry_data_1)
        self.capture.add(entry_data_2)

        # Dump to file
        file_name, _, _ = self.dumpToFileHelper()

        # Ensure that the file has been created
        self.assertTrue(os.path.exists(file_name))

        # Read from the file and print the loaded entries
        loaded_capture = F1PacketCapture()
        loaded_capture.readFromFile(file_name)

        # Ensure that the number of loaded entries matches the expected count
        self.assertEqual(len(loaded_capture.m_packet_history), 2)
        self.assertEqual(len(loaded_capture.m_packet_history), loaded_capture.m_header.num_packets)

    def test_read_from_file(self):
        """Test reading from a file into F1PacketCapture."""
        entry_data = b'\x01\x02\x03\x04'
        self.capture.add(entry_data)

        # Dump to file
        file_name, _, _ = self.dumpToFileHelper()

        # Clear existing entries and read from the file
        self.capture.m_packet_history = []  # Clear existing entries
        self.capture.readFromFile(file_name)

        # Ensure that the entry has been read from the file
        self.assertEqual(len(self.capture.m_packet_history), 1)
        self.assertEqual(len(self.capture.m_packet_history), self.capture.m_header.num_packets)
        self.assertEqual(self.capture.m_packet_history[0].m_data, entry_data)

    def test_add_random_packets(self):
        """Test adding random packets to F1PacketCapture."""

        # Generate a random number of packets to add
        num_packets = random.randint(1, FullPCapTests.max_num_packets)

        for _ in range(num_packets):
            # Generate random data for the packet with a length up to max_packet_len
            packet_len = random.randint(1, FullPCapTests.max_packet_len)
            packet_data = bytes([random.randint(0, 255) for _ in range(packet_len)])

            # Add the packet to the capture object
            self.capture.add(packet_data)

            # Check if the added packet length is within the specified limit
            self.assertLessEqual(len(packet_data),FullPCapTests.max_packet_len)

        # Check if the number of added packets matches the expected number
        self.assertEqual(len(self.capture.m_packet_history), num_packets)
        self.assertEqual(self.capture.m_header.num_packets, num_packets)

    def test_random_packets_to_file_and_read(self):
        """Test generating random packets, writing to a file, and reading back."""

        # Generate a random number of packets to add
        num_packets = random.randint(1, FullPCapTests.max_num_packets)

        for i in range(num_packets):
            # Generate random data for the packet with a length up to max_packet_len
            packet_len = random.randint(1, FullPCapTests.max_packet_len)
            packet_data = bytes([random.randint(0, 255) for _ in range(packet_len)])

            # Add the packet to the capture object
            self.capture.add(packet_data)

            # Check if the added packet length is within the specified limit
            self.assertLessEqual(len(packet_data), FullPCapTests.max_packet_len)
            self.assertEqual(len(packet_data), packet_len)

        self.assertEqual(num_packets, len(self.capture.m_packet_history))
        self.assertEqual(num_packets, self.capture.m_header.num_packets)

        # Dump to file
        file_name, _, _ = self.dumpToFileHelper()

        # Ensure that the file has been created
        self.assertTrue(os.path.exists(file_name))

        # Create a new instance to read from the file
        loaded_capture = F1PacketCapture()
        loaded_capture.readFromFile(file_name)

        # Ensure that the number of loaded entries matches the expected count
        self.assertEqual(len(loaded_capture.m_packet_history), num_packets)
        self.assertEqual(loaded_capture.m_header.num_packets, num_packets)

    def tearDown(self):
        self.capture.m_packet_history = None
        for file_name in self.m_created_files:
            if os.path.exists(file_name):
                os.remove(file_name)

class TestF1PacketCaptureHeader(TestF1PacketCapture):
    def test_to_bytes_and_from_bytes(self):
        # Test serialization and deserialization
        header1 = F1PktCapFileHeader(major_version=3, minor_version=8, num_packets=1000, is_little_endian=True)
        header_bytes = header1.to_bytes()
        header2 = F1PktCapFileHeader.from_bytes(header_bytes)

        # Assert equality of the two headers
        self.assertEqual(header1.major_version, header2.major_version)
        self.assertEqual(header1.minor_version, header2.minor_version)
        self.assertEqual(header1.num_packets, header2.num_packets)
        self.assertEqual(header1.is_little_endian, header2.is_little_endian)

    def test_major_version_boundary(self):
        # Test major version boundary
        with self.assertRaises(ValueError):
            F1PktCapFileHeader(major_version=8)

    def test_minor_version_boundary(self):
        # Test minor version boundary
        with self.assertRaises(ValueError):
            F1PktCapFileHeader(minor_version=16)

# -------------------------------------------OVERTAKES-ANALYZER---------------------------------------------------------

class OvertakeAnalyzerUT(F1TelemetryUnitTestsBase):
    pass

class TestOvertakeAnalyzerFile(OvertakeAnalyzerUT):
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
        self.analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_FILE, self.temp_file.name)

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

class TestOvertakeAnalyzerList(TestOvertakeAnalyzerFile):

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
        self.analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_LIST, self.sample_data)

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
            analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_FILE, temp_file.name)

    def test_empty_list_input(self):
        # Initialize OvertakeAnalyzer with an empty list
        analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_LIST, [])

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
            analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_LIST, invalid_data)

    def test_invalid_data_handling_file(self):
        # Create a temporary CSV file with invalid data
        invalid_data = "1, HAMILTON, 1, RUSSELL\n2, LECLERC, 2\n3, PIASTRI, 3, NORRIS"

        # Write the invalid data to a temporary file
        temp_file = NamedTemporaryFile(mode='w', delete=False)
        temp_file.write(invalid_data)
        temp_file.close()

        # Initializing OvertakeAnalyzer with invalid CSV file should raise a ValueError
        with self.assertRaises(ValueError):
            analyzer = OvertakeAnalyzer(OvertakeAnalyzerMode.INPUT_MODE_FILE, temp_file.name)

        # Clean up the temporary file
        os.remove(temp_file.name)

# ----------------------------------------------------------------------------------------------------------------------

def runTests():
    unittest.main(testRunner=unittest.TextTestRunner(resultclass=CustomTestResult))

if __name__ == '__main__':
    if '--profile' in sys.argv:
        cProfile.run('runTests()', sort='cumulative')
    else:
        runTests()