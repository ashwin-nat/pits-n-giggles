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
from typing import Any, Dict, Union

from .common import (F1Utils, GearboxAssistMode, PacketHeader, TeamID24, TeamID25,
                     TractionControlAssistMode)

# --------------------- CLASS DEFINITIONS --------------------------------------

class TimeTrialDataSet:
    """The class representing the time trial data for a single car.

    Attributes:
        m_carIdx (uint8): Index of the car this data relates to
        m_teamId (TeamID24): Team id - see appendix
        m_lapTimeInMS (uint32): Lap time in milliseconds
        m_sector1TimeInMS (uint32): Sector 1 time in milliseconds
        m_sector2TimeInMS (uint32): Sector 2 time in milliseconds
        m_sector3TimeInMS (uint32): Sector 3 time in milliseconds
        m_tractionControl (bool): false = assist off, true = assist on
        m_gearboxAssist (bool): false = assist off, true = assist on
        m_antiLockBrakes (bool): false = assist off, true = assist on
        m_equalCarPerformance (bool): 0 = Realistic, 1 = Equal
        m_customSetup (bool): 0 = No, 1 = Yes
        m_valid (bool): 0 = invalid, 1 = valid
    """
    PACKET_FORMAT = ("<"
        "B" # uint8     m_carIdx;                   // Index of the car this data relates to
        "B" # uint8     m_teamId;                   // Team id - see appendix
        "I" # uint32    m_lapTimeInMS;              // Lap time in milliseconds
        "I" # uint32    m_sector1TimeInMS;          // Sector 1 time in milliseconds
        "I" # uint32    m_sector2TimeInMS;          // Sector 2 time in milliseconds
        "I" # uint32    m_sector3TimeInMS;          // Sector 3 time in milliseconds
        "B" # uint8     m_tractionControl;          // 0 = assist off, 1 = assist on
        "B" # uint8     m_gearboxAssist;            // 0 = assist off, 1 = assist on
        "B" # uint8     m_antiLockBrakes;           // 0 = assist off, 1 = assist on
        "B" # uint8     m_equalCarPerformance;      // 0 = Realistic, 1 = Equal
        "B" # uint8     m_customSetup;              // 0 = No, 1 = Yes
        "B" # uint8     m_valid;                    // 0 = invalid, 1 = valid
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    def __init__(self, data: bytes, packet_format: int) -> None:
        """
        Initializes a TimeTrialDataSet object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.
            packet_format (int): Packet format version

        Raises:
            struct.error: If the binary data does not match the expected format.
        """

        unpacked_data = struct.unpack(self.PACKET_FORMAT, data)
        (
            self.m_carIdx,
            self.m_teamId,
            self.m_lapTimeInMS,
            self.m_sector1TimeInMS,
            self.m_sector2TimeInMS,
            self.m_sector3TimeInMS,
            self.m_tractionControl,
            self.m_gearboxAssist,
            self.m_antiLockBrakes,
            self.m_equalCarPerformance,
            self.m_customSetup,
            self.m_isValid,
        ) = unpacked_data

        # No ned to check game year, since this packet type is not available in F1 23
        if packet_format < 2025 and TeamID24.isValid(self.m_teamId):
                self.m_teamId = TeamID24(self.m_teamId)
        elif TeamID25.isValid(self.m_teamId):
            self.m_teamId = TeamID25(self.m_teamId)
        self.m_tractionControl = bool(self.m_tractionControl)
        self.m_gearboxAssist = bool(self.m_gearboxAssist)
        self.m_antiLockBrakes = bool(self.m_antiLockBrakes)
        self.m_equalCarPerformance = bool(self.m_equalCarPerformance)
        self.m_customSetup = bool(self.m_customSetup)
        self.m_isValid = bool(self.m_isValid)

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON dump of this object

        Returns:
            Dict[str, Any]: The JSON dict
        """

        return {
            "car-index": self.m_carIdx,
            "team": str(self.m_teamId),
            "lap-time-ms": self.m_lapTimeInMS,
            "lap-time-str": F1Utils.getLapTimeStr(self.m_lapTimeInMS),
            "sector-1-time-ms": self.m_sector1TimeInMS,
            "sector-1-time-str": F1Utils.getLapTimeStr(self.m_sector1TimeInMS),
            "sector-2-time-in-ms": self.m_sector2TimeInMS,
            "sector-2-time-str": F1Utils.getLapTimeStr(self.m_sector2TimeInMS),
            "sector3-time-in-ms": self.m_sector3TimeInMS,
            "sector-3-time-str": F1Utils.getLapTimeStr(self.m_sector3TimeInMS),
            "traction-control": self.m_tractionControl,
            "gearbox-assist": self.m_gearboxAssist,
            "anti-lock-brakes": self.m_antiLockBrakes,
            "equal-car-performance": self.m_equalCarPerformance,
            "custom-setup": self.m_customSetup,
            "is-valid": self.m_isValid
        }

    def __eq__(self, other: "TimeTrialDataSet") -> bool:
        """Check if two TimeTrialDataSets are equal

        Args:
            other (TimeTrialDataSet): The other TimeTrialDataSet

        Returns:
            bool: True if the TimeTrialDataSets are equal, False otherwise
        """

        return (
            self.m_carIdx == other.m_carIdx and
            self.m_teamId == other.m_teamId and
            self.m_lapTimeInMS == other.m_lapTimeInMS and
            self.m_sector1TimeInMS == other.m_sector1TimeInMS and
            self.m_sector2TimeInMS == other.m_sector2TimeInMS and
            self.m_sector3TimeInMS == other.m_sector3TimeInMS and
            self.m_tractionControl == other.m_tractionControl and
            self.m_gearboxAssist == other.m_gearboxAssist and
            self.m_antiLockBrakes == other.m_antiLockBrakes and
            self.m_equalCarPerformance == other.m_equalCarPerformance and
            self.m_customSetup == other.m_customSetup and
            self.m_isValid == other.m_isValid
        )

    def __ne__(self, other: "TimeTrialDataSet") -> bool:
        """Check if two TimeTrialDataSets are not equal

        Args:
            other (TimeTrialDataSet): The other TimeTrialDataSet

        Returns:
            bool: True if the TimeTrialDataSets are not equal, False otherwise
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """Serialize the TimeTrialDataSet object to bytes based on PACKET_FORMAT.

        Returns:
            bytes: The serialized TimeTrialDataSet object
        """

        return struct.pack(self.PACKET_FORMAT,
            self.m_carIdx,
            self.m_teamId.value,
            self.m_lapTimeInMS,
            self.m_sector1TimeInMS,
            self.m_sector2TimeInMS,
            self.m_sector3TimeInMS,
            self.m_tractionControl,
            self.m_gearboxAssist,
            self.m_antiLockBrakes,
            self.m_equalCarPerformance,
            self.m_customSetup,
            self.m_isValid,
        )

    @classmethod
    def from_values(cls,
                    game_year: int,
                    car_index: int,
                    team_id: Union[TeamID24, TeamID25],
                    lap_time_in_ms: int,
                    sector1_time_in_ms: int,
                    sector2_time_in_ms: int,
                    sector3_time_in_ms: int,
                    traction_control: bool,
                    gearbox_assist: bool,
                    anti_lock_brakes: bool,
                    equal_car_performance: bool,
                    custom_setup: bool,
                    is_valid: bool) -> "TimeTrialDataSet":
        """Create a new TimeTrialDataSet object from the provided values

        Args:
            game_year (int): The game year
            car_index (int): The car index
            team_id (TeamID24 | TeamID25): The team id
            lap_time_in_ms (int): The lap time in milliseconds
            sector1_time_in_ms (int): The sector 1 time in milliseconds
            sector2_time_in_ms (int): The sector 2 time in milliseconds
            sector3_time_in_ms (int): The sector 3 time in milliseconds
            traction_control (TractionControlAssistMode): The traction control assist mode
            gearbox_assist (GearboxAssistMode): The gearbox assist mode
            anti_lock_brakes (bool): Whether or not the anti-lock brakes are enabled
            equal_car_performance (bool): Whether or not the equal car performance mode is enabled
            custom_setup (bool): Whether or not the custom setup mode is enabled
            is_valid (bool): Whether or not the data is valid

        Returns:
            TimeTrialDataSet: A new TimeTrialDataSet object
        """

        return cls(
            struct.pack(cls.PACKET_FORMAT,
                car_index,
                team_id.value,
                lap_time_in_ms,
                sector1_time_in_ms,
                sector2_time_in_ms,
                sector3_time_in_ms,
                traction_control,
                gearbox_assist,
                anti_lock_brakes,
                equal_car_performance,
                custom_setup,
                is_valid
            ), game_year
        )

class PacketTimeTrialData:
    """Class representing the Time Trial Data Packet.

    Attributes:
        - m_header (PacketHeader): The packet header
        - m_playerSessionBestDataSet (TimeTrialDataSet): The player session best data set
        - m_personalBestDataSet (TimeTrialDataSet): The personal best data set
        - m_rivalDataSet (TimeTrialDataSet): The rival data set

    """

    def __init__(self, header: PacketHeader, data: bytes) -> None:
        """
        Initializes a PacketTimeTrialData object by unpacking the provided binary data.

        Parameters:
            header (PacketHeader): The packet header
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """

        self.m_header = header

        # First, the Player session best data set
        bytes_so_far = 0
        raw_data = data[:bytes_so_far + TimeTrialDataSet.PACKET_LEN]
        bytes_so_far += TimeTrialDataSet.PACKET_LEN
        self.m_playerSessionBestDataSet = TimeTrialDataSet(raw_data, header.m_packetFormat)

        # Next, the personal best data set
        raw_data = data[bytes_so_far:bytes_so_far + TimeTrialDataSet.PACKET_LEN]
        bytes_so_far += TimeTrialDataSet.PACKET_LEN
        self.m_personalBestDataSet = TimeTrialDataSet(raw_data, header.m_packetFormat)

        # Finally, the rival data set
        raw_data = data[bytes_so_far:bytes_so_far + TimeTrialDataSet.PACKET_LEN]
        bytes_so_far += TimeTrialDataSet.PACKET_LEN
        self.m_rivalSessionBestDataSet = TimeTrialDataSet(raw_data, header.m_packetFormat)

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """Get the JSON dump of this object

        Args:
            include_header (bool, optional): Whether the packet header should be included. Defaults to False.

        Returns:
            Dict[str, Any]: The JSON dict
        """
        json_data = {
            "player-session-best-data-set": self.m_playerSessionBestDataSet.toJSON(),
            "personal-best-data-set": self.m_personalBestDataSet.toJSON(),
            "rival-session-best-data-set": self.m_rivalSessionBestDataSet.toJSON()
        }

        if include_header:
            json_data["header"] = self.m_header.toJSON()

        return json_data

    def __eq__(self, other: "PacketTimeTrialData") -> bool:
        """Check if two PacketTimeTrialData objects are equal

        Args:
            other (PacketTimeTrialData): The other PacketTimeTrialData object to compare with

        Returns:
            bool: True if the PacketTimeTrialData objects are equal, False otherwise
        """

        return (
            self.m_header == other.m_header and
            self.m_playerSessionBestDataSet == other.m_playerSessionBestDataSet and
            self.m_personalBestDataSet == other.m_personalBestDataSet and
            self.m_rivalSessionBestDataSet == other.m_rivalSessionBestDataSet
        )

    def __ne__(self, other: "PacketTimeTrialData") -> bool:
        """Check if two PacketTimeTrialData objects are not equal

        Args:
            other (PacketTimeTrialData): The other PacketTimeTrialData object to compare with

        Returns:
            bool: True if the PacketTimeTrialData objects are not equal, False otherwise
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """Get the binary representation of this object

        Returns:
            bytes: The binary representation of this object
        """

        return (
            self.m_header.to_bytes() +
            self.m_playerSessionBestDataSet.to_bytes() +
            self.m_personalBestDataSet.to_bytes() +
            self.m_rivalSessionBestDataSet.to_bytes()
        )

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    player_session_best_data_set: TimeTrialDataSet,
                    personal_best_data_set: TimeTrialDataSet,
                    rival_session_best_data_set: TimeTrialDataSet) -> "PacketTimeTrialData":
        """Create a new PacketTimeTrialData object from the provided values

        Args:
            header (PacketHeader): The packet header
            player_session_best_data_set (TimeTrialDataSet): The player session best data set
            personal_best_data_set (TimeTrialDataSet): The personal best data set
            rival_session_best_data_set (TimeTrialDataSet): The rival data set

        Returns:
            PacketTimeTrialData: A new PacketTimeTrialData object
        """

        return cls(
            header,
            player_session_best_data_set.to_bytes() +
            personal_best_data_set.to_bytes() +
            rival_session_best_data_set.to_bytes()
        )