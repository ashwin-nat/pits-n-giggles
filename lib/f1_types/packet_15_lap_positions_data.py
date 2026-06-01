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

from .header import PacketHeader
from .base_pkt import F1PacketBase

# --------------------- CLASS DEFINITIONS --------------------------------------

class PacketLapPositionsData(F1PacketBase):
    """
    Class representing lap positions data for a race session.

    Attributes:
        m_header (PacketHeader): Header information for the packet.
        m_numLaps (int): Number of laps recorded in this packet.
        m_lapStart (int): Starting lap number.
        m_lapPositions (List[List[int]]): 2D list of car positions per lap.
            Outer index = lap, inner index = car position entry (22 cars for pre-2026, 24 for 2026+).
        m_numCars (int): Number of cars in the array (22 for pre-2026, 24 for F1 26+).
    """

    MAX_CARS = 22
    MAX_CARS_2026 = 24
    MAX_LAPS = 50

    COMPILED_PACKET_STRUCT_BASE = struct.Struct("<BB")
    PACKET_LEN_BASE = COMPILED_PACKET_STRUCT_BASE.size

    COMPILED_PACKET_STRUCT_ARRAY = struct.Struct(f"<{MAX_CARS * MAX_LAPS}B")
    PACKET_LEN_ARRAY = COMPILED_PACKET_STRUCT_ARRAY.size

    # F1 26: car count grows from 22 to 24
    COMPILED_PACKET_STRUCT_ARRAY_2026 = struct.Struct(f"<{MAX_CARS_2026 * MAX_LAPS}B")
    PACKET_LEN_ARRAY_2026 = COMPILED_PACKET_STRUCT_ARRAY_2026.size

    __slots__ = (
        "m_numLaps",
        "m_lapStart",
        "m_lapPositions",
        "m_numCars",
    )

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        super().__init__(header)
        self.m_numLaps: int
        self.m_lapStart: int
        self.m_lapPositions: List[int]
        self.m_numCars: int

        self.m_numLaps, self.m_lapStart = self.COMPILED_PACKET_STRUCT_BASE.unpack(packet[:self.PACKET_LEN_BASE])

        if header.m_packetFormat >= 2026:
            arr_struct = self.COMPILED_PACKET_STRUCT_ARRAY_2026
            self.m_numCars = self.MAX_CARS_2026
        else:
            arr_struct = self.COMPILED_PACKET_STRUCT_ARRAY
            self.m_numCars = self.MAX_CARS

        flat_array = arr_struct.unpack(packet[self.PACKET_LEN_BASE:])

        # Convert the flat list into a 2D list: m_numLaps rows (laps), each with m_numCars cars
        self.m_lapPositions = [
            list(flat_array[i * self.m_numCars:(i + 1) * self.m_numCars])
            for i in range(self.m_numLaps)
        ]

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

    def to_bytes(self) -> bytes:
        """Serialize this object to bytes.

        Returns:
            bytes: The binary representation
        """

        base_bytes = self.COMPILED_PACKET_STRUCT_BASE.pack(self.m_numLaps, self.m_lapStart)

        # Pad each lap row to m_numCars entries (trailing zeros for unused slots)
        flat: List[int] = []
        for lap_row in self.m_lapPositions:
            padded = list(lap_row) + [0] * (self.m_numCars - len(lap_row))
            flat.extend(padded[:self.m_numCars])

        # Fill remaining (MAX_LAPS - m_numLaps) rows with zeros
        flat.extend([0] * (self.m_numCars * (self.MAX_LAPS - self.m_numLaps)))

        if self.m_numCars == self.MAX_CARS_2026:
            arr_bytes = self.COMPILED_PACKET_STRUCT_ARRAY_2026.pack(*flat)
        else:
            arr_bytes = self.COMPILED_PACKET_STRUCT_ARRAY.pack(*flat)

        return self.m_header.to_bytes() + base_bytes + arr_bytes

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    num_laps: int,
                    lap_start: int,
                    lap_positions: List[List[int]]) -> "PacketLapPositionsData":
        """Create a PacketLapPositionsData from constituent values.

        Args:
            header (PacketHeader): The packet header
            num_laps (int): Number of laps recorded
            lap_start (int): Starting lap number
            lap_positions (List[List[int]]): 2D list of car positions per lap

        Returns:
            PacketLapPositionsData: The constructed object
        """

        num_cars = cls.MAX_CARS_2026 if header.m_packetFormat >= 2026 else cls.MAX_CARS

        base_bytes = cls.COMPILED_PACKET_STRUCT_BASE.pack(num_laps, lap_start)

        flat: List[int] = []
        for lap_row in lap_positions:
            padded = list(lap_row) + [0] * (num_cars - len(lap_row))
            flat.extend(padded[:num_cars])
        flat.extend([0] * (num_cars * (cls.MAX_LAPS - num_laps)))

        if num_cars == cls.MAX_CARS_2026:
            arr_bytes = cls.COMPILED_PACKET_STRUCT_ARRAY_2026.pack(*flat)
        else:
            arr_bytes = cls.COMPILED_PACKET_STRUCT_ARRAY.pack(*flat)

        return cls(header, base_bytes + arr_bytes)
