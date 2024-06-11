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
from typing import Dict, List, Any, Optional
from .common import _split_list, _extract_sublist, PacketHeader, VisualTyreCompound, ActualTyreCompound

# --------------------- CLASS DEFINITIONS --------------------------------------

class TyreSetData:
    """
    Represents information about a specific tyre set, including its compound, wear, availability, and other details.

    Attributes:
        m_actualTyreCompound (int): Actual tyre compound used.
        m_visualTyreCompound (int): Visual tyre compound used.
        m_wear (int): Tyre wear percentage.
        m_available (int): Whether this set is currently available.
        m_recommendedSession (int): Recommended session for the tyre set.
        m_lifeSpan (int): Laps left in this tyre set.
        m_usableLife (int): Max number of laps recommended for this compound.
        m_lapDeltaTime (int): Lap delta time in milliseconds compared to the fitted set.
        m_fitted (bool): Whether the set is fitted or not.

    Methods:
        __init__(self, data: bytes) -> None:
            Initializes TyreSetData with raw data.

        __str__(self) -> str:
            Returns a string representation of TyreSetData.
    """

    PACKET_FORMAT = ("<"
        "B" # uint8     m_actualTyreCompound;    // Actual tyre compound used
        "B" # uint8     m_visualTyreCompound;    // Visual tyre compound used
        "B" # uint8     m_wear;                  // Tyre wear (percentage)
        "B" # uint8     m_available;             // Whether this set is currently available
        "B" # uint8     m_recommendedSession;    // Recommended session for tyre set
        "B" # uint8     m_lifeSpan;              // Laps left in this tyre set
        "B" # uint8     m_usableLife;            // Max number of laps recommended for this compound
        "h" # int16     m_lapDeltaTime;          // Lap delta time in milliseconds compared to fitted set
        "B" # uint8     m_fitted;                // Whether the set is fitted or not
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    def __init__(self, data) -> None:
        """
        Initializes TyreSetData with raw data.

        Args:
            data (bytes): Raw data representing information about a tyre set.
        """

        (
            self.m_actualTyreCompound,
            self.m_visualTyreCompound,
            self.m_wear,
            self.m_available,
            self.m_recommendedSession,
            self.m_lifeSpan,
            self.m_usableLife,
            self.m_lapDeltaTime,
            self.m_fitted,
        ) = struct.unpack(self.PACKET_FORMAT, data)

        if ActualTyreCompound.isValid(self.m_actualTyreCompound):
            self.m_actualTyreCompound = ActualTyreCompound(self.m_actualTyreCompound)
        if VisualTyreCompound.isValid(self.m_visualTyreCompound):
            self.m_visualTyreCompound = VisualTyreCompound(self.m_visualTyreCompound)
        self.m_fitted = bool(self.m_fitted)

    def __str__(self) -> str:
        """
        Returns a string representation of TyreSetData.

        Returns:
            str: String representation of TyreSetData.
        """

        return (
            f"Actual Tyre Compound: {self.m_actualTyreCompound}, Visual Tyre Compound: {self.m_visualTyreCompound}, "
            f"Wear: {self.m_wear}%, Available: {self.m_available}, Recommended Session: {self.m_recommendedSession}, "
            f"Life Span: {self.m_lifeSpan}, Usable Life: {self.m_usableLife}, Lap Delta Time: {self.m_lapDeltaTime} ms, "
            f"Fitted: {self.m_fitted}"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the TyreSetData instance to a JSON-compatible dictionary with kebab-case keys.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the TyreSetData instance.
        """

        return {
            "actual-tyre-compound": str(self.m_actualTyreCompound),
            "visual-tyre-compound": str(self.m_visualTyreCompound),
            "wear": self.m_wear,
            "available": bool(self.m_available),
            "recommended-session": self.m_recommendedSession,
            "life-span": self.m_lifeSpan,
            "usable-life": self.m_usableLife,
            "lap-delta-time": self.m_lapDeltaTime,
            "fitted": bool(self.m_fitted),
        }

class PacketTyreSetsData:
    """
    Represents information about tyre sets for a specific car in a race.

    Attributes:
        m_header (PacketHeader): Header information for the packet.
        m_carIdx (int): Index of the car this data relates to.
        m_tyreSetData (List[TyreSetData]): List of TyreSetData objects representing tyre set information.
        m_fittedIdx (int): Index into the array of the fitted tyre.

    """
    max_tyre_sets = 20

    def __init__(self, header, data) -> None:
        """
        Initializes PacketTyreSetsData with raw data.

        Args:
            header (PacketHeader): Header information for the packet.
            data (bytes): Raw data representing information about tyre sets for a car in a race.
        """

        self.m_header: PacketHeader = header
        self.m_carIdx: int = struct.unpack("<B", data[0:1])[0]
        self.m_tyreSetData: List[TyreSetData] = []

        tyre_set_data_full_len = PacketTyreSetsData.max_tyre_sets * TyreSetData.PACKET_LEN
        full_tyre_set_data_raw = _extract_sublist(data, 1, 1 + tyre_set_data_full_len)
        for tyre_set_data_raw in _split_list(full_tyre_set_data_raw, TyreSetData.PACKET_LEN):
            self.m_tyreSetData.append(TyreSetData(tyre_set_data_raw))

        self.m_fittedIdx = struct.unpack("<B", data[(1 + tyre_set_data_full_len):])[0]

    def __str__(self) -> str:
        """
        Returns a string representation of PacketTyreSetsData.

        Returns:
            str: String representation of PacketTyreSetsData.
        """

        return (
            f"Header: {str(self.m_header)}, Car Index: {self.m_carIdx}, "
            f"Tyre Set Data: {[str(tyre_set_data) for tyre_set_data in self.m_tyreSetData]}, Fitted Index: {self.m_fittedIdx}"
        )

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketTyreSetsData instance to a JSON-compatible dictionary with kebab-case keys.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the PacketTyreSetsData instance.
        """

        json_data = {
            "car-index": self.m_carIdx,
            "tyre-set-data": [tyre_set_data.toJSON() for tyre_set_data in self.m_tyreSetData],
            "fitted-index": self.m_fittedIdx
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

    def getFittedTyreSetKey(self) -> Optional[str]:
        """Key containing tyre set ID and actual compound name

        Returns:
            Optional[str]: Key if fitted index is valid, else None
        """

        if self.m_fittedIdx == 255:
            return None
        return str(self.m_fittedIdx) + "." + str(self.m_tyreSetData[self.m_fittedIdx].m_actualTyreCompound)

    def getTyreSetKey(self, index) -> Optional[str]:
        """Key containing tyre set ID and actual compound name for the given index

        Arguments:
            index (int): Tyre set index

        Returns:
            Optional[str]: Key if index is valid, else None
        """

        if 0 <= index < len(self.m_tyreSetData):
            return str(index) + "." + str(self.m_tyreSetData[index].m_actualTyreCompound)
        return None