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

    PACKET_FORMAT = ("<"
        "B" # uint8      m_aiControlled;      // Whether the vehicle is AI (1) or Human (0) controlled
        "B" # uint8      m_driverId;       // Driver id - see appendix, 255 if network human
        "B" # uint8      m_networkId;       // Network id – unique identifier for network players
        "B" # uint8      m_teamId;            // Team id - see appendix
        "B" # uint8      m_myTeam;            // My team flag – 1 = My Team, 0 = otherwise
        "B" # uint8      m_raceNumber;        // Race number of the car
        "B" # uint8      m_nationality;       // Nationality of the driver
        "48s" # char       m_name[48];          // Name of participant in UTF-8 format – null terminated
                                        # // Will be truncated with … (U+2026) if too long
        "B" # uint8      m_yourTelemetry;     // The player's UDP setting, 0 = restricted, 1 = public
        "B" # uint8      m_showOnlineNames;   // The player's show online names setting, 0 = off, 1 = on
        "B" # uint8      m_platform;          // 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
    )
    PACKET_LEN = struct.calcsize(PACKET_FORMAT)

    class TelemetrySetting(Enum):
        """
        Enumeration representing the telemetry setting for the player.
        """

        RESTRICTED = 0
        PUBLIC = 1

        def __str__(self) -> str:
            """
            Returns a human-readable string representation of the telemetry setting.

            Returns:
                str: String representation of the telemetry setting.
            """
            return {
                ParticipantData.TelemetrySetting.RESTRICTED: "Restricted",
                ParticipantData.TelemetrySetting.PUBLIC: "Public",
            }.get(self)

        @staticmethod
        def isValid(telemetry_setting_code: int) -> bool:
            """Check if the given telemetry setting code is valid.

            Args:
                driver_id (int): The telemetry setting code to be validated.

            Returns:
                bool: True if valid.
            """
            if isinstance(telemetry_setting_code, ParticipantData.TelemetrySetting):
                return True  # It's already an instance of TelemetrySetting
            else:
                min_value = min(member.value for member in ParticipantData.TelemetrySetting)
                max_value = max(member.value for member in ParticipantData.TelemetrySetting)
                return min_value <= telemetry_setting_code <= max_value

    def __init__(self, data) -> None:
        """
        Initializes a ParticipantData object by unpacking the provided binary data.

        Parameters:
            data (bytes): Binary data to be unpacked.

        Raises:
            struct.error: If the binary data does not match the expected format.
        """
        unpacked_data = struct.unpack(self.PACKET_FORMAT, data)
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

        self.m_name = self.m_name.decode('utf-8', errors='replace').rstrip('\x00')
        if Platform.isValid(self.m_platform):
            self.m_platform = Platform(self.m_platform)
        if TeamID.isValid(self.m_teamId):
            self.m_teamId = TeamID(self.m_teamId)
        if ParticipantData.TelemetrySetting.isValid(self.m_yourTelemetry):
            self.m_yourTelemetry = ParticipantData.TelemetrySetting(self.m_yourTelemetry)
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

        for participant_data_raw in _split_list(packet[1:], ParticipantData.PACKET_LEN):
            self.m_participants.append(ParticipantData(participant_data_raw))

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
