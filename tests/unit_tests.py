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
from src.telemetry_web_api import DriversListRsp
from lib.overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode, OvertakeRecord, OvertakeRivalryKey
from lib.race_analyzer import getFastestTimesJson

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

# ----------------------------------------------------------------------------------------------------------------------

class RaceAnalyzerUT(F1TelemetryUnitTestsBase):
    pass

class TestGetFastestTimesJson(RaceAnalyzerUT):

    def test_getFastestTimesJson(self):
        # Mock JSON data
        json_data = {
            "classification-data": [
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 2,
                        "best-sector-2-lap-num": 2,
                        "best-sector-3-lap-num": 3,
                        "lap-history-data": [
                            {"lap-time-in-ms": 90000, "sector-1-time-in-ms": 20000, "sector-2-time-in-ms": 30000, "sector-3-time-in-ms": 40000},
                            {"lap-time-in-ms": 88000, "sector-1-time-in-ms": 19000, "sector-2-time-in-ms": 29000, "sector-3-time-in-ms": 39000},
                            {"lap-time-in-ms": 87000, "sector-1-time-in-ms": 19500, "sector-2-time-in-ms": 30500, "sector-3-time-in-ms": 38000}
                        ]
                    },
                    "index": 0,
                    "driver-name" : "HAMILTON",
                    "participant-data" : {
                        "team-id" : "Mercedes"
                    }
                },
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 3,
                        "best-sector-2-lap-num": 2,
                        "best-sector-3-lap-num": 3,
                        "lap-history-data": [
                            {"lap-time-in-ms": 92000, "sector-1-time-in-ms": 21000, "sector-2-time-in-ms": 32000, "sector-3-time-in-ms": 39000},
                            {"lap-time-in-ms": 89000, "sector-1-time-in-ms": 20000, "sector-2-time-in-ms": 30000, "sector-3-time-in-ms": 39000},
                            {"lap-time-in-ms": 88000, "sector-1-time-in-ms": 19500, "sector-2-time-in-ms": 31000, "sector-3-time-in-ms": 37500}
                        ]
                    },
                    "index": 1,
                    "driver-name" : "VERSTAPPEN",
                    "participant-data" : {
                        "team-id" : "Red Bull"
                    }
                },
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 2,
                        "best-sector-2-lap-num": 2,
                        "best-sector-3-lap-num": 3,
                        "lap-history-data": [
                            {"lap-time-in-ms": 91000, "sector-1-time-in-ms": 19000, "sector-2-time-in-ms": 31000, "sector-3-time-in-ms": 41000},
                            {"lap-time-in-ms": 90000, "sector-1-time-in-ms": 18000, "sector-2-time-in-ms": 30000, "sector-3-time-in-ms": 42000},
                            {"lap-time-in-ms": 89000, "sector-1-time-in-ms": 19500, "sector-2-time-in-ms": 32000, "sector-3-time-in-ms": 37550}
                        ]
                    },
                    "index": 2,
                    "driver-name" : "LECLERC",
                    "participant-data" : {
                        "team-id" : "Ferrari"
                    }
                },
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 3,
                        "best-sector-2-lap-num": 3,
                        "best-sector-3-lap-num": 1,
                        "lap-history-data": [
                            {"lap-time-in-ms": 93000, "sector-1-time-in-ms": 20000, "sector-2-time-in-ms": 33000, "sector-3-time-in-ms": 40000},
                            {"lap-time-in-ms": 92000, "sector-1-time-in-ms": 19500, "sector-2-time-in-ms": 32000, "sector-3-time-in-ms": 40500},
                            {"lap-time-in-ms": 91000, "sector-1-time-in-ms": 19000, "sector-2-time-in-ms": 31000, "sector-3-time-in-ms": 41000}
                        ]
                    },
                    "index": 3,
                    "driver-name" : "NORRIS",
                    "participant-data" : {
                        "team-id" : "McLaren"
                    }
                },
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 2,
                        "best-sector-2-lap-num": 3,
                        "best-sector-3-lap-num": 1,
                        "lap-history-data": [
                            {"lap-time-in-ms": 94000, "sector-1-time-in-ms": 21000, "sector-2-time-in-ms": 33000, "sector-3-time-in-ms": 40000},
                            {"lap-time-in-ms": 93000, "sector-1-time-in-ms": 20000, "sector-2-time-in-ms": 32000, "sector-3-time-in-ms": 41000},
                            {"lap-time-in-ms": 92000, "sector-1-time-in-ms": 20500, "sector-2-time-in-ms": 31000, "sector-3-time-in-ms": 40500}
                        ]
                    },
                    "index": 4,
                    "driver-name" : "ALONSO",
                    "participant-data" : {
                        "team-id" : "Aston Martin"
                    }
                }
            ]
        }

        expected_result = {
            'lap': {
                'driver-index': 0,
                'driver-name' : 'HAMILTON',
                'team-id' : 'Mercedes',
                'lap-number': 3,
                'time': 87000,
                'time-str': '01:27.000'
            },
            's1': {
                'driver-index': 2,
                'driver-name' : 'LECLERC',
                'team-id' : 'Ferrari',
                'lap-number': 2,
                'time': 18000,
                'time-str': '18.000'
            },
            's2': {
                'driver-index': 0,
                'driver-name' : 'HAMILTON',
                'team-id' : 'Mercedes',
                'lap-number': 2,
                'time': 29000,
                'time-str': '29.000'
            },
            's3': {
                'driver-index': 1,
                'driver-name' : 'VERSTAPPEN',
                'team-id' : 'Red Bull',
                'lap-number': 3,
                'time': 37500,
                'time-str': '37.500'
            }
        }

        result = getFastestTimesJson(json_data)
        self.assertEqual(result, expected_result)

# ----------------------------------------------------------------------------------------------------------------------

def runTests():
    unittest.main(testRunner=unittest.TextTestRunner(resultclass=CustomTestResult))

if __name__ == '__main__':
    if '--profile' in sys.argv:
        cProfile.run('runTests()', sort='cumulative')
    else:
        runTests()