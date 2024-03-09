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

import struct
import time
from typing import Optional, List, Tuple, Generator
import sys

class F1PktCapFileHeader:
    """Represents the header of a file containing F1 UDP telemetry packets."""

    # Class attribute for the magic number
    MAGIC_NUMBER = b'F1UDP\0'

    # Use thist string to parse to and from the header
    HEADER_STRUCT_STR = '<6sBBI'
    HEADER_LEN = struct.calcsize(HEADER_STRUCT_STR)

    def __init__(self,
                major_version: int = 1,
                minor_version: int = 0,
                num_packets: int = 0,
                is_little_endian: bool = True):
        """
        Initialize an F1PktCapFileHeader.

        Parameters:
        - major_version (int): Major version number of the file format (default is 1).
        - minor_version (int): Minor version number of the file format (default is 0).
        - num_packets (int): Number of telemetry packets in the file.
        - is_little_endian (bool): If the actual file contents is in little endian
        """
        if major_version > 7: # Major version is only 3 bits
            raise ValueError("Major version is only 3 bits. Cannot go higher than 7")
        if minor_version > 15: # Minor version is only 4 bits
            raise ValueError("Minor version is only 4 bits. Cannot go higher than 15")
        self._major_version = major_version
        self._minor_version = minor_version
        self._num_packets = num_packets
        self._is_little_endian = is_little_endian

    @property
    def major_version(self) -> int:
        """Getter for major version."""
        return self._major_version

    @major_version.setter
    def major_version(self, value: int) -> None:
        """Setter for major version."""
        if value > 7: # Major version is only 3 bits
            raise ValueError("Major version is only 3 bits. Cannot go higher than 7")
        self._major_version = value

    @property
    def minor_version(self) -> int:
        """Getter for minor version."""
        return self._minor_version

    @minor_version.setter
    def minor_version(self, value: int) -> None:
        """Setter for minor version."""
        if value > 15: # Minor version is only 4 bits
            raise ValueError("Minor version is only 4 bits. Cannot go higher than 15")
        self._minor_version = value

    @property
    def is_little_endian(self) -> bool:
        """Getter for is_little_endian"""
        return self._is_little_endian

    @is_little_endian.setter
    def is_little_endian(self, value: bool) -> None:
        """Setter for is_little_endian"""
        self._is_little_endian = value

    @property
    def num_packets(self) -> int:
        """Getter for number of packets."""
        return self._num_packets

    @num_packets.setter
    def num_packets(self, value: int) -> None:
        """Setter for number of packets."""
        self._num_packets = value

    def getEndiannessStr(self) -> str:
        """_summary_

        Returns:
            _type_: _description_
        """
        return '<' if self._is_little_endian else '>'

    def to_bytes(self) -> bytes:
        """
        Convert the header to bytes for serialization.

        Returns:
        - bytes: Serialized bytes representation of the header.
        """

        # Most significant bit is endianness
        # Next 3 most significant bits is major version
        # 4 least significant bits is minor version
        reserved_byte = 0
        version_byte = 0
        version_byte += int(self._is_little_endian) << 7
        version_byte += (self._major_version << 4)
        version_byte += (self._minor_version)

        return struct.pack(F1PktCapFileHeader.HEADER_STRUCT_STR,
                F1PktCapFileHeader.MAGIC_NUMBER, # 6 bytes (including null terminator)
                reserved_byte, # 1 byte
                version_byte,  # 1 byte
                self._num_packets) # 4 bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> 'F1PktCapFileHeader':
        """
        Create an F1PktCapFileHeader from serialized bytes.

        Parameters:
        - data (bytes): Serialized bytes containing file header information.

        Returns:
        - F1PktCapFileHeader: Deserialized file header.
        """
        result = struct.unpack(F1PktCapFileHeader.HEADER_STRUCT_STR, data)
        (
            magic_number,
            reserved_byte,
            version_packed,
            num_packets
        ) = result

        is_little_endian = bool((version_packed >> 7) & 0x01)
        major_version = (version_packed >> 4) & 0x07
        minor_version = version_packed & 0x0F

        return F1PktCapFileHeader(
            major_version=major_version,
            minor_version=minor_version,
            num_packets=num_packets,
            is_little_endian=is_little_endian)

class F1PktCapMessage:
    """Represents an entry in the F1PacketCapture."""

    HEADER_LEN = 8

    def __init__(self, data: bytes, timestamp: float = None, is_little_endian: bool = True):
        """
        Initialize a F1PktCapMessage.

        Parameters:
        - data (bytes): Raw data for the entry.
        - timestamp (float) : The timestamp to be written, will be initialised with current time if not provid
        """
        self._m_data = data
        self.m_timestamp = timestamp if timestamp is not None else time.time()
        self.m_endianness_str = '<' if is_little_endian else '>'

    @property
    def m_data(self) -> bytes:
        """Getter for the raw data of the entry."""
        return self._m_data

    def to_bytes(self) -> bytes:
        """
        Convert the entry to bytes for serialization.

        Returns:
        - bytes: Serialized bytes representation of the entry.
        """
        timestamp_bytes = struct.pack(self.m_endianness_str + 'f', self.m_timestamp)
        data_length_bytes = struct.pack(self.m_endianness_str + 'I', len(self.m_data))
        return timestamp_bytes + data_length_bytes + self.m_data

    @classmethod
    def from_bytes(cls, data: bytes, is_little_endian: bool = True):
        """
        Create a F1PktCapMessage from serialized bytes.

        Parameters:
        - data (bytes): Serialized bytes containing timestamp and payload length followed by the payload.

        Returns:
        - F1PktCapMessage: Deserialized entry.

        Raises:
        - ValueError: If the length of the payload does not match the expected length specified in the header.
        """
        # Rest of the code remains the same
        endianness_str = '<' if is_little_endian else '>'
        timestamp, length = struct.unpack(endianness_str + 'fI', data[:8])
        payload = data[8:]
        if len(payload) != length:
            raise ValueError(f"Data length mismatch. Header length: {length}, Actual length: {len(payload)}")
        return F1PktCapMessage(payload, timestamp)

class F1PacketCapture:
    """Represents a collection of F1PktCapMessage objects."""

    major_ver = 1
    minor_ver = 0
    is_little_endian = (sys.byteorder == "little")
    file_extension = "f1pcap"

    def __init__(self, file_name:str=None):
        """Initialize a F1PacketCapture.

        Parmeters:
            file_name(str): If specified, will parse the given file into this container
        """
        self.m_packet_history: List[F1PktCapMessage] = []
        if file_name:
            self.readFromFile(file_name, append=False)
        else:
            self.m_header = F1PktCapFileHeader(self.major_ver, self.minor_ver, 0, self.is_little_endian)

    def clear(self):
        """
        Clear the packet history table
        """
        self.m_packet_history = []

    def add(self, data: bytes):
        """
        Add an entry to the packet history.

        Parameters:
        - data (bytes): Raw data for the entry.
        """
        entry = F1PktCapMessage(data, is_little_endian=self.is_little_endian)
        self.m_packet_history.append(entry)
        self.m_header.num_packets += 1

    def getNumPackets(self) -> int:
        """Get the number of packets in the list

        Returns:
            int: Number of packets in memory
        """

        return self.m_header.num_packets

    def dumpToFile(self, file_name: Optional[str] = None, append: bool = False) -> Tuple[str, int, int]:
        """
        Dump the packet history to a binary file.

        Parameters:
        - file_name (str, optional): Name of the file. If not provided, a timestamped filename will be generated.
        - append (bool): If True, append to an existing file; otherwise, create a new file.

        Returns:
        - str: The filename where the data is saved. None if nothing is written
        - int: The number of packets written. 0 if nothing is written
        - int: The number of bytes written. 0 if nothing is written
        """

        if len(self.m_packet_history) == 0:
            return None, 0, 0

        mode = "ab" if append else "wb"

        if file_name is None:
            timestamp_str = time.strftime("%Y%m%d%H%M%S", time.localtime())
            file_name = f"capture_{timestamp_str}." + self.file_extension

        byte_count = 0
        packet_count = len(self.m_packet_history)

        # Construct the header
        header = F1PktCapFileHeader(
            major_version=self.major_ver,
            minor_version=self.minor_ver,
            num_packets=packet_count,
            is_little_endian=self.is_little_endian)

        # Write to file
        with open(file_name, mode) as file:
            # First, write the header
            file.write(header.to_bytes())
            # Next write all packets
            for entry in self.m_packet_history:
                data_to_write = entry.to_bytes()
                file.write(data_to_write)
                byte_count += len(data_to_write)

        return file_name, packet_count, byte_count

    def readFromFile(self, file_name: str, append:bool = False) -> None:
        """
        Read packet entries from a binary file and populate the packet history.

        Parameters:
        - file_name (str): The name of the file to read from.
        - append (bool): If true, will append the file contents into the existing table
                            If false, will clear the table before reading the file
        """
        # Clear existing entries before reading from file if not in append mode

        if not append:
            self.m_packet_history.clear()

        with open(file_name, "rb") as file:
            # First, fetch the file header
            self.m_header = F1PktCapFileHeader.from_bytes(file.read(F1PktCapFileHeader.HEADER_LEN))
            endianness_str = self.m_header.getEndiannessStr()
            # Next process all the packets
            while True:
                entry_header_bytes = file.read(8)  # Assuming a fixed size for the header
                if not entry_header_bytes:
                    break

                timestamp_bytes = entry_header_bytes[:4]
                data_length_bytes = entry_header_bytes[4:]
                data_length = struct.unpack(endianness_str + 'I', data_length_bytes)[0]

                payload = file.read(data_length)

                # Concatenate timestamp_bytes, data_length_bytes, and payload
                entry_data = timestamp_bytes + data_length_bytes + payload

                # Use F1PktCapMessage.from_bytes to create the entry
                entry = F1PktCapMessage.from_bytes(entry_data, self.m_header.is_little_endian)
                self.m_packet_history.append(entry)

    def getPackets(self) -> Generator[Tuple[float, bytes], None, None]:
        """
        Generate packets from the packet history.

        Yields:
        - Tuple[float, bytes]: A tuple containing timestamp (float) and data (bytes) for each packet.
        """
        for entry in self.m_packet_history:
            yield entry.m_timestamp, entry.m_data

    def getFirstTimestamp(self) -> float:
        """Returns the timestamp of the first packet in the capture

        Returns:
            float: Timestamp
        """
        return self.m_packet_history[0].m_timestamp if len(self.m_packet_history) > 0 else None