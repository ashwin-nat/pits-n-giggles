import struct
import time
from typing import Optional, List, Tuple, Generator

class F1PacketCaptureEntry:
    """Represents an entry in the F1PacketCapture."""

    def __init__(self, data: bytes, timestamp: float = None):
        """
        Initialize a F1PacketCaptureEntry.

        Parameters:
        - data (bytes): Raw data for the entry.
        - timestamp (float) : The timestamp to be written, will be initialised with current time if not provid
        """
        self._m_data = data
        self.m_timestamp = time.time()

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
        timestamp_bytes = struct.pack('f', self.m_timestamp)
        data_length_bytes = struct.pack('I', len(self.m_data))
        return timestamp_bytes + data_length_bytes + self.m_data

    @classmethod
    def from_bytes(cls, data: bytes):
        """
        Create a F1PacketCaptureEntry from serialized bytes.

        Parameters:
        - data (bytes): Serialized bytes containing timestamp and payload length followed by the payload.

        Returns:
        - F1PacketCaptureEntry: Deserialized entry.

        Raises:
        - ValueError: If the length of the payload does not match the expected length specified in the header.
        """
        # Rest of the code remains the same
        timestamp, length = struct.unpack('fI', data[:8])
        payload = data[8:]
        if len(payload) != length:
            raise ValueError(f"Data length mismatch. Header length: {length}, Actual length: {len(payload)}")
        return F1PacketCaptureEntry(payload, timestamp)

class F1PacketCapture:
    """Represents a collection of F1PacketCaptureEntry objects."""

    def __init__(self, file_name:str=None):
        """Initialize a F1PacketCapture.

        Parmeters:
            file_name(str): If specified, will parse the given file into this container
        """
        self.m_packet_history: List[F1PacketCaptureEntry] = []
        if file_name:
            self.readFromFile(file_name, append=False)

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
        entry = F1PacketCaptureEntry(data)
        self.m_packet_history.append(entry)

    def getNumPackets(self) -> int:
        """Get the number of packets in the list

        Returns:
            int: Number of packets in memory
        """

        return len(self.m_packet_history)

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
            file_name = f"capture_{timestamp_str}.bin"

        byte_count = 0
        packet_count = 0

        # Batch write to file
        data_to_write = b''.join(entry.to_bytes() for entry in self.m_packet_history)

        with open(file_name, mode) as file:
            file.write(data_to_write)
            packet_count = len(self.m_packet_history)
            byte_count = len(data_to_write)

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
            while True:
                header_bytes = file.read(8)  # Assuming a fixed size for the header
                if not header_bytes:
                    break

                timestamp_bytes = header_bytes[:4]
                data_length_bytes = header_bytes[4:]
                data_length = struct.unpack('I', data_length_bytes)[0]

                payload = file.read(data_length)

                # Concatenate timestamp_bytes, data_length_bytes, and payload
                entry_data = timestamp_bytes + data_length_bytes + payload

                # Use F1PacketCaptureEntry.from_bytes to create the entry
                entry = F1PacketCaptureEntry.from_bytes(entry_data)
                self.m_packet_history.append(entry)

    def getPackets(self) -> Generator[Tuple[float, bytes], None, None]:
        """
        Generate packets from the packet history.

        Yields:
        - Tuple[float, bytes]: A tuple containing timestamp (float) and data (bytes) for each packet.
        """
        for entry in self.m_packet_history:
            yield entry.m_timestamp, entry.m_data