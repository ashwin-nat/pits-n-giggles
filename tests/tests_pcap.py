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
import random
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.packet_cap import F1PacketCapture, F1PktCapFileHeader
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

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
