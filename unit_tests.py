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
from telemetry_data import _get_adjacent_positions
from packet_cap import F1PacketCapture, F1PacketCaptureEntry
from colorama import Fore, Style
import random
import cProfile
import sys

# Initialize colorama
from colorama import init
init(autoreset=True)

class CustomTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        test_class_name = test.__class__.__name__
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

class TestAdjacentPositions(unittest.TestCase):

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

class TestF1PacketCapture(unittest.TestCase):

    # Configurable max_packet_len value
    max_packet_len = 1250
    max_num_packets = 3

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
        self.assertEqual(self.capture.m_packet_history[0].m_data, entry_data)

    def test_add_random_packets(self):
        """Test adding random packets to F1PacketCapture."""

        # Generate a random number of packets to add
        num_packets = random.randint(1, TestF1PacketCapture.max_num_packets)
        print("num_packets = " + str(num_packets))

        for _ in range(num_packets):
            # Generate random data for the packet with a length up to max_packet_len
            packet_len = random.randint(1, TestF1PacketCapture.max_packet_len)
            packet_data = bytes([random.randint(0, 255) for _ in range(packet_len)])

            # Add the packet to the capture object
            self.capture.add(packet_data)

            # Check if the added packet length is within the specified limit
            self.assertLessEqual(len(packet_data),TestF1PacketCapture.max_packet_len)

        # Check if the number of added packets matches the expected number
        self.assertEqual(len(self.capture.m_packet_history), num_packets)

    def test_random_packets_to_file_and_read(self):
        """Test generating random packets, writing to a file, and reading back."""
        # Configurable max_packet_len value
        max_packet_len = 50

        # Generate a random number of packets to add
        num_packets = random.randint(1, TestF1PacketCapture.max_num_packets)
        print("num_packets = " + str(num_packets))

        for i in range(num_packets):
            # Generate random data for the packet with a length up to max_packet_len
            packet_len = random.randint(1, max_packet_len)
            packet_data = bytes([random.randint(0, 255) for _ in range(packet_len)])

            # Add the packet to the capture object
            self.capture.add(packet_data)

            # Check if the added packet length is within the specified limit
            self.assertLessEqual(len(packet_data), max_packet_len)
            self.assertEqual(len(packet_data), packet_len)

        self.assertEqual(num_packets, len(self.capture.m_packet_history))

        # Dump to file
        file_name, _, num_bytes = self.dumpToFileHelper()
        print("num_bytes_written = " + str(num_bytes))

        # Ensure that the file has been created
        self.assertTrue(os.path.exists(file_name))

        # Create a new instance to read from the file
        loaded_capture = F1PacketCapture()
        loaded_capture.readFromFile(file_name)

        # Ensure that the number of loaded entries matches the expected count
        self.assertEqual(len(loaded_capture.m_packet_history), num_packets)

    def tearDown(self):
        self.capture.m_packet_history = None
        for file_name in self.m_created_files:
            if os.path.exists(file_name):
                os.remove(file_name)


    def shortDescription(self):
        return self._testMethodName

def runTests():
    unittest.main(testRunner=unittest.TextTestRunner(resultclass=CustomTestResult))

if __name__ == '__main__':
    if '--profile' in sys.argv:
        cProfile.run('runTests()', sort='cumulative')
    else:
        runTests()