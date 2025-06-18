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


from __future__ import annotations

import struct
from typing import Any, Dict, List, Optional

from .common import (ActualTyreCompound, F1Utils, PacketHeader,
                     VisualTyreCompound, _validate_parse_fixed_segments)

# --------------------- CLASS DEFINITIONS --------------------------------------

class LapHistoryData:
    """
    Class representing lap history data for a session.

    Attributes:
        m_lapTimeInMS (uint32): Lap time in milliseconds.
        m_sector1TimeInMS (uint16): Sector 1 time in milliseconds.
        m_sector1TimeMinutes (uint8): Sector 1 whole minute part.
        m_sector2TimeInMS (uint16): Sector 2 time in milliseconds.
        m_sector2TimeMinutes (uint8): Sector 2 whole minute part.
        m_sector3TimeInMS (uint16): Sector 3 time in milliseconds.
        m_sector3TimeMinutes (uint8): Sector 3 whole minute part.
        m_lapValidBitFlags (uint8): Bit flags representing lap and sector validity.

    Note:
        - The lapValidBitFlags use individual bits to indicate the validity of the lap and each sector.
        - 0x01 bit set: Lap valid
        - 0x02 bit set: Sector 1 valid
        - 0x04 bit set: Sector 2 valid
        - 0x08 bit set: Sector 3 valid
    """

    FULL_LAP_VALID_BIT_MASK = 0x01
    SECTOR_1_VALID_BIT_MASK = 0x02
    SECTOR_2_VALID_BIT_MASK = 0x04
    SECTOR_3_VALID_BIT_MASK = 0x08

    PACKET_FORMAT = ("<"
        "I" # uint32    m_lapTimeInMS;           // Lap time in milliseconds
        "H" # uint16    m_sector1TimeInMS;       // Sector 1 time in milliseconds
        "B" # uint8     m_sector1TimeMinutes;    // Sector 1 whole minute part
        "H" # uint16    m_sector2TimeInMS;       // Sector 2 time in milliseconds
        "B" # uint8     m_sector1TimeMinutes;    // Sector 2 whole minute part
        "H" # uint16    m_sector3TimeInMS;       // Sector 3 time in milliseconds
        "B" # uint8     m_sector3TimeMinutes;    // Sector 3 whole minute part
        "B" # uint8     m_lapValidBitFlags;      // 0x01 bit set-lap valid,      0x02 bit set-sector 1 valid
                                        #    // 0x04 bit set-sector 2 valid, 0x08 bit set-sector 3 valid
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    def __init__(self, data: bytes) -> None:
        """
        Initializes LapHistoryData with raw data.

        Args:
            data (bytes): Raw data representing lap history for a session.
        """

        self.m_lapTimeInMS: int
        self.m_sector1TimeInMS: int
        self.m_sector1TimeMinutes: int
        self.m_sector2TimeInMS: int
        self.m_sector2TimeMinutes: int
        self.m_sector3TimeInMS: int
        self.m_sector3TimeMinutes: int
        self.m_lapValidBitFlag: int

        (
            self.m_lapTimeInMS,
            self.m_sector1TimeInMS,
            self.m_sector1TimeMinutes,
            self.m_sector2TimeInMS,
            self.m_sector2TimeMinutes,
            self.m_sector3TimeInMS,
            self.m_sector3TimeMinutes,
            self.m_lapValidBitFlags,
        ) = struct.unpack(self.PACKET_FORMAT, data)

    def __str__(self) -> str:
        """
        Returns a string representation of LapHistoryData.

        Returns:
            str: String representation of LapHistoryData.
        """

        return (
            f"Lap Time: {self.m_lapTimeInMS} ms, "
            f"Sector 1 Time: {self.m_sector1TimeInMS} ms, "
            f"Sector 1 Minutes: {self.m_sector1TimeMinutes}, "
            f"Sector 2 Time: {self.m_sector2TimeInMS} ms, "
            f"Sector 2 Minutes: {self.m_sector2TimeMinutes}, "
            f"Sector 3 Time: {self.m_sector3TimeInMS} ms, "
            f"Sector 3 Minutes: {self.m_sector3TimeMinutes}, "
            f"Lap Valid Bit Flags: {self.m_lapValidBitFlags}"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the LapHistoryData instance to a JSON-compatible dictionary with kebab-case keys.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the LapHistoryData instance.
        """

        return {
            "lap-time-in-ms": self.m_lapTimeInMS,
            "lap-time-str": F1Utils.millisecondsToMinutesSecondsMilliseconds(self.m_lapTimeInMS),
            "sector-1-time-in-ms": self.m_sector1TimeInMS,
            "sector-1-time-minutes": self.m_sector1TimeMinutes,
            "sector-1-time-str" : F1Utils.getLapTimeStrSplit(self.m_sector1TimeMinutes, self.m_sector1TimeInMS),
            "sector-2-time-in-ms": self.m_sector2TimeInMS,
            "sector-2-time-minutes": self.m_sector2TimeMinutes,
            "sector-2-time-str": F1Utils.getLapTimeStrSplit(self.m_sector2TimeMinutes, self.m_sector2TimeInMS),
            "sector-3-time-in-ms": self.m_sector3TimeInMS,
            "sector-3-time-minutes": self.m_sector3TimeMinutes,
            "sector-3-time-str": F1Utils.getLapTimeStrSplit(self.m_sector3TimeMinutes, self.m_sector3TimeInMS),
            "lap-valid-bit-flags": self.m_lapValidBitFlags,
        }

    def isSector1Valid(self) -> bool:
        """Check if the first sector of this lap was valid

        Returns:
            bool: True if valid, False if invalid
        """

        return self.m_lapValidBitFlags & LapHistoryData.SECTOR_1_VALID_BIT_MASK

    def isSector2Valid(self) -> bool:
        """Check if the second sector of this lap was valid

        Returns:
            bool: True if valid, False if invalid
        """

        return self.m_lapValidBitFlags & LapHistoryData.SECTOR_2_VALID_BIT_MASK

    def isSector3Valid(self) -> bool:
        """Check if the third sector of this lap was valid

        Returns:
            bool: True if valid, False if invalid
        """

        return self.m_lapValidBitFlags & LapHistoryData.SECTOR_3_VALID_BIT_MASK

    def isLapValid(self) -> bool:
        """Check if this lap was valid

        Returns:
            bool: True if valid, False if invalid
        """

        return self.m_lapValidBitFlags & LapHistoryData.FULL_LAP_VALID_BIT_MASK

    @property
    def s1TimeMS(self) -> int:
        """Return the total S1 time in ms

        Returns:
            int: Total S1 time in ms
        """

        return self.__getCombinedTimeMS(self.m_sector1TimeInMS, self.m_sector1TimeMinutes)

    @property
    def s2TimeMS(self) -> int:
        """Return the total S2 time in ms

        Returns:
            int: Total S2 time in ms
        """

        return self.__getCombinedTimeMS(self.m_sector2TimeInMS, self.m_sector2TimeMinutes)

    @property
    def s3TimeMS(self) -> int:
        """Return the total S3 time in ms

        Returns:
            int: Total S3 time in ms
        """

        return self.__getCombinedTimeMS(self.m_sector3TimeInMS, self.m_sector3TimeMinutes)

    def __getCombinedTimeMS(self, ms_part: int, min_part: int) -> int:
        """
        Combines minutes and milliseconds into a total time in milliseconds.

        Args:
            ms_part (int): The milliseconds part of the time.
            min_part (int): The minutes part of the time.

        Returns:
            int: The total time in milliseconds.
        """
        return (min_part * 60 * 1000) + ms_part

    def __eq__(self, other: "LapHistoryData") -> bool:
        """Check if two LapHistoryData objects are equal

        Args:
            other (LapHistoryData): The object to compare to

        Returns:
            bool: True if the objects are equal, False otherwise
        """

        return (
            self.m_lapTimeInMS == other.m_lapTimeInMS
            and self.m_sector1TimeInMS == other.m_sector1TimeInMS
            and self.m_sector1TimeMinutes == other.m_sector1TimeMinutes
            and self.m_sector2TimeInMS == other.m_sector2TimeInMS
            and self.m_sector2TimeMinutes == other.m_sector2TimeMinutes
            and self.m_sector3TimeInMS == other.m_sector3TimeInMS
            and self.m_sector3TimeMinutes == other.m_sector3TimeMinutes
            and self.m_lapValidBitFlags == other.m_lapValidBitFlags
        )

    def __ne__(self, other: "LapHistoryData") -> bool:
        """Check if two LapHistoryData objects are not equal

        Args:
            other (LapHistoryData): The object to compare to

        Returns:
            bool: True if the objects are not equal, False otherwise
        """

        return not self.__eq__(other)

class TyreStintHistoryData:
    """
    Class representing tyre stint history data for a session.

    Attributes:
        m_endLap (uint8): Lap the tyre usage ends on (255 if current tyre).
        m_tyreActualCompound (ActualTyreCompound): Actual tyres used by this driver.
        m_tyreVisualCompound (VisualTyreCompound): Visual tyres used by this driver.
    """

    PACKET_FORMAT = ("<"
        "B" # uint8     m_endLap;                // Lap the tyre usage ends on (255 of current tyre)
        "B" # uint8     m_tyreActualCompound;    // Actual tyres used by this driver
        "B" # uint8     m_tyreVisualCompound;    // Visual tyres used by this driver
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    def __init__(self, data: bytes) -> None:
        """
        Initializes TyreStintHistoryData with raw data.

        Args:
            data (bytes): Raw data representing tyre stint history for a session.
        """

        (
            self.m_endLap,
            self.m_tyreActualCompound,
            self.m_tyreVisualCompound,
        ) = struct.unpack(self.PACKET_FORMAT, data)

        if ActualTyreCompound.isValid(self.m_tyreActualCompound):
            self.m_tyreActualCompound = ActualTyreCompound(self.m_tyreActualCompound)
        if VisualTyreCompound.isValid(self.m_tyreVisualCompound):
            self.m_tyreVisualCompound = VisualTyreCompound(self.m_tyreVisualCompound)

    def __str__(self) -> str:
        """
        Returns a string representation of TyreStintHistoryData.

        Returns:
            str: String representation of TyreStintHistoryData.
        """

        return (
            f"End Lap: {self.m_endLap}, "
            f"Tyre Actual Compound: {str(self.m_tyreActualCompound)}, "
            f"Tyre Visual Compound: {str(self.m_tyreVisualCompound)}"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the TyreStintHistoryData instance to a JSON-compatible dictionary with kebab-case keys.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing
                                the TyreStintHistoryData instance.
        """

        return {
            "end-lap": self.m_endLap,
            "tyre-actual-compound": str(self.m_tyreActualCompound),
            "tyre-visual-compound": str(self.m_tyreVisualCompound),
        }

    def __eq__(self, other: "TyreStintHistoryData") -> bool:
        """Check if two TyreStintHistoryData objects are equal

        Args:
            other (TyreStintHistoryData): The object to compare to

        Returns:
            bool: True if the objects are equal, False otherwise
        """

        return (
            self.m_endLap == other.m_endLap
            and self.m_tyreActualCompound == other.m_tyreActualCompound
            and self.m_tyreVisualCompound == other.m_tyreVisualCompound
        )

    def __ne__(self, other: "TyreStintHistoryData") -> bool:
        """Check if two TyreStintHistoryData objects are not equal

        Args:
            other (TyreStintHistoryData): The object to compare to

        Returns:
            bool: True if the objects are not equal, False otherwise
        """

        return not self.__eq__(other)

class PacketSessionHistoryData:
    """
    Represents the packet containing session history data for a specific car.

    Attributes:
        m_header (PacketHeader): The header of the packet.
        m_carIdx (int): Index of the car this lap data relates to.
        m_numLaps (int): Number of laps in the data (including the current partial lap).
        m_numTyreStints (int): Number of tyre stints in the data.
        m_bestLapTimeLapNum (int): Lap the best lap time was achieved on.
        m_bestSector1LapNum (int): Lap the best Sector 1 time was achieved on.
        m_bestSector2LapNum (int): Lap the best Sector 2 time was achieved on.
        m_bestSector3LapNum (int): Lap the best Sector 3 time was achieved on.
        m_lapHistoryData (List[LapHistoryData]): List of lap history data for each lap.
        m_tyreStintsHistoryData (List[TyreStintHistoryData]): List of tyre stint history data.
    """

    MAX_LAPS = 100
    MAX_TYRE_STINT_COUNT = 8

    PACKET_FORMAT = ("<"
        "B" # uint8         m_carIdx;                   // Index of the car this lap data relates to
        "B" # uint8         m_numLaps;                  // Num laps in the data (including current partial lap)
        "B" # uint8         m_numTyreStints;            // Number of tyre stints in the data

        "B" # uint8         m_bestLapTimeLapNum;        // Lap the best lap time was achieved on
        "B" # uint8         m_bestSector1LapNum;        // Lap the best Sector 1 time was achieved on
        "B" # uint8         m_bestSector2LapNum;        // Lap the best Sector 2 time was achieved on
        "B" # uint8         m_bestSector3LapNum;        // Lap the best Sector 3 time was achieved on
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    def __init__(self, header, data) -> None:
        """
        Initializes PacketSessionHistoryData with raw data.

        Args:
            header (PacketHeader): The header of the packet.
            data (bytes): Raw data representing session history for a car in a race.
        """

        self.m_carIdx : int
        self.m_numLaps : int
        self.m_numTyreStints : int
        self.m_bestLapTimeLapNum : int
        self.m_bestSector1LapNum : int
        self.m_bestSector2LapNum : int
        self.m_bestSector3LapNum : int

        self.m_header: PacketHeader = header
        (
            self.m_carIdx,
            self.m_numLaps,
            self.m_numTyreStints,
            self.m_bestLapTimeLapNum,
            self.m_bestSector1LapNum,
            self.m_bestSector2LapNum,
            self.m_bestSector3LapNum,
        ) = struct.unpack(self.PACKET_FORMAT, data[:self.PACKET_LEN])
        bytes_index_so_far = self.PACKET_LEN

        self.m_lapHistoryData: List[LapHistoryData] = []
        self.m_tyreStintsHistoryData: List[TyreStintHistoryData] = []

        # Next, parse the lap history data
        self.m_lapHistoryData, bytes_index_so_far = _validate_parse_fixed_segments(
            data=data,
            offset=bytes_index_so_far,
            item_cls=LapHistoryData,
            item_len=LapHistoryData.PACKET_LEN,
            count=self.m_numLaps,
            max_count=PacketSessionHistoryData.MAX_LAPS,
        )

        # Finally, parse tyre stint data
        self.m_tyreStintsHistoryData, bytes_index_so_far = _validate_parse_fixed_segments(
            data=data,
            offset=bytes_index_so_far,
            item_cls=TyreStintHistoryData,
            item_len=TyreStintHistoryData.PACKET_LEN,
            count=self.m_numTyreStints,
            max_count=PacketSessionHistoryData.MAX_TYRE_STINT_COUNT,
        )

    def __str__(self) -> str:
        """
        Returns a string representation of PacketSessionHistoryData.

        Returns:
            str: String representation of PacketSessionHistoryData.
        """

        tyre_stint_str = \
            [str(tyre_stint_data) for tyre_stint_data in self.m_tyreStintsHistoryData[self.m_numTyreStints:]]
        return (
            f"Header: {str(self.m_header)}, "
            f"Car Index: {self.m_carIdx}, "
            f"Num Laps: {self.m_numLaps}, "
            f"Num Tyre Stints: {self.m_numTyreStints}, "
            f"Best Lap Time Lap Num: {self.m_bestLapTimeLapNum}, "
            f"Best Sector 1 Lap Num: {self.m_bestSector1LapNum}, "
            f"Best Sector 2 Lap Num: {self.m_bestSector2LapNum}, "
            f"Best Sector 3 Lap Num: {self.m_bestSector3LapNum}, "
            f"Lap History Data: {[str(lap_data) for lap_data in self.m_lapHistoryData[self.m_numLaps:]]}, "
            f"Tyre Stints History Data: {tyre_stint_str}"
        )

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketSessionHistoryData instance to a JSON-compatible dictionary with kebab-case keys.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the PacketSessionHistoryData instance.
        """

        json_data = {
            "car-index": self.m_carIdx,
            "num-laps": self.m_numLaps,
            "num-tyre-stints": self.m_numTyreStints,
            "best-lap-time-lap-num": self.m_bestLapTimeLapNum,
            "best-sector-1-lap-num": self.m_bestSector1LapNum,
            "best-sector-2-lap-num": self.m_bestSector2LapNum,
            "best-sector-3-lap-num": self.m_bestSector3LapNum,
            "lap-history-data": [lap.toJSON() for lap in self.m_lapHistoryData],
            "tyre-stints-history-data": [tyre.toJSON() for tyre in self.m_tyreStintsHistoryData],
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()

        return json_data

    def getLastLapData(self) -> Optional[LapHistoryData]:
        """Get the last completed lap data

        Returns:
            LapHistoryData: The last lap data. May be None if not found
        """

        return next(
            (
                lap_data
                for lap_data in reversed(self.m_lapHistoryData)
                if (lap_data.m_lapTimeInMS > 0)
                and (lap_data.m_sector1TimeInMS > 0)
                and (lap_data.m_sector2TimeInMS > 0)
                and (lap_data.m_sector3TimeInMS > 0)
            ),
            None,
        )

    def getBestLapData(self) -> Optional[LapHistoryData]:
        """Get the best lap data

        Returns:
            LapHistoryData: The best lap data. May be None if not found
        """

        # Index is lap number - 1, ensure it is within valid bounds
        if self.m_bestLapTimeLapNum and 1 <= self.m_bestLapTimeLapNum <= len(self.m_lapHistoryData):
            return self.m_lapHistoryData[self.m_bestLapTimeLapNum - 1]
        return None

    @property
    def is_valid(self) -> bool:
        """Checks if the PacketSessionHistoryData instance is valid (contains data)"""
        return (
            self.m_numLaps > 0
            and self.m_bestLapTimeLapNum > 0
            and self.m_bestSector1LapNum > 0
            and self.m_bestSector2LapNum > 0
            and self.m_bestSector3LapNum > 0
        )

    def __eq__(self, other: "PacketSessionHistoryData") -> bool:
        """
        Compare two PacketSessionHistoryData instances for equality.

        Parameters:
            - other (PacketSessionHistoryData): The other PacketSessionHistoryData instance to compare with.

        Returns:
            bool: True if the two PacketSessionHistoryData instances are equal, False otherwise.
        """

        return (
            self.m_carIdx == other.m_carIdx
            and self.m_numLaps == other.m_numLaps
            and self.m_numTyreStints == other.m_numTyreStints
            and self.m_bestLapTimeLapNum == other.m_bestLapTimeLapNum
            and self.m_bestSector1LapNum == other.m_bestSector1LapNum
            and self.m_bestSector2LapNum == other.m_bestSector2LapNum
            and self.m_bestSector3LapNum == other.m_bestSector3LapNum
            and self.m_lapHistoryData == other.m_lapHistoryData
            and self.m_tyreStintsHistoryData == other.m_tyreStintsHistoryData
        )

    def __ne__(self, other: "PacketSessionHistoryData") -> bool:
        """
        Compare two PacketSessionHistoryData instances for inequality.

        Parameters:
            - other (PacketSessionHistoryData): The other PacketSessionHistoryData instance to compare with.

        Returns:
            bool: True if the two PacketSessionHistoryData instances are not equal, False otherwise.
        """

        return not self.__eq__(other)
