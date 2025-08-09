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
from typing import Any, Dict, List, Optional, Union

from .common import (ActualTyreCompound, PacketHeader, SessionType23, _validate_parse_fixed_segments,
                     SessionType24, VisualTyreCompound)

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

    COMPILED_PACKET_STRUCT = struct.Struct("<"
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
    PACKET_LEN = COMPILED_PACKET_STRUCT.size

    def __init__(self, data: bytes, packet_format: int) -> None:
        """
        Initializes TyreSetData with raw data.

        Args:
            data (bytes): Raw data representing information about a tyre set.
            packet_format (int): The packet format version.
        """

        self.m_packetFormat = packet_format
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
        ) = self.COMPILED_PACKET_STRUCT.unpack(data)

        if ActualTyreCompound.isValid(self.m_actualTyreCompound):
            self.m_actualTyreCompound = ActualTyreCompound(self.m_actualTyreCompound)
        if VisualTyreCompound.isValid(self.m_visualTyreCompound):
            self.m_visualTyreCompound = VisualTyreCompound(self.m_visualTyreCompound)
        if self.m_packetFormat == 2023 and SessionType23.isValid(self.m_recommendedSession):
            self.m_recommendedSession = SessionType23(self.m_recommendedSession)
        elif self.m_packetFormat in {2024, 2025} and SessionType24.isValid(self.m_recommendedSession):
            self.m_recommendedSession = SessionType24(self.m_recommendedSession)
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
            "recommended-session": str(self.m_recommendedSession),
            "life-span": self.m_lifeSpan,
            "usable-life": self.m_usableLife,
            "lap-delta-time": self.m_lapDeltaTime,
            "fitted": bool(self.m_fitted),
        }

    def __eq__(self, other: "TyreSetData") -> bool:
        """
        Returns whether the TyreSetData instances are equal.

        Args:
            other (TyreSetData): The TyreSetData instance to compare with.

        Returns:
            bool: True if the TyreSetData instances are equal, False otherwise.
        """

        return (
            self.m_actualTyreCompound == other.m_actualTyreCompound and \
            self.m_visualTyreCompound == other.m_visualTyreCompound and \
            self.m_wear == other.m_wear and \
            self.m_available == other.m_available and \
            self.m_recommendedSession == other.m_recommendedSession and \
            self.m_lifeSpan == other.m_lifeSpan and \
            self.m_usableLife == other.m_usableLife and \
            self.m_lapDeltaTime == other.m_lapDeltaTime and \
            self.m_fitted == other.m_fitted
        )

    def __ne__(self, other: "TyreSetData") -> bool:
        """
        Returns whether the TyreSetData instances are not equal.

        Args:
            other (TyreSetData): The TyreSetData instance to compare with.

        Returns:
            bool: True if the TyreSetData instances are not equal, False otherwise.
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Serialize the TyreSetData object to bytes based on PACKET_FORMAT.

        Returns:
            bytes: Serialized bytes representation of the TyreSetData object
        """

        return self.COMPILED_PACKET_STRUCT.pack(
            self.m_actualTyreCompound.value,
            self.m_visualTyreCompound.value,
            self.m_wear,
            self.m_available,
            self.m_recommendedSession.value,
            self.m_lifeSpan,
            self.m_usableLife,
            self.m_lapDeltaTime,
            self.m_fitted,
        )

    @classmethod
    def from_values(cls,
                packet_format: int,
                actual_tyre_compound: ActualTyreCompound,
                visual_tyre_compound: VisualTyreCompound,
                wear: int,
                available: bool,
                recommended_session: Union[SessionType23, SessionType24],
                life_span: int,
                usable_life: int,
                lap_delta_time: int,
                fitted: bool) -> bool:
        """
        Creates a new TyreSetData object from the given values

        Args:
            packet_format (int): Packet format
            actual_tyre_compound (ActualTyreCompound): Actual tyre compound
            visual_tyre_compound (VisualTyreCompound): Visual tyre compound
            wear (int): Wear percentage
            available (bool): Available
            recommended_session (Union[SessionType23, SessionType24]): Recommended session
            life_span (int): Life span
            usable_life (int): Usable life
            lap_delta_time (int): Lap delta time
            fitted (bool): Fitted

        Returns:
            TyreSetData: New TyreSetData object
        """
        return cls(cls.COMPILED_PACKET_STRUCT.pack(
            actual_tyre_compound.value,
            visual_tyre_compound.value,
            wear,
            available,
            recommended_session.value,
            life_span,
            usable_life,
            lap_delta_time,
            fitted), packet_format)

class PacketTyreSetsData:
    """
    Represents information about tyre sets for a specific car in a race.

    Attributes:
        m_header (PacketHeader): Header information for the packet.
        m_carIdx (int): Index of the car this data relates to.
        m_tyreSetData (List[TyreSetData]): List of TyreSetData objects representing tyre set information.
        m_fittedIdx (int): Index into the array of the fitted tyre.

    """
    MAX_TYRE_SETS = 20

    COMPILED_PACKET_STRUCT_CAR_IDX = struct.Struct("<B")
    PACKET_LEN_CAR_IDX = COMPILED_PACKET_STRUCT_CAR_IDX.size

    COMPILED_PACKET_STRUCT_FITTED_IDX = struct.Struct("<B")
    PACKET_LEN_FITTED_IDX = COMPILED_PACKET_STRUCT_FITTED_IDX.size

    def __init__(self, header: PacketHeader, data: bytes) -> None:
        """
        Initializes PacketTyreSetsData with raw data.

        Args:
            header (PacketHeader): Header information for the packet.
            data (bytes): Raw data representing information about tyre sets for a car in a race.
        """

        self.m_header: PacketHeader = header
        self.m_carIdx: int = self.COMPILED_PACKET_STRUCT_CAR_IDX.unpack(data[:self.PACKET_LEN_CAR_IDX])[0]

        self.m_tyreSetData: List[TyreSetData]
        self.m_tyreSetData, offset_so_far = _validate_parse_fixed_segments(
            data=data,
            offset=self.PACKET_LEN_CAR_IDX,
            item_cls=TyreSetData,
            item_len=TyreSetData.PACKET_LEN,
            count=self.MAX_TYRE_SETS,
            max_count=self.MAX_TYRE_SETS,
            packet_format=header.m_packetFormat
        )

        self.m_fittedIdx: int = self.COMPILED_PACKET_STRUCT_FITTED_IDX.unpack(data[offset_so_far:])[0]

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
        return f"{str(self.m_fittedIdx)}.{str(self.m_tyreSetData[self.m_fittedIdx].m_actualTyreCompound)}"

    def getTyreSetKey(self, index) -> Optional[str]:
        """Key containing tyre set ID and actual compound name for the given index

        Arguments:
            index (int): Tyre set index

        Returns:
            Optional[str]: Key if index is valid, else None
        """

        if 0 <= index < len(self.m_tyreSetData):
            return f"{str(index)}.{str(self.m_tyreSetData[index].m_actualTyreCompound)}"
        return None

    def __eq__(self, other: "PacketTyreSetsData") -> bool:
        """Check if two objects are equal

        Args:
            other (PacketTyreSetsData): The object to compare to

        Returns:
            bool: True if the objects are equal, False otherwise
        """

        return (
            self.m_header == other.m_header and
            self.m_carIdx == other.m_carIdx and
            self.m_tyreSetData == other.m_tyreSetData and
            self.m_fittedIdx == other.m_fittedIdx and
            self.getFittedTyreSetKey() == other.getFittedTyreSetKey()
        )

    def __ne__(self, other: "PacketTyreSetsData") -> bool:
        """Check if two objects are not equal

        Args:
            other (PacketTyreSetsData): The object to compare to

        Returns:
            bool: True if the objects are not equal, False otherwise
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """Serialize the PacketTyreSetsData object to bytes based on PACKET_FORMAT.

        Returns:
            bytes: Serialized bytes representation of the PacketTyreSetsData object
        """

        raw_bytes = self.m_header.to_bytes() + struct.pack("<B", self.m_carIdx)
        raw_bytes += b"".join([tyre_set_data.to_bytes() for tyre_set_data in self.m_tyreSetData])
        raw_bytes += struct.pack("<B", self.m_fittedIdx)
        return raw_bytes

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    car_index: int,
                    tyre_set_data: List[TyreSetData],
                    fitted_index: int) -> "PacketTyreSetsData":
        """Create a PacketTyreSetsData object from values.

        Args:
            header (PacketHeader): The header of the telemetry packet
            car_index (int): The index of the car
            tyre_set_data (List[TyreSetData]): List of TyreSetData objects containing data for all cars on track
            fitted_index (int): The index of the fitted tyre set

        Returns:
            PacketTyreSetsData: The created PacketTyreSetsData object
        """

        return cls(header, (
            struct.pack("<B", car_index) +
            b"".join([tyre_set_data.to_bytes() for tyre_set_data in tyre_set_data]) +
            struct.pack("<B", fitted_index)
        ))

    @property
    def m_fitted_tyre_set(self) -> Optional[TyreSetData]:
        """Get the fitted tyre set data.

        Returns:
            TyreSetData: The fitted tyre set data, else None.
        """
        if not (0 <= self.m_fittedIdx < len(self.m_tyreSetData)):
            return None
        return self.m_tyreSetData[self.m_fittedIdx]