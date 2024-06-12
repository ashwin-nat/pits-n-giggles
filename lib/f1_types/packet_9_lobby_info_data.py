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
from typing import Dict, List, Any
from enum import Enum
from .common import _split_list, PacketHeader, F1PacketType, TeamID, Nationality, Platform, TelemetrySetting

# --------------------- CLASS DEFINITIONS --------------------------------------

class PacketLobbyInfoData:
    """
    Class representing the packet for lobby information data.

    Attributes:
        m_header (PacketHeader): Header information.
        m_numPlayers (int): Number of players in the lobby.
        m_lobbyPlayers (List[LobbyInfoData]): List of lobby information data for each player.

    Note:
        The class is designed to parse and represent the lobby information data packet.
    """

    def __init__(self, header: PacketHeader, packet: bytes) -> None:
        """
        Initializes PacketLobbyInfoData with raw data.

        Args:
            header (PacketHeader): Header information for the packet.
            packet (bytes): Raw data representing the packet for lobby information data.
        """

        self.m_header: PacketHeader = header
        self.m_numPlayers: int = struct.unpack("<B", packet[:1])[0]
        self.m_lobbyPlayers: List[LobbyInfoData] = []
        if header.m_gameYear == 23:
            packet_len = LobbyInfoData.PACKET_LEN_23
        else: # 24
            packet_len = LobbyInfoData.PACKET_LEN_24

        for lobby_info_per_player_raw_data in _split_list(packet[1:], packet_len):
            self.m_lobbyPlayers.append(LobbyInfoData(lobby_info_per_player_raw_data, header.m_gameYear))

        # Trim the list
        self.m_lobbyPlayers = self.m_lobbyPlayers[:self.m_numPlayers]

    def toJSON(self, include_header: bool=False) -> Dict[str, Any]:
        """
        Convert the PacketLobbyInfoData instance to a JSON-compatible dictionary with kebab-case keys.

        Arguments:
            - include_header - Whether the header dump must be included in the JSON

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the PacketLobbyInfoData instance.
        """

        json_data = {
            "num-players": self.m_numPlayers,
            "lobby-players": [player.toJSON() for player in self.m_lobbyPlayers[:self.m_numPlayers]],
        }
        if include_header:
            json_data["header"] = self.m_header.toJSON()
        return json_data

class LobbyInfoData:
    """
    Class representing lobby information data for a player.

    Attributes:
        m_aiControlled (bool): Flag indicating whether the car is AI-controlled.
        m_teamId (uint8): Team ID of the player.
        m_nationality (uint8): Nationality of the player.
        m_platform (uint8): Platform on which the player is participating.
        m_name (str): Name of the player.
        m_carNumber (uint8): Car number of the player.
        m_readyStatus (uint8): Ready status of the player.

    Note:
        The class is designed to parse and represent lobby information data for a player.
    """

    PACKET_FORMAT_23 = ("<"
        "B" # uint8     m_aiControlled;      // Whether the vehicle is AI (1) or Human (0) controlled
        "B" # uint8     m_teamId;            // Team id - see appendix (255 if no team currently selected)
        "B" # uint8     m_nationality;       // Nationality of the driver
        "B" # uint8     m_platform;          // 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
        "48s" # char    m_name[48];          // Name of participant in UTF-8 format – null terminated
                                        #    // Will be truncated with ... (U+2026) if too long
        "B" # uint8     m_carNumber;         // Car number of the player
        "B" # uint8     m_readyStatus;       // 0 = not ready, 1 = ready, 2 = spectating
    )
    PACKET_LEN_23 = struct.calcsize(PACKET_FORMAT_23)

    PACKET_FORMAT_24 = ("<"
        "B" # uint8     m_aiControlled;      // Whether the vehicle is AI (1) or Human (0) controlled
        "B" # uint8     m_teamId;            // Team id - see appendix (255 if no team currently selected)
        "B" # uint8     m_nationality;       // Nationality of the driver
        "B" # uint8     m_platform;          // 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
        "48s" # char    m_name[48];	         // Name of participant in UTF-8 format – null terminated
                                    #        // Will be truncated with ... (U+2026) if too long
        "B" # uint8     m_carNumber;         // Car number of the player
        "B" # uint8     m_yourTelemetry;     // The player's UDP setting, 0 = restricted, 1 = public
        "B" # uint8     m_showOnlineNames;   // The player's show online names setting, 0 = off, 1 = on
        "H" # uint16    m_techLevel;         // F1 World tech level
        "B" # uint8     m_readyStatus;       // 0 = not ready, 1 = ready, 2 = spectating
    )
    PACKET_LEN_24 = struct.calcsize(PACKET_FORMAT_24)

    class ReadyStatus(Enum):
        """
        ENUM class for the marshal zone flag status
        """

        NOT_READY = 0
        READY = 1
        SPECTATING = 2

        @staticmethod
        def isValid(ready_status_code: int):
            """Check if the given packet type is valid.

            Args:
                ready_status_code (int): The ready status code to be validated.
                    Also supports type ReadyStatus. Returns true in this case

            Returns:
                bool: true if valid
            """
            if isinstance(ready_status_code, LobbyInfoData.ReadyStatus):
                return True  # It's already an instance of LobbyInfoData.ReadyStatus
            return any(ready_status_code == member.value for member in LobbyInfoData.ReadyStatus)

        def __str__(self):
            if F1PacketType.isValid(self.value):
                return self.name
            return 'Marshal Zone Flag type ' + str(self.value)

    def __init__(self, data: bytes, game_year: int) -> None:
        """
        Initializes LobbyInfoData with raw data.

        Args:
            data (bytes): Raw data representing lobby information for a player.
            game_year (int): Year of the game.
        """

        if game_year == 23:
            (
                self.m_aiControlled,
                self.m_teamId,
                self.m_nationality,
                self.m_platform,
                self.m_name,
                self.m_carNumber,
                self.m_readyStatus,
            ) = struct.unpack(self.PACKET_FORMAT_23, data)
            self.m_yourTelemetry = TelemetrySetting.PUBLIC
            self.m_showOnlineNames = True
            self.m_techLevel = 0
        else:
            (
                self.m_aiControlled,
                self.m_teamId,
                self.m_nationality,
                self.m_platform,
                self.m_name,
                self.m_carNumber,
                self.m_yourTelemetry,
                self.m_showOnlineNames,
                self.m_techLevel,
                self.m_readyStatus,
            ) = struct.unpack(self.PACKET_FORMAT_24, data)
            if TelemetrySetting.isValid(self.m_yourTelemetry):
                self.m_yourTelemetry = TelemetrySetting(self.m_yourTelemetry)

        self.m_name = self.m_name.decode('utf-8', errors='replace').rstrip('\x00')

        if TeamID.isValid(self.m_teamId):
            self.m_teamId = TeamID(self.m_teamId)
        if Nationality.isValid(self.m_nationality):
            self.m_nationality = Nationality(self.m_nationality)
        if Platform.isValid(self.m_platform):
            self.m_platform = Platform(self.m_platform)
        if LobbyInfoData.ReadyStatus.isValid(self.m_readyStatus):
            self.m_readyStatus = LobbyInfoData.ReadyStatus(self.m_readyStatus)
        self.m_aiControlled = bool(self.m_aiControlled)

    def toJSON(self) -> Dict[str, Any]:
        """
        Convert the LobbyInfoData instance to a JSON-compatible dictionary with kebab-case keys.

        Returns:
            Dict[str, Any]: JSON-compatible dictionary with kebab-case keys representing the LobbyInfoData instance.
        """

        return {
            "ai-controlled": self.m_aiControlled,
            "team-id": self.m_teamId,
            "nationality": self.m_nationality,
            "platform": self.m_platform,
            "name": self.m_name,
            "car-number": self.m_carNumber,
            "your-telemetry": str(self.m_yourTelemetry),
            "show-online-names": self.m_showOnlineNames,
            "tech-level": self.m_techLevel,
            "ready-status": self.m_readyStatus,
        }
