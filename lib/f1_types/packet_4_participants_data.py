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
from typing import Dict, Any, List, Union, Optional
from .common import PacketHeader, Platform, Nationality, TeamID23, TeamID24, TelemetrySetting

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
        self.m_gameYear = game_year
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

    def to_bytes(self) -> bytes:
        """
        Convert the ParticipantData instance to bytes.

        Returns:
            bytes: Bytes representation of the ParticipantData instance.
        """
        if self.m_gameYear == 23:
            return struct.pack(self.PACKET_FORMAT_23,
                self.m_aiControlled,
                self.m_driverId,
                self.networkId,
                self.m_teamId.value,
                self.m_myTeam,
                self.m_raceNumber,
                self.m_nationality.value,
                self.m_name.encode('utf-8'),
                self.m_yourTelemetry.value,
                self.m_showOnlineNames,
                self.m_platform.value
            )
        return struct.pack(self.PACKET_FORMAT_24,
            self.m_aiControlled,
            self.m_driverId,
            self.networkId,
            self.m_teamId.value,
            self.m_myTeam,
            self.m_raceNumber,
            self.m_nationality.value,
            self.m_name.encode('utf-8'),
            self.m_yourTelemetry.value,
            self.m_showOnlineNames,
            self.m_techLevel,
            self.m_platform.value
        )

    def __eq__(self, other: "ParticipantData") -> bool:
        """
        Checks if two ParticipantData objects are equal.

        Args:
            other (ParticipantData): The other ParticipantData object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        return (
            self.m_gameYear == other.m_gameYear and
            self.m_aiControlled == other.m_aiControlled and
            self.m_driverId == other.m_driverId and
            self.networkId == other.networkId and
            self.m_teamId == other.m_teamId and
            self.m_myTeam == other.m_myTeam and
            self.m_raceNumber == other.m_raceNumber and
            self.m_nationality == other.m_nationality and
            self.m_name == other.m_name and
            self.m_yourTelemetry == other.m_yourTelemetry and
            self.m_showOnlineNames == other.m_showOnlineNames and
            self.m_techLevel == other.m_techLevel and
            self.m_platform == other.m_platform
        )

    def __ne__(self, other: "ParticipantData") -> bool:
        """
        Checks if two ParticipantData objects are not equal.

        Args:
            other (ParticipantData): The other ParticipantData object to compare with.

        Returns:
            bool: True if the objects are not equal, False otherwise.
        """
        return not self.__eq__(other)

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    ai_controlled: bool,
                    driver_id: int,
                    network_id: int,
                    team_id: Union[TeamID23, TeamID24],
                    my_team: bool,
                    race_number: int,
                    nationality: Nationality,
                    name: str,
                    your_telemetry: TelemetrySetting,
                    show_online_names: bool,
                    platform: Platform,
                    tech_level: Optional[int] = 0
                    ) -> "ParticipantData":
        """
        Creates a new ParticipantData object with the provided values.

        Args:
            header (PacketHeader): Header containing general information about the packet.
            ai_controlled (bool): Whether the car is an AI car or not.
            driver_id (int): ID of the car's driver.
            network_id (int): ID of the car on the network.
            team_id (Union[TeamID23, TeamID24]): ID of the car's team.
            my_team (bool): Whether the car is on its team or not.
            race_number (int): Race number of the car.
            nationality (Nationality): Nationality of the car.
            name (str): Name of the car.
            your_telemetry (TelemetrySetting): Your telemetry setting.
            show_online_names (bool): Whether to show online names or not.
            platform (Platform): Platform of the car.
            tech_level (Optional[int], optional): Tech level of the car. Defaults to 0. Will only be considered for 24

        Returns:
            ParticipantData: A new ParticipantData object with the provided values.
        """

        if header.m_gameYear == 23:
            data = struct.pack(ParticipantData.PACKET_FORMAT_23,
                ai_controlled,
                driver_id,
                network_id,
                team_id.value,
                my_team,
                race_number,
                nationality.value,
                name.encode('utf-8'),
                your_telemetry.value,
                show_online_names,
                platform.value
            )
        else:
            data = struct.pack(ParticipantData.PACKET_FORMAT_24,
                ai_controlled,
                driver_id,
                network_id,
                team_id.value,
                my_team,
                race_number,
                nationality.value,
                name.encode('utf-8'),
                your_telemetry.value,
                show_online_names,
                tech_level,
                platform.value
            )
        return cls(data, header.m_gameYear)

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
        self.m_numActiveCars: int = struct.unpack("<B", packet[:1])[0]
        self.m_participants: List[ParticipantData] = []            # ParticipantData[22]

        packet_len = ParticipantData.PACKET_LEN_23 if (header.m_gameYear == 23) else ParticipantData.PACKET_LEN_24
        # Iterate over packet[1:] in steps of packet_len,
        # creating ParticipantData objects for each segment and passing the game year.

        self.m_participants.extend(
            ParticipantData(packet[i:i + packet_len], header.m_gameYear)
            for i in range(1, len(packet), packet_len)
        )
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

    def to_bytes(self) -> bytes:
        """
        Convert the PacketParticipantsData instance to a bytes object.

        Returns:
            bytes: Bytes object representing the PacketParticipantsData instance.
        """

        return (
            self.m_header.to_bytes() +
            struct.pack("<B", self.m_numActiveCars) +
            b''.join([participant.to_bytes() for participant in self.m_participants]))

    @classmethod
    def from_values(cls,
                    header: PacketHeader,
                    num_active_cars: int,
                    participants: List[ParticipantData]) -> "PacketParticipantsData":
        """
        Create a new PacketParticipantsData instance with the provided values.

        Parameters:
            - header (PacketHeader): Header containing general information about the packet.
            - num_active_cars (int): Number of active cars in the data - should match the number of cars on HUD.
            - participants (List[ParticipantData]): List of ParticipantData objects representing information
                about each participant in the race.

                Note:
                    The length of participants should not exceed max_participants.

        Returns:
            PacketParticipantsData: A new PacketParticipantsData instance with the provided values.
        """

        return cls(header,
                   struct.pack("<B", num_active_cars) +
                        b''.join([participant.to_bytes() for participant in participants]))

    def __eq__(self, other: "PacketParticipantsData") -> bool:
        """
        Compare two PacketParticipantsData instances for equality.

        Parameters:
            - other (PacketParticipantsData): The other PacketParticipantsData instance to compare with.

        Returns:
            bool: True if the two instances are equal, False otherwise.
        """

        if not isinstance(other, PacketParticipantsData):
            return False
        return (
            self.m_header == other.m_header and
            self.m_numActiveCars == other.m_numActiveCars and
            self.m_participants == other.m_participants
        )

    def __ne__(self, other: "PacketParticipantsData") -> bool:
        """
        Compare two PacketParticipantsData instances for inequality.

        Parameters:
            - other (PacketParticipantsData): The other PacketParticipantsData instance to compare with.

        Returns:
            bool: True if the two instances are not equal, False otherwise.
        """

        return not self.__eq__(other)