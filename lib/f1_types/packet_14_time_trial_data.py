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
from typing import Dict, Any
from .common import PacketHeader, TeamID, TractionControlAssistMode, _extract_sublist, F1Utils

# --------------------- CLASS DEFINITIONS --------------------------------------

class TimeTrialDataSet:
    """The class representing the time trial data for a single car.

    Attributes:
        m_carIdx (uint8): Index of the car this data relates to
        m_teamId (TeamID): Team id - see appendix
        m_lapTimeInMS (uint32): Lap time in milliseconds
        m_sector1TimeInMS (uint32): Sector 1 time in milliseconds
        m_sector2TimeInMS (uint32): Sector 2 time in milliseconds
        m_sector3TimeInMS (uint32): Sector 3 time in milliseconds
        m_tractionControl (TractionControlAssistMode): Refer TractionControlAssistMode enumeration
        m_gearboxAssist (int): 1 = manual, 2 = manual & suggested gear, 3 = auto
        m_antiLockBrakes (bool): 0 (off) - 1 (on)
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
        "B" # uint8     m_tractionControl;          // 0 = off, 1 = medium, 2 = full
        "B" # uint8     m_gearboxAssist;            // 1 = manual, 2 = manual & suggested gear, 3 = auto
        "B" # uint8     m_antiLockBrakes;           // 0 (off) - 1 (on)
        "B" # uint8     m_equalCarPerformance;      // 0 = Realistic, 1 = Equal
        "B" # uint8     m_customSetup;              // 0 = No, 1 = Yes
        "B" # uint8     m_valid;                    // 0 = invalid, 1 = valid
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    def __init__(self, data: bytes) -> None:
        """
        Initializes a TimeTrialDataSet object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

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
            self.m_gearboxAssist, # TODO: make enum
            self.m_antiLockBrakes,
            self.m_equalCarPerformance,
            self.m_customSetup,
            self.m_isValid,
        ) = unpacked_data

        if TeamID.isValid(self.m_teamId):
            self.m_teamID = TeamID(self.m_teamID)
        if TractionControlAssistMode.isValid(self.m_tractionControl):
            self.m_tractionControl = TractionControlAssistMode(self.m_tractionControl)
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
            "traction-control": str(self.m_tractionControl),
            "gearbox-assist": str(self.m_gearboxAssist),
            "anti-lock-brakes": self.m_antiLockBrakes,
            "equal-car-performance": self.m_equalCarPerformance,
            "custom-setup": self.m_customSetup,
            "is-valid": self.m_isValid
        }

class PacketTimeTrialData:
    """Class representing the Time Trial Data Packet.

    Attributes:
        - m_header (PacketHeader): The packet header
        - m_playerSessionBestDataSet (TimeTrialDataSet): The player session best data set
        - m_personalBestDataSet (TimeTrialDataSet): The personal best data set
        - m_rivalDataSet (TimeTrialDataSet): The rival data set

    """

    def __init__(self, data: bytes, header: PacketHeader) -> None:
        """
        Initializes a PacketTimeTrialData object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """

        self.m_header = header

        # First, the Player session best data set
        bytes_so_far = 0
        raw_data = _extract_sublist(data, 0, TimeTrialDataSet.PACKET_LEN)
        bytes_so_far += TimeTrialDataSet.PACKET_LEN
        self.m_playerSessionBestDataSet = TimeTrialDataSet(raw_data)

        # Next, the personal best data set
        raw_data = _extract_sublist(data, bytes_so_far, TimeTrialDataSet.PACKET_LEN)
        bytes_so_far += TimeTrialDataSet.PACKET_LEN
        self.m_personalBestDataSet = TimeTrialDataSet(raw_data)

        # Finally, the rival data set
        raw_data = _extract_sublist(data, bytes_so_far, TimeTrialDataSet.PACKET_LEN)
        bytes_so_far += TimeTrialDataSet.PACKET_LEN
        self.m_rivalSessionBestDataSet = TimeTrialDataSet(raw_data)

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
