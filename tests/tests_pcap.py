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
import random
import sys
import time
import tempfile

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.packet_cap import F1PacketCapture, F1PktCapFileHeader, F1PktCapMessage
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestF1PacketCapture(F1TelemetryUnitTestsBase):
    pass

class FullPCapTests(TestF1PacketCapture):
    # Configurable max_packet_len value
    max_packet_len = 1250
    max_num_packets = 5000

    def setUp(self):
        self.m_created_files = []

    def dumpToFileHelper(self, file_name=None, compressed=True):
        # self.capture = F1PacketCapture(compressed=compressed)
        file_name, packets_count, bytes_count = self.capture.dumpToFile(file_name)

        # Ensure file_name is not None
        if file_name:
            self.m_created_files.append(file_name)  # Keep track of created files
        else:
            raise ValueError("The file_name returned from dumpToFile is None")

        return file_name, packets_count, bytes_count

    def test_add_data(self):
        """Test adding data to F1PacketCapture."""
        for compressed in [True, False]:
            with self.subTest(compressed=compressed):
                self.capture = F1PacketCapture(compressed=compressed)
                entry_data = b'\x01\x02\x03\x04'
                self.capture.add(entry_data)

                # Ensure that the entry has been added to the packet history
                self.assertEqual(len(self.capture.m_packet_history), 1)
                self.assertEqual(self.capture.m_packet_history[0].m_data, entry_data)

    def test_dump_to_file(self):
        """Test dumping F1PacketCapture to a file."""
        for compressed in [True, False]:
            with self.subTest(compressed=compressed):
                self.capture = F1PacketCapture(compressed=compressed)
                entry_data_1 = b'\x01\x02\x03\x04'
                entry_data_2 = b'\x05\x06\x07\x08'
                self.capture.add(entry_data_1)
                self.capture.add(entry_data_2)

                # Dump to file
                file_name, _, _ = self.dumpToFileHelper(compressed=compressed)

                # Ensure that the file has been created
                self.assertTrue(os.path.exists(file_name))

                # Read from the file and print the loaded entries
                loaded_capture = F1PacketCapture(compressed=compressed)
                loaded_capture.readFromFile(file_name)

                # Ensure that the number of loaded entries matches the expected count
                self.assertEqual(len(loaded_capture.m_packet_history), 2)
                self.assertEqual(len(loaded_capture.m_packet_history), loaded_capture.m_header.num_packets)

    def test_read_from_file(self):
        """Test reading from a file into F1PacketCapture."""
        for compressed in [True, False]:
            with self.subTest(compressed=compressed):
                self.capture = F1PacketCapture(compressed=compressed)
                entry_data = b'\x01\x02\x03\x04'
                self.capture.add(entry_data)

                # Dump to file
                file_name, _, _ = self.dumpToFileHelper(compressed=compressed)

                # Clear existing entries and read from the file
                self.capture.m_packet_history = []  # Clear existing entries
                self.capture.readFromFile(file_name)

                # Ensure that the entry has been read from the file
                self.assertEqual(len(self.capture.m_packet_history), 1)
                self.assertEqual(len(self.capture.m_packet_history), self.capture.m_header.num_packets)
                self.assertEqual(self.capture.m_packet_history[0].m_data, entry_data)

    def test_add_random_packets(self):
        """Test adding random packets to F1PacketCapture."""
        for compressed in [True, False]:
            with self.subTest(compressed=compressed):
                self.capture = F1PacketCapture(compressed=compressed)

                # Generate a random number of packets to add
                num_packets = random.randint(1, FullPCapTests.max_num_packets)
                self._generate_add_random_packets(num_packets)

                # Check if the number of added packets matches the expected number
                self.assertEqual(len(self.capture.m_packet_history), num_packets)
                self.assertEqual(self.capture.m_header.num_packets, num_packets)

    def test_random_packets_to_file_and_read(self):
        """Test generating random packets, writing to a file, and reading back."""
        for compressed in [True, False]:
            with self.subTest(compressed=compressed):
                self.capture = F1PacketCapture(compressed=compressed)

                # Generate a random number of packets to add
                num_packets = random.randint(1, FullPCapTests.max_num_packets)
                self._generate_add_random_packets(num_packets)

                self.assertEqual(num_packets, len(self.capture.m_packet_history))
                self.assertEqual(num_packets, self.capture.m_header.num_packets)

                # Dump to file
                file_name, _, _ = self.dumpToFileHelper(compressed=compressed)

                # Ensure that the file has been created
                self.assertTrue(os.path.exists(file_name))

                # Create a new instance to read from the file
                loaded_capture = F1PacketCapture(compressed=compressed)
                loaded_capture.readFromFile(file_name)

                # Ensure that the number of loaded entries matches the expected count
                self.assertEqual(len(loaded_capture.m_packet_history), num_packets)
                self.assertEqual(loaded_capture.m_header.num_packets, num_packets)

    def test_clear_and_reload_with_random_packets(self):
        """Test generating random packets, writing to a file, and reading back."""
        for compressed in [True, False]:
            with self.subTest(compressed=compressed):
                self.capture = F1PacketCapture(compressed=compressed)

                # Generate a random number of packets to add
                num_packets = random.randint(1, FullPCapTests.max_num_packets)
                self._generate_add_random_packets(num_packets)

                self.assertEqual(num_packets, len(self.capture.m_packet_history))
                self.assertEqual(num_packets, self.capture.m_header.num_packets)

                # Clear the object, then continue with the test
                self.capture.clear()

                # Generate a random number of packets to add
                num_packets = random.randint(1, FullPCapTests.max_num_packets)
                self._generate_add_random_packets(num_packets)

                # Dump to file
                file_name, _, _ = self.dumpToFileHelper(compressed=compressed)

                # Ensure that the file has been created
                self.assertTrue(os.path.exists(file_name))

                # Create a new instance to read from the file
                loaded_capture = F1PacketCapture(compressed=compressed)
                loaded_capture.readFromFile(file_name)

                # Ensure that the number of loaded entries matches the expected count
                self.assertEqual(len(loaded_capture.m_packet_history), num_packets)
                self.assertEqual(loaded_capture.m_header.num_packets, num_packets)

    def tearDown(self):
        self.capture.m_packet_history = None
        for file_name in self.m_created_files:
            if file_name and os.path.exists(file_name):
                os.remove(file_name)

    def _generate_add_random_packets(self, num_packets: int) -> None:
        """Generate and add random packets to the capture object.

        Args:
            num_packets (int): The number of packets to generate and add.
        """

        for _ in range(num_packets):
            # Generate random data for the packet with a length up to max_packet_len
            packet_len = random.randint(1, FullPCapTests.max_packet_len)
            packet_data = bytes([random.randint(0, 255) for _ in range(packet_len)])

            # Add the packet to the capture object
            self.capture.add(packet_data)

            # Check if the added packet length is within the specified limit
            self.assertLessEqual(len(packet_data), FullPCapTests.max_packet_len)
            self.assertEqual(len(packet_data), packet_len)

class TestF1PacketCaptureHeader(TestF1PacketCapture):
    def test_to_bytes_and_from_bytes(self):
        # Test serialization and deserialization
        header1 = F1PktCapFileHeader(
            major_version=3,
            minor_version=8,
            num_packets=1000,
            is_little_endian=True,
            is_compressed=False
        )
        header_bytes = header1.to_bytes()
        header2 = F1PktCapFileHeader.from_bytes(header_bytes)

        # Assert equality of the two headers
        self.assertEqual(header1.major_version, header2.major_version)
        self.assertEqual(header1.minor_version, header2.minor_version)
        self.assertEqual(header1.num_packets, header2.num_packets)
        self.assertEqual(header1.is_little_endian, header2.is_little_endian)
        self.assertEqual(header1.is_compressed, header2.is_compressed)

    def test_major_version_boundary(self):
        # Test major version boundary
        with self.assertRaises(ValueError):
            F1PktCapFileHeader(major_version=8)

    def test_minor_version_boundary(self):
        # Test minor version boundary
        with self.assertRaises(ValueError):
            F1PktCapFileHeader(minor_version=16)

class TestF1PacketCaptureCompression(TestF1PacketCapture):
    def setUp(self):
        # Create some sample packet data for testing
        self.test_packets = [
            b'This is test packet 1',
            b'This is a longer test packet with more data to compress',
            b'\x00\x01\x02\x03\x04\x05', # Binary data
            b'Short',
            b'A' * 1000  # Large packet to test compression
        ]
        self.test_timestamps = [
            time.time(),
            time.time() + 0.1,
            time.time() + 0.2,
            time.time() + 0.3,
            time.time() + 0.4
        ]

    def test_uncompressed_to_compressed_conversion(self):
        """Test converting from uncompressed to compressed format"""
        # Create an uncompressed capture
        uncompressed_capture = F1PacketCapture(compressed=False)

        # Add test packets
        for packet in self.test_packets:
            uncompressed_capture.add(packet)

        # Write uncompressed file
        temp_dir = tempfile.gettempdir()
        uncompressed_filename = os.path.join(temp_dir, "uncompressed_test.f1pcap")
        uncompressed_capture.dumpToFile(uncompressed_filename)

        # Create new capture from the uncompressed file
        loaded_uncompressed = F1PacketCapture(file_name=uncompressed_filename)

        # Convert to compressed
        compressed_filename = os.path.join(temp_dir, "compressed_test.f1pcap")
        compressed_capture = F1PacketCapture(compressed=True)

        # Copy packets from uncompressed to compressed
        for timestamp, data in loaded_uncompressed.getPackets():
            entry = F1PktCapMessage(data, timestamp, is_little_endian=compressed_capture.is_little_endian)
            compressed_capture.m_packet_history.append(entry)
            compressed_capture.m_header.num_packets += 1

        # Write compressed file
        compressed_capture.dumpToFile(compressed_filename)

        # Load the compressed file
        loaded_compressed = F1PacketCapture(file_name=compressed_filename)

        # Verify packets match
        self.assertEqual(loaded_uncompressed.getNumPackets(), loaded_compressed.getNumPackets())

        # Compare packets
        uncompressed_packets = list(loaded_uncompressed.getPackets())
        compressed_packets = list(loaded_compressed.getPackets())

        for i in range(len(uncompressed_packets)):
            # Compare timestamps (with small float tolerance)
            self.assertAlmostEqual(uncompressed_packets[i][0], compressed_packets[i][0], places=6)
            # Compare data
            self.assertEqual(uncompressed_packets[i][1], compressed_packets[i][1])

        # Clean up
        os.remove(uncompressed_filename)
        os.remove(compressed_filename)

    def test_conversion_helper_method(self):
        """Test a helper method to convert between formats"""
        # Create uncompressed capture with test data
        uncompressed_capture = F1PacketCapture(compressed=False)
        for i, packet in enumerate(self.test_packets):
            entry = F1PktCapMessage(packet, self.test_timestamps[i], is_little_endian=uncompressed_capture.is_little_endian)
            uncompressed_capture.m_packet_history.append(entry)
            uncompressed_capture.m_header.num_packets += 1

        # Convert to compressed format using a helper method
        def convert_capture_format(source_capture, target_compressed):
            """Helper method to convert between compressed/uncompressed formats"""
            temp_dir = tempfile.gettempdir()
            temp_filename = os.path.join(temp_dir, f"temp_conversion_{int(time.time())}.f1pcap")

            # Write source to file
            source_capture.dumpToFile(temp_filename)

            # Create new capture with target compression setting
            converted = F1PacketCapture(compressed=target_compressed)

            # Load packets from source
            source_packets = list(source_capture.getPackets())

            # Add packets to new capture
            for timestamp, data in source_packets:
                entry = F1PktCapMessage(data, timestamp, is_little_endian=converted.is_little_endian)
                converted.m_packet_history.append(entry)
                converted.m_header.num_packets += 1

            # Clean up temp file
            os.remove(temp_filename)

            return converted

        # Convert uncompressed to compressed
        compressed_capture = convert_capture_format(uncompressed_capture, True)

        # Verify conversion
        self.assertTrue(compressed_capture.is_compressed)
        self.assertEqual(uncompressed_capture.getNumPackets(), compressed_capture.getNumPackets())

        # Compare packets
        uncompressed_packets = list(uncompressed_capture.getPackets())
        compressed_packets = list(compressed_capture.getPackets())

        for i in range(len(uncompressed_packets)):
            # Compare timestamps
            self.assertAlmostEqual(uncompressed_packets[i][0], compressed_packets[i][0], places=3)
            # Compare data
            self.assertEqual(uncompressed_packets[i][1], compressed_packets[i][1])

        # Now convert back to uncompressed
        back_to_uncompressed = convert_capture_format(compressed_capture, False)

        # Verify conversion back
        self.assertFalse(back_to_uncompressed.is_compressed)
        self.assertEqual(compressed_capture.getNumPackets(), back_to_uncompressed.getNumPackets())

        # Compare packets again
        back_packets = list(back_to_uncompressed.getPackets())

        for i in range(len(compressed_packets)):
            # Compare timestamps
            self.assertEqual(compressed_packets[i][0], back_packets[i][0])
            # Compare data
            self.assertEqual(compressed_packets[i][1], back_packets[i][1])

    def test_direct_conversion_method(self):
        """Test a direct method to convert a file between compressed/uncompressed"""
        # Create and implement a convert_file function
        def convert_file(input_filename, output_filename, target_compressed):
            """Convert a capture file between compressed/uncompressed formats"""
            # Load source file
            source_capture = F1PacketCapture(file_name=input_filename)

            # Create target capture with desired compression
            target_capture = F1PacketCapture(compressed=target_compressed)

            # Copy all packets
            for timestamp, data in source_capture.getPackets():
                entry = F1PktCapMessage(data, timestamp, is_little_endian=target_capture.is_little_endian)
                target_capture.m_packet_history.append(entry)
                target_capture.m_header.num_packets += 1

            # Write to target file
            target_capture.dumpToFile(output_filename)

            return target_capture.getNumPackets()

        # Create test capture file
        uncompressed_capture = F1PacketCapture(compressed=False)
        for packet in self.test_packets:
            uncompressed_capture.add(packet)

        # Save to temp file
        temp_dir = tempfile.gettempdir()
        uncompressed_filename = os.path.join(temp_dir, "unconverted.f1pcap")
        compressed_filename = os.path.join(temp_dir, "converted.f1pcap")

        uncompressed_capture.dumpToFile(uncompressed_filename)

        # Convert to compressed
        packets_converted = convert_file(uncompressed_filename, compressed_filename, True)

        # Verify conversion
        self.assertEqual(uncompressed_capture.getNumPackets(), packets_converted)

        # Load converted file and check
        compressed_capture = F1PacketCapture(file_name=compressed_filename)

        # Verify compression flag is set
        self.assertTrue(compressed_capture.m_header.is_compressed)

        # Compare packets
        uncompressed_packets = list(uncompressed_capture.getPackets())
        compressed_packets = list(compressed_capture.getPackets())

        for i in range(len(uncompressed_packets)):
            # Compare data (timestamps may have floating point differences due to serialization)
            self.assertEqual(uncompressed_packets[i][1], compressed_packets[i][1])

        # Clean up
        os.remove(uncompressed_filename)
        os.remove(compressed_filename)