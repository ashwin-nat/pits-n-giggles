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

## NOTE: Please refer to the F1 23 UDP specification document to understand fully how the telemetry data works.
## All classes in supported in this library are documented with the members, but it is still recommended to read the
## official document. https://answers.ea.com/t5/General-Discussion/F1-23-UDP-Specification/m-p/12633159

from __future__ import annotations
import struct
from typing import Dict, Any, List
from .common import _split_list, _extract_sublist, F1Utils, ActualTyreCompound, VisualTyreCompound, PacketHeader

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
        len_total_lap_hist = LapHistoryData.PACKET_LEN * PacketSessionHistoryData.MAX_LAPS
        laps_history_data_all = _extract_sublist(data, bytes_index_so_far, bytes_index_so_far+len_total_lap_hist)
        for per_lap_history_raw in _split_list(laps_history_data_all, LapHistoryData.PACKET_LEN):
            self.m_lapHistoryData.append(LapHistoryData(per_lap_history_raw))
        bytes_index_so_far += len_total_lap_hist

        # Finally, parse tyre stint data
        len_total_tyre_stint = PacketSessionHistoryData.MAX_TYRE_STINT_COUNT * TyreStintHistoryData.PACKET_LEN
        tyre_stint_history_all = _extract_sublist(data, bytes_index_so_far, (bytes_index_so_far+len_total_tyre_stint))
        for tyre_history_per_stint_raw in _split_list(tyre_stint_history_all, TyreStintHistoryData.PACKET_LEN):
            self.m_tyreStintsHistoryData.append(TyreStintHistoryData(tyre_history_per_stint_raw))

        # Trim the tyre stint and lap history lists
        self.m_lapHistoryData = self.m_lapHistoryData[:self.m_numLaps]
        self.m_tyreStintsHistoryData = self.m_tyreStintsHistoryData[:self.m_numTyreStints]

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
