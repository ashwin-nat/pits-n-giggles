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

import lzma
import struct
import sys
import time
import zlib
from abc import ABC, abstractmethod
from enum import IntEnum
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

class CompressionMode(IntEnum):
    """Compression scheme of a capture file, stored in the low 4 bits of the header flags byte."""
    NONE = 0
    PER_PACKET_ZLIB = 1
    GLOBAL_LZMA = 2

class F1PktCapFileHeader:
    """Represents the header of a file containing F1 UDP telemetry packets.
    Offset | Size | Description
    -------+------+----------------------------------------
     0     | 6    | Magic Number ("F1UDP\0")
     6     | 1    | Flags byte (bits 3-0: CompressionMode, bits 7-4: reserved)
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

    # Highest major version this reader understands
    SUPPORTED_MAJOR_VERSION = 1

    COMPRESSION_MODE_MASK = 0x0F

    # First minor version whose packet timestamps are float64. Earlier files use float32,
    # which cannot resolve better than ~128 s at epoch magnitudes.
    FLOAT64_TIMESTAMP_MINOR_VERSION = 2

    def __init__(self,
                major_version: int = 1,
                minor_version: int = 0,
                num_packets: int = 0,
                is_little_endian: bool = True,
                is_compressed: bool = True,
                compression_mode: Optional[CompressionMode] = None):
        """
        Initialize an F1PktCapFileHeader.

        Parameters:
        - major_version (int): Major version number of the file format (default is 1).
        - minor_version (int): Minor version number of the file format (default is 0).
        - num_packets (int): Number of telemetry packets in the file.
        - is_little_endian (bool): If the actual file contents is in little endian
        - is_compressed (bool): If each packet is compressed. Ignored if compression_mode is given
        - compression_mode (CompressionMode): Compression scheme of the file body
        """
        if major_version > 7: # Major version is only 3 bits
            raise ValueError("Major version is only 3 bits. Cannot go higher than 7")
        if minor_version > 15: # Minor version is only 4 bits
            raise ValueError("Minor version is only 4 bits. Cannot go higher than 15")
        self._major_version = major_version
        self._minor_version = minor_version
        self._num_packets = num_packets
        self._is_little_endian = is_little_endian
        if compression_mode is None:
            compression_mode = CompressionMode.PER_PACKET_ZLIB if is_compressed else CompressionMode.NONE
        self._compression_mode = compression_mode

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
    def compression_mode(self) -> CompressionMode:
        """Getter for the compression mode."""
        return self._compression_mode

    @property
    def is_compressed(self) -> bool:
        """Getter for compressed."""
        return self._compression_mode != CompressionMode.NONE

    @property
    def timestamp_format(self) -> str:
        """struct format character of the per-packet timestamp: 'd' (float64) or 'f' (legacy float32)."""
        if self._minor_version >= F1PktCapFileHeader.FLOAT64_TIMESTAMP_MINOR_VERSION:
            return 'd'
        return 'f'

    def getEndiannessStr(self) -> str:
        """Get the endianness as a string for struct library.

        Returns:
        - str: '<' for little endian, '>' for big endian
        """
        return '<' if self._is_little_endian else '>'

    def get_flags(self) -> int:
        """Get the flags as an integer."""

        # Low 4 bits: compression mode. High 4 bits are reserved
        return int(self._compression_mode)

    def to_bytes(self) -> bytes:
        """
        Convert the header to bytes for serialization.

        Returns:
        - bytes: Serialized bytes representation of the header.
        """

        # Most significant bit is endianness
        # Next 3 most significant bits is major version
        # 4 least significant bits is minor version
        flags_byte      = self.get_flags()
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

        Raises:
        - ValueError: If the header is truncated, the magic number is wrong, the major version is
            newer than supported, or the compression mode is unknown
        """
        if len(data) != F1PktCapFileHeader.HEADER_LEN:
            raise ValueError(f"Truncated file header. Expected {F1PktCapFileHeader.HEADER_LEN} bytes, "
                             f"got {len(data)}")
        result = struct.unpack(F1PktCapFileHeader.HEADER_STRUCT_STR, data)
        (
            magic_number,
            flags_byte,
            version_packed,
            num_packets
        ) = result

        if magic_number != F1PktCapFileHeader.MAGIC_NUMBER:
            raise ValueError(f"Not an f1pcap file. Bad magic number: {magic_number!r}")

        is_little_endian = bool((version_packed >> 7) & 0x01)
        major_version = (version_packed >> 4) & 0x07
        minor_version = version_packed & 0x0F
        if major_version > F1PktCapFileHeader.SUPPORTED_MAJOR_VERSION:
            raise ValueError(f"Unsupported f1pcap major version {major_version}. "
                             f"Highest supported is {F1PktCapFileHeader.SUPPORTED_MAJOR_VERSION}")

        mode_value = flags_byte & F1PktCapFileHeader.COMPRESSION_MODE_MASK
        try:
            compression_mode = CompressionMode(mode_value)
        except ValueError as e:
            raise ValueError(f"Unknown f1pcap compression mode {mode_value}") from e

        return F1PktCapFileHeader(
            major_version=major_version,
            minor_version=minor_version,
            num_packets=num_packets,
            is_little_endian=is_little_endian,
            compression_mode=compression_mode)

class F1PktCapMessage:
    """Represents an entry in the F1PacketCapture."""

    # Offset | Size | Description
    # -------+------+----------------------------------------
    #  0     | 8    | Timestamp (float64; float32 in files below minor version 2)
    #  8     | 4    | Data length (uint32)
    #  12    | N    | Packet data (raw or compressed)
    # In the global compression modes this framing is inside the compressed stream, and the
    # data is always raw.

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

    def to_bytes(self, compression_helper: CompressionHelper, timestamp_format: str = 'd') -> bytes:
        """
        Convert the entry to bytes for serialization.

        Parameters:
        - compression_helper (CompressionHelper): Compression helper object for compression.
        - timestamp_format (str): struct format character of the timestamp ('d' or legacy 'f').

        Returns:
        - bytes: Serialized bytes representation of the entry.
        """
        timestamp_bytes = struct.pack(f'{self.m_endianness_str}{timestamp_format}', self.m_timestamp)
        compressed_data = compression_helper.compress(self.m_data)
        data_length_bytes = struct.pack(f'{self.m_endianness_str}I', len(compressed_data))
        return timestamp_bytes + data_length_bytes + compressed_data

    @classmethod
    def from_bytes(cls, data: bytes, is_little_endian: bool, compression_helper: CompressionHelper,
                   timestamp_format: str = 'd'):
        """
        Create a F1PktCapMessage from serialized bytes.

        Parameters:
        - data (bytes): Serialized bytes containing timestamp and payload length followed by the payload.
        - is_little_endian (bool): Whether the data is in little endian format.
        - compression_helper (CompressionHelper): Compression helper object for decompression.
        - timestamp_format (str): struct format character of the timestamp ('d' or legacy 'f').

        Returns:
        - F1PktCapMessage: Deserialized entry.

        Raises:
        - ValueError: If the length of the payload does not match the expected length specified in the header.
        """
        endianness_str = '<' if is_little_endian else '>'
        frame_fmt = f'{endianness_str}{timestamp_format}I'
        frame_len = struct.calcsize(frame_fmt)
        timestamp, length = struct.unpack(frame_fmt, data[:frame_len])
        compressed_payload = data[frame_len:]
        payload = compression_helper.decompress(compressed_payload)
        if len(compressed_payload) != length:
            raise ValueError(f"Data length mismatch. Header length: {length}, Actual length: {len(compressed_payload)}")
        return F1PktCapMessage(payload, timestamp)

class F1PacketCapture:
    """Represents a collection of F1PktCapMessage objects."""

    major_ver = 1
    minor_ver = 2
    lzma_preset = 6  # preset 9 gains 0.2% for 6x the encoder memory
    lzma_read_chunk = 1 << 20
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
        self.compression_mode = CompressionMode.NONE
        self.is_compressed = False
        self.m_compression_helper: Optional[CompressionHelper] = NoCompressionHelper()

        if file_name:
            self.readFromFile(file_name)
        else:
            self.set_compressed(compressed)
            self.m_header = F1PktCapFileHeader(
                major_version=self.major_ver,
                minor_version=self.minor_ver,
                num_packets=0,
                is_little_endian=self.is_little_endian,
                compression_mode=self.compression_mode)

    def set_compression_mode(self, mode: CompressionMode):
        """Set the compression mode used by dumpToFile."""
        self.compression_mode = mode
        self.is_compressed = mode != CompressionMode.NONE
        # Only the per-packet mode goes through a helper; global modes compress the whole body
        if mode == CompressionMode.PER_PACKET_ZLIB:
            self.m_compression_helper = ZlibCompressionHelper()
        elif mode == CompressionMode.NONE:
            self.m_compression_helper = NoCompressionHelper()
        else:
            self.m_compression_helper = None

    def set_compressed(self, compressed: bool):
        """Compress with the current default scheme (global LZMA) if true, else store raw."""
        self.set_compression_mode(CompressionMode.GLOBAL_LZMA if compressed else CompressionMode.NONE)

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

        packets_snapshot = list(self.m_packet_history)
        total_packet_count = len(packets_snapshot)

        # Construct the header
        header = F1PktCapFileHeader(
            major_version=self.major_ver,
            minor_version=self.minor_ver,
            num_packets=total_packet_count,
            is_little_endian=self.is_little_endian,
            compression_mode=self.compression_mode)

        byte_count = 0
        with open(file_name, "wb") as file:
            file.write(header.to_bytes())
            if self.compression_mode == CompressionMode.GLOBAL_LZMA:
                # Stream into the compressor so the body is never held in memory a second time
                frame_fmt = f'{header.getEndiannessStr()}{header.timestamp_format}I'
                compressor = lzma.LZMACompressor(format=lzma.FORMAT_XZ, preset=self.lzma_preset)
                for curr_packet_count, entry in enumerate(packets_snapshot):
                    chunk = (compressor.compress(struct.pack(frame_fmt, entry.m_timestamp, len(entry.m_data)))
                             + compressor.compress(entry.m_data))
                    file.write(chunk)
                    byte_count += len(chunk)
                    self._notify_progress(progress_update_callback, progress_update_callback_arg,
                                          curr_packet_count, total_packet_count)
                tail = compressor.flush()
                file.write(tail)
                byte_count += len(tail)
            else:
                for curr_packet_count, entry in enumerate(packets_snapshot):
                    data_to_write = entry.to_bytes(self.m_compression_helper, header.timestamp_format)
                    file.write(data_to_write)
                    byte_count += len(data_to_write)
                    self._notify_progress(progress_update_callback, progress_update_callback_arg,
                                          curr_packet_count, total_packet_count)

        return file_name, total_packet_count, byte_count

    @staticmethod
    def _notify_progress(callback: Optional[Callable], callback_arg: Optional[Any], current: int, total: int) -> None:
        """Invoke the dumpToFile progress callback, if any."""
        if callback:
            if callback_arg:
                callback(current, total, callback_arg)
            else:
                callback(current, total)

    def readFromFile(self, file_name: str) -> None:
        """
        Read packet entries from a binary file and populate the packet history.

        Parameters:
            - file_name (str): The name of the file to read from.

        Raises:
            - ValueError: If the file header is invalid (see F1PktCapFileHeader.from_bytes),
                or a compressed body is corrupt. A body that is merely cut short is read as far
                as it goes, with a warning.
        """

        with open(file_name, "rb") as file:
            # First, fetch the file header
            self.m_header = F1PktCapFileHeader.from_bytes(file.read(F1PktCapFileHeader.HEADER_LEN))
            self.set_compression_mode(self.m_header.compression_mode)
            if self.compression_mode == CompressionMode.GLOBAL_LZMA:
                self._read_global_lzma_body(file)
            else:
                self._read_per_packet_body(file)

        if self.m_header.num_packets != len(self.m_packet_history):
            print(f"[WARN]: Number of packets in the file {self.m_header.num_packets} does not match the header "
                             f"{len(self.m_packet_history)}. Possibly corrupt file", file=sys.stderr)

    def _read_per_packet_body(self, file) -> None:
        """Read a body where each packet is framed and (optionally) compressed on its own."""
        endianness_str = self.m_header.getEndiannessStr()
        ts_fmt = self.m_header.timestamp_format
        frame_len = struct.calcsize(f'{endianness_str}{ts_fmt}I')
        while True:
            frame_bytes = file.read(frame_len)
            if not frame_bytes:
                break

            data_length = struct.unpack(f'{endianness_str}I', frame_bytes[-4:])[0]
            payload = file.read(data_length)

            entry = F1PktCapMessage.from_bytes(
                frame_bytes + payload,
                self.m_header.is_little_endian,
                self.m_compression_helper,
                ts_fmt
            )
            self.m_packet_history.append(entry)

    def _read_global_lzma_body(self, file) -> None:
        """Read a body that is one LZMA stream of framed raw packets.

        Decodes incrementally, so a stream cut off mid-write still yields every complete packet.
        """
        frame_fmt = f'{self.m_header.getEndiannessStr()}{self.m_header.timestamp_format}I'
        frame_len = struct.calcsize(frame_fmt)
        decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_XZ)
        buf = bytearray()
        while not decompressor.eof:
            chunk = file.read(self.lzma_read_chunk)
            if not chunk:
                break
            try:
                buf += decompressor.decompress(chunk)
            except lzma.LZMAError as e:
                raise ValueError(f"LZMA decompression failed: {e}") from e

            pos = 0
            while len(buf) - pos >= frame_len:
                timestamp, length = struct.unpack_from(frame_fmt, buf, pos)
                end = pos + frame_len + length
                if end > len(buf):
                    break
                self.m_packet_history.append(
                    F1PktCapMessage(bytes(buf[pos + frame_len:end]), timestamp, self.m_header.is_little_endian))
                pos = end
            del buf[:pos]

        if not decompressor.eof or buf:
            print("[WARN]: Compressed body ends early. Possibly truncated file", file=sys.stderr)

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
