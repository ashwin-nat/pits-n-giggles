# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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
from typing import Any, Dict, List

from .common import PacketHeader

# --------------------- CLASS DEFINITIONS --------------------------------------

class PacketLapPositionsData:
    """
    Class representing lap positions data for a player.

    Attributes:
        m_header (PacketHeader): Header information for the packet.
        m_lapPositions (List[LapPositionData]): List of lap positions data for each player.

    Note:
        The class is designed to parse and represent lap positions data for a player.
    """

    MAX_CARS = 22
    MAX_LAPS = 50
    TOTAL_BYTES = MAX_CARS * MAX_LAPS # its uint8, so no need to multiply by size of each item

    COMPILED_PACKET_STRUCT_BASE = struct.Struct("<BB")
    PACKET_LEN_BASE = COMPILED_PACKET_STRUCT_BASE.size

    COMPILED_PACKET_STRUCT_ARRAY = struct.Struct(f"<{MAX_CARS * MAX_LAPS}B")
    PACKET_LEN_ARRAY = COMPILED_PACKET_STRUCT_ARRAY.size

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        self.m_header: PacketHeader = header
        self.m_numLaps: int
        self.m_lapStart: int
        self.m_lapPositions: List[int]

        self.m_numLaps, self.m_lapStart = self.COMPILED_PACKET_STRUCT_BASE.unpack(packet[:self.PACKET_LEN_BASE])
        flat_array = self.COMPILED_PACKET_STRUCT_ARRAY.unpack(packet[self.PACKET_LEN_BASE:])

        # Convert the flat list into a 2D list: m_numLaps rows (laps), each with 22 cars
        self.m_lapPositions = [list(flat_array[i * self.MAX_CARS:(i + 1) * self.MAX_CARS]) for i in range(self.m_numLaps)]

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """Converts the PacketLapPositions object to a dictionary suitable for JSON serialization.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """

        json_data = {
            "num-laps": self.m_numLaps,
            "lap-start": self.m_lapStart,
            "lap-positions": self.m_lapPositions,
        }

        if include_header:
            json_data["header"] = self.m_header.toJSON()

        return json_data

    def __eq__(self, other: "PacketLapPositionsData") -> bool:
        """Check if two objects are equal

        Args:
            other (PacketLapPositionsData): The object to compare to

        Returns:
            bool: True if the objects are equal, False otherwise
        """

        return \
            self.m_header == other.m_header and \
            self.m_numLaps == other.m_numLaps and \
            self.m_lapStart == other.m_lapStart and \
            self.m_lapPositions == other.m_lapPositions

    def __ne__(self, other: "PacketLapPositionsData") -> bool:
        """Check if two objects are not equal

        Args:
            other (PacketLapPositionsData): The object to compare to

        Returns:
            bool: True if the objects are not equal, False otherwise
        """

        return not self.__eq__(other)
