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
from typing import Dict, Any, List
from .common import _split_list, PacketHeader, Platform, Nationality, TeamID23, TeamID24, TelemetrySetting

# --------------------- CLASS DEFINITIONS --------------------------------------

class ParticipantData:
    """
    A class representing participant data in a racing simulation.

    Attributes:
        m_aiControlled (bool): Whether the vehicle is AI (True) or Human (False) controlled.
        m_driverId (int): Driver id - see appendix, 255 if network human.
        networkId (int): Network id - unique identifier for network players.
        m_teamId (TeamID): See TeamID enumeration
        m_myTeam (bool): My team flag - True = My Team, False = otherwise.
        m_raceNumber (int): Race number of the car.
        m_nationality (int): Nationality of the driver.
        m_name (str): Name of participant in UTF-8 format - null terminated.
                      Will be truncated with … (U+2026) if too long.
        m_yourTelemetry (TelemetrySetting): The player's UDP setting (see TelemetrySetting enumeration)
        m_showOnlineNames (bool): The player's show online names setting, False = off, True = on.
        m_platform (Platform): Gaming platform (see Platform enumeration).

        Note:
            The m_platform attribute is an instance of Platform.
    """

    PACKET_FORMAT_23 = ("<"
        "B" # uint8      m_aiControlled;      // Whether the vehicle is AI (1) or Human (0) controlled
        "B" # uint8      m_driverId;       // Driver id - see appendix, 255 if network human
        "B" # uint8      m_networkId;       // Network id – unique identifier for network players
        "B" # uint8      m_teamId;            // Team id - see appendix
        "B" # uint8      m_myTeam;            // My team flag – 1 = My Team, 0 = otherwise
        "B" # uint8      m_raceNumber;        // Race number of the car
        "B" # uint8      m_nationality;       // Nationality of the driver
        "48s" # char     m_name[48];          // Name of participant in UTF-8 format – null terminated
                                        # // Will be truncated with … (U+2026) if too long
        "B" # uint8      m_yourTelemetry;     // The player's UDP setting, 0 = restricted, 1 = public
        "B" # uint8      m_showOnlineNames;   // The player's show online names setting, 0 = off, 1 = on
        "B" # uint8      m_platform;          // 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
    )
    PACKET_LEN_23 = struct.calcsize(PACKET_FORMAT_23)

    PACKET_FORMAT_24 = ("<"
        "B" # uint8      m_aiControlled;      // Whether the vehicle is AI (1) or Human (0) controlled
        "B" # uint8      m_driverId;       // Driver id - see appendix, 255 if network human
        "B" # uint8      m_networkId;       // Network id – unique identifier for network players
        "B" # uint8      m_teamId;            // Team id - see appendix
        "B" # uint8      m_myTeam;            // My team flag – 1 = My Team, 0 = otherwise
        "B" # uint8      m_raceNumber;        // Race number of the car
        "B" # uint8      m_nationality;       // Nationality of the driver
        "48s" # char     m_name[48];          // Name of participant in UTF-8 format – null terminated
                                        # // Will be truncated with … (U+2026) if too long
        "B" # uint8      m_yourTelemetry;     // The player's UDP setting, 0 = restricted, 1 = public
        "B" # uint8      m_showOnlineNames;   // The player's show online names setting, 0 = off, 1 = on
        "H" # uint16     m_techLevel          // F1 World tech level
        "B" # uint8      m_platform;          // 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
    )
    PACKET_LEN_24 = struct.calcsize(PACKET_FORMAT_24)

    def __init__(self, data: bytes, game_year: int) -> None:
        """
        Initializes a ParticipantData object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.
            game_year (int): Year of the game.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        if game_year == 23:
            unpacked_data = struct.unpack(self.PACKET_FORMAT_23, data)
            (
                self.m_aiControlled,
                self.m_driverId,
                self.networkId,
                self.m_teamId,
                self.m_myTeam,
                self.m_raceNumber,
                self.m_nationality,
                self.m_name,
                self.m_yourTelemetry,
                self.m_showOnlineNames,
                self.m_platform
            ) = unpacked_data
            self.m_techLevel = 0
        else:
            unpacked_data = struct.unpack(self.PACKET_FORMAT_24, data)
            (
                self.m_aiControlled,
                self.m_driverId,
                self.networkId,
                self.m_teamId,
                self.m_myTeam,
                self.m_raceNumber,
                self.m_nationality,
                self.m_name,
                self.m_yourTelemetry,
                self.m_showOnlineNames,
                self.m_techLevel,
                self.m_platform
            ) = unpacked_data

        self.m_name = self.m_name.decode('utf-8', errors='replace').rstrip('\x00')
        if Platform.isValid(self.m_platform):
            self.m_platform = Platform(self.m_platform)
        if game_year == 23 and TeamID23.isValid(self.m_teamId):
            self.m_teamId = TeamID23(self.m_teamId)
        elif TeamID24.isValid(self.m_teamId):
            self.m_teamId = TeamID24(self.m_teamId)
        if TelemetrySetting.isValid(self.m_yourTelemetry):
            self.m_yourTelemetry = TelemetrySetting(self.m_yourTelemetry)
        if Nationality.isValid(self.m_nationality):
            self.m_nationality = Nationality(self.m_nationality)
        self.m_showOnlineNames = bool(self.m_showOnlineNames)
        self.m_myTeam = bool(self.m_myTeam)
        self.m_aiControlled = bool(self.m_aiControlled)

    def __str__(self):
        """
        Returns a string representation of the ParticipantData object.

        Returns:
            str: String representation of the object.
        """
        return (
            f"ParticipantData("
            f"m_aiControlled={self.m_aiControlled}, "
            f"m_driverId={self.m_driverId}, "
            f"networkId={self.networkId}, "
            f"m_teamId={self.m_teamId}, "
            f"m_myTeam={str(self.m_myTeam)}, "
            f"m_raceNumber={self.m_raceNumber}, "
            f"m_nationality={self.m_nationality}, "
            f"m_name={self.m_name}, "
            f"m_yourTelemetry={str(self.m_yourTelemetry)}, "
            f"m_showOnlineNames={str(self.m_showOnlineNames)}, "
            f"m_techLevel={str(self.m_techLevel)}, "
            f"m_platform={str(self.m_platform)})"
        )

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the ParticipantData instance to a JSON-compatible dictionary.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representing the ParticipantData instance.
        """

        return {
            "ai-controlled": self.m_aiControlled,
            "driver-id": self.m_driverId,
            "network-id": self.networkId,
            "team-id": str(self.m_teamId),
            "my-team": self.m_myTeam,
            "race-number": self.m_raceNumber,
            "nationality": str(self.m_nationality),
            "name": self.m_name,
            "telemetry-setting": str(self.m_yourTelemetry),
            "show-online-names": self.m_showOnlineNames,
            "tech-level" : self.m_techLevel,
            "platform": str(self.m_platform)
        }

class PacketParticipantsData:
    """
    A class representing participant data in a racing simulation.

    Attributes:
        max_participants (int): Maximum number of participants (cars) in the packet.
        m_header (PacketHeader): Header containing general information about the packet.
        m_numActiveCars (int): Number of active cars in the data - should match the number of cars on HUD.
        m_participants (List[ParticipantData]): List of ParticipantData objects representing information
            about each participant in the race.

            Note:
                The length of m_participants should not exceed max_participants.
    """

    max_participants = 22
    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """
        Initializes a PacketParticipantsData object by unpacking the provided binary data.

        Parameters:
            header (PacketHeader): Header containing general information about the packet.
            packet (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """

        self.m_header: PacketHeader = header         # PacketHeader
        self.m_numActiveCars: int = struct.unpack("<B", packet[0:1])[0]
        self.m_participants: List[ParticipantData] = []            # ParticipantData[22]

        packet_len = ParticipantData.PACKET_LEN_23 if (header.m_gameYear == 23) else ParticipantData.PACKET_LEN_24
        for participant_data_raw in _split_list(packet[1:], packet_len):
            self.m_participants.append(ParticipantData(participant_data_raw, header.m_gameYear))

        # Trim the list
        self.m_participants = self.m_participants[:self.m_numActiveCars]

    def __str__(self) -> str:
        """
        Returns a string representation of the PacketParticipantsData object.

        Returns:
            str: String representation of the object.
        """

        participants_str = ", ".join(str(participant) for participant in self.m_participants[self.m_numActiveCars:])
        return (
            f"PacketParticipantsData("
            f"Header: {str(self.m_header)}, "
            f"Number of Active Cars: {self.m_numActiveCars}, "
            f"Participants: [{participants_str}])"
        )

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketParticipantsData instance to a JSON-compatible dictionary.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON-compatible dictionary representing the PacketParticipantsData instance.
        """

        json_data = {
            "num-active-cars": self.m_numActiveCars,
            "participants": [participant.toJSON() for participant in self.m_participants]
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data
