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

from .common import *
from .common import _split_list, _extract_sublist

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

        for lobby_info_per_player_raw_data in _split_list(packet[1:], LobbyInfoData.PACKET_LEN):
            self.m_lobbyPlayers.append(LobbyInfoData(lobby_info_per_player_raw_data))

        # Trim the list
        self.m_lobbyPlayers = self.m_lobbyPlayers[:self.m_numPlayers]

    def __str__(self) -> str:
        """
        Returns a string representation of PacketLobbyInfoData.

        Returns:
            str: String representation of PacketLobbyInfoData.
        """

        lobby_players_str = ", ".join(str(player) for player in self.m_lobbyPlayers[:self.m_numPlayers])
        return (
            f"PacketLobbyInfoData("
            f"Number of Players: {self.m_numPlayers}, "
            f"Lobby Players: [{lobby_players_str}])"
        )

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

    PACKET_FORMAT = ("<"
        "B" # uint8     m_aiControlled;      // Whether the vehicle is AI (1) or Human (0) controlled
        "B" # uint8     m_teamId;            // Team id - see appendix (255 if no team currently selected)
        "B" # uint8     m_nationality;       // Nationality of the driver
        "B" # uint8     m_platform;          // 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
        "48s" # char      m_name[48];	  // Name of participant in UTF-8 format – null terminated
                                    #    // Will be truncated with ... (U+2026) if too long
        "B" # uint8     m_carNumber;         // Car number of the player
        "B" # uint8     m_readyStatus;       // 0 = not ready, 1 = ready, 2 = spectating
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

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
            else:
                min_value = min(member.value for member in LobbyInfoData.ReadyStatus)
                max_value = max(member.value for member in LobbyInfoData.ReadyStatus)
                return min_value <= ready_status_code <= max_value

        def __str__(self):
            if F1PacketType.isValid(self.value):
                return self.name
            else:
                return 'Marshal Zone Flag type ' + str(self.value)

    def __init__(self, data) -> None:
        """
        Initializes LobbyInfoData with raw data.

        Args:
            data (bytes): Raw data representing lobby information for a player.
        """

        (
            self.m_aiControlled,
            self.m_teamId,
            self.m_nationality,
            self.m_platform,
            self.m_name,
            self.m_carNumber,
            self.m_readyStatus,
        ) = struct.unpack(self.PACKET_FORMAT, data)

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

    def __str__(self) -> str:
        """
        Returns a string representation of LobbyInfoData.

        Returns:
            str: String representation of LobbyInfoData.
        """

        return (
            f"LobbyInfoData("
            f"AI Controlled: {self.m_aiControlled}, "
            f"Team ID: {self.m_teamId}, "
            f"Nationality: {self.m_nationality}, "
            f"Platform: {self.m_platform}, "
            f"Name: {self.m_name}, "
            f"Car Number: {self.m_carNumber}, "
            f"Ready Status: {self.m_readyStatus})"
        )

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
            "ready-status": self.m_readyStatus,
        }
