# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Dict, Any
from enum import Enum
import struct

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class F1PacketType(Enum):
    """Class of enum representing the different packet types emitted by the game
    """
    MOTION = 0
    SESSION = 1
    LAP_DATA = 2
    EVENT = 3
    PARTICIPANTS = 4
    CAR_SETUPS = 5
    CAR_TELEMETRY = 6
    CAR_STATUS = 7
    FINAL_CLASSIFICATION = 8
    LOBBY_INFO = 9
    CAR_DAMAGE = 10
    SESSION_HISTORY = 11
    TYRE_SETS = 12
    MOTION_EX = 13
    TIME_TRIAL = 14
    LAP_POSITIONS = 15

    @staticmethod
    def isValid(packet_type) -> bool:
        """Check if the given packet type ID is valid

        Args:
            packet_type (int or F1PacketType): The packet type to be validated

        Returns:
            bool: True if valid, else False
        """

        if isinstance(packet_type, F1PacketType):
            return True  # It's already an instance of F1PacketType
        return any(packet_type == member.value for member in F1PacketType)

    def __str__(self) -> str:
        """to_string method

        Returns:
            str: string representation of this enum
        """
        if F1PacketType.isValid(self.value):
            return self.name
        return f'packet type {str(self.value)}'

class PacketHeader:
    """
    A class for parsing the Packet Header of a telemetry packet in a racing game.

    The packet header structure is as follows:

    Attributes:
        - m_packetFormat (int): The format of the telemetry packet (2023).
        - m_gameYear (int): The game year, represented by the last two digits (e.g., 23).
        - m_gameMajorVersion (int): The game's major version (X.00).
        - m_gameMinorVersion (int): The game's minor version (1.XX).
        - m_packetVersion (int): The version of this packet type, starting from 1.
        - m_packetId (F1PacketType): Identifier for the packet type. Refer to the F1PacketType enumeration.
        - m_sessionUID (int): Unique identifier for the session.
        - m_sessionTime (float): Timestamp of the session.
        - m_frameIdentifier (int): Identifier for the frame the data was retrieved on.
        - m_overallFrameIdentifier (int): Overall identifier for the frame, not going back after flashbacks.
        - m_playerCarIndex (int): Index of the player's car in the array.
        - m_secondaryPlayerCarIndex (int): Index of the secondary player's car in the array (255 if no second player).
    """

    COMPILED_PACKET_STRUCT = struct.Struct("<"
        "H" # packet format
        "B" # year
        "B" # major
        "B" # minor
        "B" # ver
        "B" # pktID
        "Q" # sessionID
        "f" # session time
        "I" # uint32
        "I" # uint32
        "B" # carIndex
        "B" # sec car index
    )
    PACKET_LEN: int = COMPILED_PACKET_STRUCT.size

    def __init__(self, data: bytes) -> None:
        """
        Initializes the PacketHeaderParser with the raw packet data.

        Args:
            data (bytes): Raw binary data representing the packet header.
        """

        # Declare all variables with types
        self.m_packetFormat: int
        self.m_gameYear: int
        self.m_gameMajorVersion: int
        self.m_gameMinorVersion: int
        self.m_packetVersion: int
        self.m_packetId: F1PacketType
        self.m_sessionUID: int
        self.m_sessionTime: float
        self.m_frameIdentifier: int
        self.m_overallFrameIdentifier: int
        self.m_playerCarIndex: int
        self.m_secondaryPlayerCarIndex: int

        # Unpack the data
        self.m_packetFormat, self.m_gameYear, self.m_gameMajorVersion, self.m_gameMinorVersion, \
            self.m_packetVersion, self.m_packetId, self.m_sessionUID, self.m_sessionTime, \
            self.m_frameIdentifier, self.m_overallFrameIdentifier, self.m_playerCarIndex, \
            self.m_secondaryPlayerCarIndex = self.COMPILED_PACKET_STRUCT.unpack(data)

        # Set packet ID as enum type
        if F1PacketType.isValid(self.m_packetId):
            self.m_packetId = F1PacketType(self.m_packetId)
            self.is_supported_packet_type = True
        else:
            self.is_supported_packet_type = False

    def __str__(self) -> str:
        return (
            f"PacketHeader("
            f"Format: {self.m_packetFormat}, "
            f"Year: {self.m_gameYear}, "
            f"Major Version: {self.m_gameMajorVersion}, "
            f"Minor Version: {self.m_gameMinorVersion}, "
            f"Packet Version: {self.m_packetVersion}, "
            f"Packet ID: {self.m_packetId}, "
            f"Session UID: {self.m_sessionUID}, "
            f"Session Time: {self.m_sessionTime}, "
            f"Frame Identifier: {self.m_frameIdentifier}, "
            f"Overall Frame Identifier: {self.m_overallFrameIdentifier}, "
            f"Player Car Index: {self.m_playerCarIndex}, "
            f"Secondary Player Car Index: {self.m_secondaryPlayerCarIndex})"
        )

    def toJSON(self) -> Dict[str, Any]:
        """Converts the PacketHeader object to a dictionary suitable for JSON serialization.

        Returns:
            Dict[str, Any]: A dictionary representing the JSON-compatible data.
        """

        return {
            "packet-format": self.m_packetFormat,
            "game-year": self.m_gameYear,
            "game-major-version": self.m_gameMajorVersion,
            "game-minor-version": self.m_gameMinorVersion,
            "packet-version": self.m_packetVersion,
            "packet-id": str(self.m_packetId),
            "session-uid": self.m_sessionUID,
            "session-time": self.m_sessionTime,
            "frame-identifier": self.m_frameIdentifier,
            "overall-frame-identifier": self.m_overallFrameIdentifier,
            "player-car-index": self.m_playerCarIndex,
            "secondary-player-car-index": self.m_secondaryPlayerCarIndex
        }

    def __eq__(self, other: Any) -> bool:
        """Check if this PacketHeader is equal to another.

        Args:
            other (Any): The object to compare against.

        Returns:
            bool: True if equal, False otherwise.
        """
        if not isinstance(other, PacketHeader):
            return NotImplemented

        return (self.m_packetFormat == other.m_packetFormat and
                self.m_gameYear == other.m_gameYear and
                self.m_gameMajorVersion == other.m_gameMajorVersion and
                self.m_gameMinorVersion == other.m_gameMinorVersion and
                self.m_packetVersion == other.m_packetVersion and
                self.m_packetId == other.m_packetId and
                self.m_sessionUID == other.m_sessionUID and
                self.m_sessionTime == other.m_sessionTime and
                self.m_frameIdentifier == other.m_frameIdentifier and
                self.m_overallFrameIdentifier == other.m_overallFrameIdentifier and
                self.m_playerCarIndex == other.m_playerCarIndex and
                self.m_secondaryPlayerCarIndex == other.m_secondaryPlayerCarIndex)

    def __ne__(self, other: Any) -> bool:
        """Check if this PacketHeader is not equal to another.

        Args:
            other (Any): The object to compare against.

        Returns:
            bool: True if not equal, False otherwise.
        """
        return not self.__eq__(other)

    @classmethod
    def from_values(cls, packet_format: int, game_year: int, game_major_version: int,
                    game_minor_version: int, packet_version: int, packet_type: F1PacketType,
                    session_uid: int, session_time: float, frame_identifier: int,
                    overall_frame_identifier: int, player_car_index: int,
                    secondary_player_car_index: int) -> 'PacketHeader':
        """Create a PacketHeader object from individual values.

        Args:
            packet_format (int): The format of the telemetry packet.
            game_year (int): The game year.
            game_major_version (int): The game's major version.
            game_minor_version (int): The game's minor version.
            packet_version (int): The version of this packet type.
            packet_type (F1PacketType): Identifier for the packet type.
            session_uid (int): Unique identifier for the session.
            session_time (float): Timestamp of the session.
            frame_identifier (int): Identifier for the frame.
            overall_frame_identifier (int): Overall identifier for the frame.
            player_car_index (int): Index of the player's car.
            secondary_player_car_index (int): Index of the secondary player's car.

        Returns:
            PacketHeader: A PacketHeader object initialized with the given values.
        """
        return cls(cls.COMPILED_PACKET_STRUCT.pack(packet_format, game_year, game_major_version,
                               game_minor_version, packet_version, packet_type.value, session_uid,
                               session_time, frame_identifier, overall_frame_identifier,
                               player_car_index, secondary_player_car_index))

    def to_bytes(self) -> bytes:
        """Converts the PacketHeader object to bytes.

        Returns:
            bytes: The raw binary data representing the packet header.
        """
        return self.COMPILED_PACKET_STRUCT.pack(self.m_packetFormat, self.m_gameYear,
                           self.m_gameMajorVersion, self.m_gameMinorVersion,
                           self.m_packetVersion, self.m_packetId.value, self.m_sessionUID,
                           self.m_sessionTime, self.m_frameIdentifier,
                           self.m_overallFrameIdentifier, self.m_playerCarIndex,
                           self.m_secondaryPlayerCarIndex)
