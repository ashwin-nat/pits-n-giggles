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
import sys
import time
import zlib
from abc import ABC, abstractmethod
from typing import Any, Callable, Generator, List, Optional, Tuple


class CompressionHelper(ABC):
    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        pass

    @property
    @abstractmethod
    def is_compressed(self) -> bool:
        pass

class NoCompressionHelper(CompressionHelper):
    def decompress(self, data: bytes) -> bytes:
        return data

    def compress(self, data: bytes) -> bytes:
        return data

    @property
    def is_compressed(self) -> bool:
        return False

class ZlibCompressionHelper(CompressionHelper):
    def decompress(self, data: bytes) -> bytes:
        try:
            return zlib.decompress(data)
        except zlib.error as e:
            raise ValueError(f"Zlib decompression failed: {e}") from e

    def compress(self, data: bytes) -> bytes:
        return zlib.compress(data)

    @property
    def is_compressed(self) -> bool:
        return True

class F1PktCapFileHeader:
    """Represents the header of a file containing F1 UDP telemetry packets.
    Offset | Size | Description
    -------+------+----------------------------------------
     0     | 6    | Magic Number ("F1UDP\0")
     6     | 1    | Flags byte (bit 0: compression flag)
     7     | 1    | Version byte:
           |      |   bit 7: Endianness (1=little, 0=big)
           |      |   bits 6-4: Major version (3 bits, max 7)
           |      |   bits 3-0: Minor version (4 bits, max 15)
     8     | 4    | Number of packets (uint32)
     12    | Total header length
    """

    # Class attribute for the magic number
    MAGIC_NUMBER = b'F1UDP\0'

    HEADER_STRUCT_STR = '<6sBBI'
    HEADER_LEN = struct.calcsize(HEADER_STRUCT_STR)

    def __init__(self,
                major_version: int = 1,
                minor_version: int = 0,
                num_packets: int = 0,
                is_little_endian: bool = True,
                is_compressed: bool = True):
        """
        Initialize an F1PktCapFileHeader.

        Parameters:
        - major_version (int): Major version number of the file format (default is 1).
        - minor_version (int): Minor version number of the file format (default is 0).
        - num_packets (int): Number of telemetry packets in the file.
        - is_little_endian (bool): If the actual file contents is in little endian
        - is_compressed (bool): If each packet is compressed
        """
        if major_version > 7: # Major version is only 3 bits
            raise ValueError("Major version is only 3 bits. Cannot go higher than 7")
        if minor_version > 15: # Minor version is only 4 bits
            raise ValueError("Minor version is only 4 bits. Cannot go higher than 15")
        self._major_version = major_version
        self._minor_version = minor_version
        self._num_packets = num_packets
        self._is_little_endian = is_little_endian
        self._is_compressed = is_compressed

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

    @property
    def is_compressed(self) -> bool:
        """Getter for compressed."""
        return self._is_compressed

    def getEndiannessStr(self) -> str:
        """Get the endianness as a string for struct library.

        Returns:
        - str: '<' for little endian, '>' for big endian
        """
        return '<' if self._is_little_endian else '>'

    def get_flags(self) -> int:
        """Get the flags as an integer."""

        # Currently, only the compressed flag is supported
        # This is the 0th/least significant bit
        return int(self._is_compressed)

    def to_bytes(self) -> bytes:
        """
        Convert the header to bytes for serialization.

        Returns:
        - bytes: Serialized bytes representation of the header.
        """

        # Most significant bit is endianness
        # Next 3 most significant bits is major version
        # 4 least significant bits is minor version
        flags_byte      = self.get_flags() # 0th bit indicates
        version_byte    = 0
        version_byte    += int(self._is_little_endian) << 7
        version_byte    += (self._major_version << 4)
        version_byte    += (self._minor_version)

        return struct.pack(F1PktCapFileHeader.HEADER_STRUCT_STR,
                F1PktCapFileHeader.MAGIC_NUMBER, # 6 bytes (including null terminator)
                flags_byte, # 1 byte
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
            _, # magic_number,
            flags_byte,
            version_packed,
            num_packets
        ) = result

        is_compressed = bool(flags_byte & 0x01)
        is_little_endian = bool((version_packed >> 7) & 0x01)
        major_version = (version_packed >> 4) & 0x07
        minor_version = version_packed & 0x0F

        return F1PktCapFileHeader(
            major_version=major_version,
            minor_version=minor_version,
            num_packets=num_packets,
            is_little_endian=is_little_endian,
            is_compressed=is_compressed)

class F1PktCapMessage:
    """Represents an entry in the F1PacketCapture."""

    HEADER_LEN = 8

    # Offset | Size | Description
    # -------+------+----------------------------------------
    #  0     | 4    | Timestamp (float)
    #  4     | 4    | Data length (uint32)
    #  8     | N    | Packet data (raw or compressed)

    def __init__(self, data: bytes, timestamp: float = None, is_little_endian: bool = True):
        """
        Initialize a F1PktCapMessage.

        Parameters:
        - data (bytes): Raw data for the entry.
        - timestamp (float) : The timestamp to be written, will be initialised with current time if not provid
        - is_little_endian (bool): Endianness of the data.
        """
        self._m_data = data
        self.m_timestamp = timestamp if timestamp is not None else time.time()
        self.m_endianness_str = '<' if is_little_endian else '>'

    @property
    def m_data(self) -> bytes:
        """Getter for the raw data of the entry."""
        return self._m_data

    def to_bytes(self, compression_helper: CompressionHelper) -> bytes:
        """
        Convert the entry to bytes for serialization.

        Parameters:
        - compression_helper (CompressionHelper): Compression helper object for compression.

        Returns:
        - bytes: Serialized bytes representation of the entry.
        """
        timestamp_bytes = struct.pack(f'{self.m_endianness_str}f', self.m_timestamp)
        compressed_data = compression_helper.compress(self.m_data)
        data_length_bytes = struct.pack(f'{self.m_endianness_str}I', len(compressed_data))
        return timestamp_bytes + data_length_bytes + compressed_data

    @classmethod
    def from_bytes(cls, data: bytes, is_little_endian: bool, compression_helper: CompressionHelper):
        """
        Create a F1PktCapMessage from serialized bytes.

        Parameters:
        - data (bytes): Serialized bytes containing timestamp and payload length followed by the payload.
        - is_little_endian (bool): Whether the data is in little endian format.
        - compression_helper (CompressionHelper): Compression helper object for decompression.

        Returns:
        - F1PktCapMessage: Deserialized entry.

        Raises:
        - ValueError: If the length of the payload does not match the expected length specified in the header.
        """
        # Rest of the code remains the same
        endianness_str = '<' if is_little_endian else '>'
        timestamp, length = struct.unpack(f'{endianness_str}fI', data[:8])
        compressed_payload = data[8:]
        payload = compression_helper.decompress(compressed_payload)
        if len(compressed_payload) != length:
            raise ValueError(f"Data length mismatch. Header length: {length}, Actual length: {len(payload)}")
        return F1PktCapMessage(payload, timestamp)

class F1PacketCapture:
    """Represents a collection of F1PktCapMessage objects."""

    major_ver = 1
    minor_ver = 1
    is_little_endian = (sys.byteorder == "little")
    file_extension = "f1pcap"

    def __init__(self, compressed:Optional[bool]=None, file_name:Optional[str]=None):
        """Initialize a F1PacketCapture.

        Parmeters:
            compressed(bool): If true, will use compression
            file_name(str): If specified, will parse the given file into this container
        """
        if compressed is not None and file_name is not None:
            raise ValueError("Cannot specify both compressed and file_name")
        if compressed is None and file_name is None:
            raise ValueError("Must specify either compressed or file_name")

        self.m_packet_history: List[F1PktCapMessage] = []
        self.is_compressed = compressed

        if file_name:
            self.readFromFile(file_name)
        else:
            self.m_header = F1PktCapFileHeader(
                major_version=self.major_ver,
                minor_version=self.minor_ver,
                num_packets=0,
                is_little_endian=self.is_little_endian,
                is_compressed=compressed)
            if compressed:
                self.m_compression_helper: CompressionHelper = ZlibCompressionHelper()
            else:
                self.m_compression_helper: CompressionHelper = NoCompressionHelper()

    def set_compressed(self, compressed: bool):
        """Set the compression state and update the compression helper accordingly."""
        self.is_compressed = compressed
        if compressed:
            self.m_compression_helper = ZlibCompressionHelper()
        else:
            self.m_compression_helper = NoCompressionHelper()

    def add(self, data: bytes, timestamp: float = None):
        """
        Add an entry to the packet history.

        Parameters:
        - data (bytes): Raw data for the entry.
        - timestamp (float): The timestamp to be written, will be initialised with current time if not provided
        """
        entry = F1PktCapMessage(data, timestamp=timestamp, is_little_endian=self.is_little_endian)
        self.m_packet_history.append(entry)
        self.m_header.num_packets = len(self.m_packet_history)

    def getNumPackets(self) -> int:
        """Get the number of packets in the list

        Returns:
            int: Number of packets in memory
        """

        return self.m_header.num_packets

    def dumpToFile(self,
        file_name: Optional[str] = None,
        progress_update_callback: Optional[Callable] = None,
        progress_update_callback_arg: Optional[Any] = None) -> Tuple[str, int, int]:
        """
        Dump the packet history to a binary file.

        Arguments:
            - file_name (str, optional): Name of the file. If not provided, a timestamped filename will be generated.
            - progress_update_callback (Callable): If not None, will be called with two args (both int)
                    - The current packet count
                    - The total number of packets
                    - The optional argument passed in
            - progress_update_callback_arg (Any): Optional argument passed to the progress_update_callback

        Returns:
            - str: The filename where the data is saved. None if nothing is written
            - int: The number of packets written. 0 if nothing is written
            - int: The number of bytes written. 0 if nothing is written
        """

        if len(self.m_packet_history) == 0:
            return None, 0, 0

        if file_name is None:
            timestamp_str = time.strftime("%Y%m%d%H%M%S", time.localtime())
            file_name = f"capture_{timestamp_str}.{self.file_extension}"

        byte_count = 0
        total_packet_count = len(self.m_packet_history)

        # Construct the header
        header = F1PktCapFileHeader(
            major_version=self.major_ver,
            minor_version=self.minor_ver,
            num_packets=total_packet_count,
            is_little_endian=self.is_little_endian,
            is_compressed=self.is_compressed)

        # Write to file
        with open(file_name, "wb") as file:
            # First, write the header
            file.write(header.to_bytes())
            # Next write all packets
            for curr_packet_count, entry in enumerate(self.m_packet_history):
                data_to_write = entry.to_bytes(self.m_compression_helper)
                file.write(data_to_write)
                byte_count += len(data_to_write)
                if progress_update_callback:
                    if progress_update_callback_arg:
                        progress_update_callback(curr_packet_count, total_packet_count, progress_update_callback_arg)
                    else:
                        progress_update_callback(curr_packet_count, total_packet_count)

        return file_name, total_packet_count, byte_count

    def readFromFile(self, file_name: str) -> None:
        """
        Read packet entries from a binary file and populate the packet history.

        Parameters:
            - file_name (str): The name of the file to read from.

        Raises:
            - ValueError: If the number of packets mentioned in the file does not match
                the number of packets in the file body
        """

        with open(file_name, "rb") as file:
            # First, fetch the file header
            self.m_header = F1PktCapFileHeader.from_bytes(file.read(F1PktCapFileHeader.HEADER_LEN))
            endianness_str = self.m_header.getEndiannessStr()
            if self.m_header.is_compressed:
                self.m_compression_helper = ZlibCompressionHelper()
            else:
                self.m_compression_helper = NoCompressionHelper()

            # Next process all the packets
            while True:
                entry_header_bytes = file.read(8)  # Assuming a fixed size for the header
                if not entry_header_bytes:
                    break

                timestamp_bytes = entry_header_bytes[:4]
                data_length_bytes = entry_header_bytes[4:]
                data_length = struct.unpack(f'{endianness_str}I', data_length_bytes)[0]

                payload = file.read(data_length)

                # Concatenate timestamp_bytes, data_length_bytes, and payload
                entry_data = timestamp_bytes + data_length_bytes + payload

                # Use F1PktCapMessage.from_bytes to create the entry
                entry = F1PktCapMessage.from_bytes(
                    entry_data,
                    self.m_header.is_little_endian,
                    self.m_compression_helper
                )
                self.m_packet_history.append(entry)

        if self.m_header.num_packets != len(self.m_packet_history):
            print(f"[WARN]: Number of packets in the file {self.m_header.num_packets} does not match the header "
                             f"{len(self.m_packet_history)}. Possibly corrupt file", file=sys.stderr)

    def getPackets(self) -> Generator[Tuple[float, bytes], None, None]:
        """
        Generate packets from the packet history.

        Yields:
        - Tuple[float, bytes]: A tuple containing timestamp (float) and data (bytes) for each packet.
        """
        yield from ((entry.m_timestamp, entry.m_data) for entry in self.m_packet_history)

    def getFirstTimestamp(self) -> float:
        """Returns the timestamp of the first packet in the capture

        Returns:
            float: Timestamp
        """
        return self.m_packet_history[0].m_timestamp if len(self.m_packet_history) > 0 else None

    def clear(self) -> None:
        """
       Clear the packet history table and reset the number of packets.
        """

        self.m_packet_history.clear()
        self.m_header.num_packets = 0
