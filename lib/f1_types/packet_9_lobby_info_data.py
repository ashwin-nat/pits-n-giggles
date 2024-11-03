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
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from .common import _split_list, PacketHeader, F1PacketType, TeamID23, TeamID24, Nationality, Platform, TelemetrySetting

# --------------------- CLASS DEFINITIONS --------------------------------------

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
            return f'Marshal Zone Flag type {str(self.value)}'

    def __init__(self, data: bytes, packet_format: int) -> None:
        """
        Initializes LobbyInfoData with raw data.

        Args:
            data (bytes): Raw data representing lobby information for a player.
            packet_format (int): Packet format
        """

        self.packet_format = packet_format
        if packet_format == 2023:
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

        if packet_format == 2023 and TeamID23.isValid(self.m_teamId):
            self.m_teamId = TeamID23(self.m_teamId)
        elif TeamID24.isValid(self.m_teamId):
            self.m_teamId = TeamID24(self.m_teamId)
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
            "team-id": str(self.m_teamId),
            "nationality": str(self.m_nationality),
            "platform": str(self.m_platform),
            "name": self.m_name,
            "car-number": self.m_carNumber,
            "your-telemetry": str(self.m_yourTelemetry),
            "show-online-names": self.m_showOnlineNames,
            "tech-level": self.m_techLevel,
            "ready-status": str(self.m_readyStatus),
        }

    def __eq__(self, other: "LobbyInfoData") -> bool:
        """Check if two objects are equal

        Args:
            other (LobbyInfoData): The object to compare to

        Returns:
            bool: True if the objects are equal, False otherwise
        """

        return (
            self.packet_format == other.packet_format and
            self.m_aiControlled == other.m_aiControlled and
            self.m_teamId == other.m_teamId and
            self.m_nationality == other.m_nationality and
            self.m_platform == other.m_platform and
            self.m_name == other.m_name and
            self.m_carNumber == other.m_carNumber and
            self.m_yourTelemetry == other.m_yourTelemetry and
            self.m_showOnlineNames == other.m_showOnlineNames and
            self.m_techLevel == other.m_techLevel and
            self.m_readyStatus == other.m_readyStatus
        )

    def __ne__(self, other: "LobbyInfoData") -> bool:
        """Check if two objects are not equal

        Args:
            other (LobbyInfoData): The object to compare to

        Returns:
            bool: True if the objects are not equal, False otherwise
        """

        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Convert the LobbyInfoData instance to raw data.

        Returns:
            bytes: Raw data representing the LobbyInfoData instance.
        """

        if self.packet_format == 2023:
            return struct.pack(self.PACKET_FORMAT_23,
                self.m_aiControlled,
                self.m_teamId.value,
                self.m_nationality.value,
                self.m_platform.value,
                self.m_name.encode('utf-8'),
                self.m_carNumber,
                self.m_readyStatus.value,
            )
        if self.packet_format == 2024:
            return struct.pack(self.PACKET_FORMAT_24,
                self.m_aiControlled,
                self.m_teamId.value,
                self.m_nationality.value,
                self.m_platform.value,
                self.m_name.encode('utf-8'),
                self.m_carNumber,
                self.m_yourTelemetry.value,
                self.m_showOnlineNames,
                self.m_techLevel,
                self.m_readyStatus.value,
            )

        raise NotImplementedError(f"Unsupported game year: {self.packet_format}")

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    ai_controlled: bool,
                    team_id: Union[TeamID23, TeamID24],
                    nationality: Nationality,
                    platform: Platform,
                    name: str,
                    car_number: int,
                    your_telemetry: Optional[TelemetrySetting] = TelemetrySetting.PUBLIC,
                    show_online_names: Optional[bool] = True,
                    tech_level: Optional[int] = 0,
                    ready_status: Optional[ReadyStatus] = ReadyStatus.READY) -> "LobbyInfoData":
        """
        Create a LobbyInfoData object from values.

        Args:
            header (PacketHeader): The header of the telemetry packet.
            ai_controlled (bool): Whether the car is controlled by an AI car.
            team_id (TeamID23): Team ID of the player.
            nationality (Nationality): Nationality of the player.
            platform (Platform): Platform on which the player is participating.
            name (str): Name of the player.
            car_number (int): Car number of the player.
            your_telemetry (TelemetrySetting): Your telemetry setting.
            show_online_names (bool): Whether to show online player names.
            tech_level (int): Tech level of the player.
            ready_status (LobbyInfoData.ReadyStatus): Ready status of the player.

        Returns:
            LobbyInfoData: A new LobbyInfoData object.
        """

        if header.m_gameYear == 23:
            return cls(struct.pack(cls.PACKET_FORMAT_23,
                ai_controlled,
                team_id.value,
                nationality.value,
                platform.value,
                name.encode('utf-8'),
                car_number,
                ready_status.value,
            ), header.m_packetFormat)
        if header.m_gameYear == 24:
            return cls(struct.pack(cls.PACKET_FORMAT_24,
                ai_controlled,
                team_id.value,
                nationality.value,
                platform.value,
                name.encode('utf-8'),
                car_number,
                your_telemetry.value,
                show_online_names,
                tech_level,
                ready_status.value,
            ), header.m_packetFormat)
        raise NotImplementedError(f"Unsupported game year: {header.m_gameYear}")

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
        if header.m_packetFormat == 2023:
            packet_len = LobbyInfoData.PACKET_LEN_23
        else: # 24
            packet_len = LobbyInfoData.PACKET_LEN_24

        self.m_lobbyPlayers.extend(
            LobbyInfoData(lobby_info_per_player_raw_data, header.m_packetFormat)
            for lobby_info_per_player_raw_data in _split_list(
                packet[1:], packet_len
            )
        )
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

    def __eq__(self, other: "PacketLobbyInfoData") -> bool:
        """
        Check if two PacketLobbyInfoData instances are equal.

        Args:
            other (PacketLobbyInfoData): The other PacketLobbyInfoData instance.

        Returns:
            bool: True if the two PacketLobbyInfoData instances are equal, False otherwise.
        """
        return (
            self.m_header == other.m_header and
            self.m_numPlayers == other.m_numPlayers and
            self.m_lobbyPlayers == other.m_lobbyPlayers
        )

    def __ne__(self, other: "PacketLobbyInfoData") -> bool:
        """
        Check if two PacketLobbyInfoData instances are not equal.

        Args:
            other (PacketLobbyInfoData): The other PacketLobbyInfoData instance.

        Returns:
            bool: True if the two PacketLobbyInfoData instances are not equal, False otherwise.
        """
        return not self.__eq__(other)

    def to_bytes(self) -> bytes:
        """
        Convert the PacketLobbyInfoData instance to raw data.

        Returns:
            bytes: Raw data representing the PacketLobbyInfoData instance.
        """

        return self.m_header.to_bytes() + struct.pack("<B", self.m_numPlayers) + \
                b"".join([player.to_bytes() for player in self.m_lobbyPlayers])

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    num_players: int,
                    lobby_players: List[LobbyInfoData]) -> "PacketLobbyInfoData":
        """Create a PacketLobbyInfoData object from individual values.

        Args:
            header (PacketHeader): The header of the telemetry packet.
            num_players (int): Number of players in the lobby.
            lobby_players (List[LobbyInfoData]): List of LobbyInfoData objects containing data for each player in the lobby.

        Returns:
            PacketLobbyInfoData: A PacketLobbyInfoData object initialized with the provided values.
        """

        raw_packet = struct.pack("<B", num_players) + \
                   b''.join([player.to_bytes() for player in lobby_players])
        return cls(header, raw_packet)