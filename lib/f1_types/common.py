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

from enum import Enum
from typing import List, Any, Dict, Optional, Set
import struct

# ------------------------- PRIVATE FUNCTIONS ----------------------------------

def _split_list(original_list: List[Any], sublist_length: int) -> List[List[Any]]:
    """
    Splits the given list into sublists of a specified length.

    Args:
        original_list (List[Any]): The original list to be split.
        sublist_length (int): The desired length of each sublist.

    Returns:
        List[List[Any]]: A list containing sublists of the specified length.
    """
    return [original_list[i:i + sublist_length] for i in range(0, len(original_list), sublist_length)]

def _extract_sublist(data: bytes, lower_index: int, upper_index: int) -> bytes:
    # Ensure the indices are within bounds
    if lower_index < 0 or upper_index > len(data) or lower_index > upper_index:
        # Return an empty bytes object to indicate an error
        return b''

    # Extract the sub-list
    sub_list: bytes = data[lower_index:upper_index]
    return sub_list

# ------------------------- ERROR CLASSES --------------------------------------

class InvalidPacketLengthError(Exception):
    """
    This exception type is used to indicate to the telemetry manager that there has
    been a parsing error due to receving a packet of unexpected length (possibly
    incomplete or corrupt. or more realistically a bug)
    """
    def __init__(self, message):
        super().__init__("Invalid packet length. " + message)

# -------------------- COMMON CLASSES ------------------------------------------
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
        return 'packet type ' + str(self.value)

class ResultStatus(Enum):
    """
    Enumeration representing the result status of a driver after a racing session.
    """

    INVALID = 0
    INACTIVE = 1
    ACTIVE = 2
    FINISHED = 3
    DID_NOT_FINISH = 4
    DISQUALIFIED = 5
    NOT_CLASSIFIED = 6
    RETIRED = 7

    @staticmethod
    def isValid(result_status: int) -> bool:
        """Check if the given result status is valid.

        Args:
            result_status (int): The result status to be validated.

        Returns:
            bool: True if valid.
        """
        if isinstance(result_status, ResultStatus):
            return True  # It's already an instance of ResultStatus
        return any(result_status == member.value for member in ResultStatus)

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the result status.

        Returns:
            str: String representation of the result status.
        """
        status_mapping = {
            0: "INVALID",
            1: "INACTIVE",
            2: "ACTIVE",
            3: "FINISHED",
            4: "DID_NOT_FINISH",
            5: "DISQUALIFIED",
            6: "NOT_CLASSIFIED",
            7: "RETIRED",
        }
        return status_mapping.get(self.value, "---")

class SessionType(Enum):
    """
    Enum class representing F1 session types.
    """
    UNKNOWN = 0
    PRACTICE_1 = 1
    PRACTICE_2 = 2
    PRACTICE_3 = 3
    SHORT_PRACTICE = 4
    QUALIFYING_1 = 5
    QUALIFYING_2 = 6
    QUALIFYING_3 = 7
    SHORT_QUALIFYING = 8
    ONE_SHOT_QUALIFYING = 9
    RACE = 10
    RACE_2 = 11
    RACE_3 = 12
    TIME_TRIAL = 13

    @staticmethod
    def isValid(session_type: int):
        """
        Check if the given session type is valid.

        Args:
            session_type (int): The session type to be validated.

        Returns:
            bool: True if valid
        """
        if isinstance(session_type, SessionType):
            return True  # It's already an instance of SessionType
        return any(session_type == member.value for member in SessionType)

    def __str__(self):
        """
        Return a string representation of the SessionType with spaces.

        Returns:
            str: String representation of the SessionType.
        """
        return {
            SessionType.UNKNOWN : "N/A",
            SessionType.PRACTICE_1 : "Practice 1",
            SessionType.PRACTICE_2 : "Practice 2",
            SessionType.PRACTICE_3 : "Practice 3",
            SessionType.SHORT_PRACTICE : "Short Practice",
            SessionType.QUALIFYING_1 : "Qualifying 1",
            SessionType.QUALIFYING_2 : "Qualifying 2",
            SessionType.QUALIFYING_3 : "Qualifying 3",
            SessionType.SHORT_QUALIFYING : "Short Qualifying",
            SessionType.ONE_SHOT_QUALIFYING : "One Shot Qualifying",
            SessionType.RACE  : "Race",
            SessionType.RACE_2  : "Race 2",
            SessionType.RACE_3  : "Race 3",
            SessionType.TIME_TRIAL  : "Time Trial",
        }.get(self, " ")

class ActualTyreCompound(Enum):
    """
    Enumeration representing different tyre compounds used in Formula 1 and Formula 2.

    Attributes:
        C5 (int): F1 Modern - C5
        C4 (int): F1 Modern - C4
        C3 (int): F1 Modern - C3
        C2 (int): F1 Modern - C2
        C1 (int): F1 Modern - C1
        C0 (int): F1 Modern - C0
        INTER (int): F1 Modern - Intermediate
        WET (int): F1 Modern - Wet
        DRY (int): F1 Classic - Dry
        WET_CLASSIC (int): F1 Classic - Wet
        SUPER_SOFT (int): F2 - Super Soft
        SOFT (int): F2 - Soft
        MEDIUM (int): F2 - Medium
        HARD (int): F2 - Hard
        WET_F2 (int): F2 - Wet

        Note:
            Each attribute represents a unique tyre compound identified by an integer value.
    """

    C5 = 16
    C4 = 17
    C3 = 18
    C2 = 19
    C1 = 20
    C0 = 21
    INTER = 7
    WET = 8
    DRY = 9
    WET_CLASSIC = 10
    SUPER_SOFT = 11
    SOFT = 12
    MEDIUM = 13
    HARD = 14
    WET_F2 = 15

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the tyre compound.

        Returns:
            str: String representation of the tyre compound.
        """
        return {
            ActualTyreCompound.C5: "C5",
            ActualTyreCompound.C4: "C4",
            ActualTyreCompound.C3: "C3",
            ActualTyreCompound.C2: "C2",
            ActualTyreCompound.C1: "C1",
            ActualTyreCompound.C0: "C0",
            ActualTyreCompound.INTER: "Inters",
            ActualTyreCompound.WET: "Wet",
            ActualTyreCompound.DRY: "Dry",
            ActualTyreCompound.WET_CLASSIC: "Wet (Classic)",
            ActualTyreCompound.SUPER_SOFT: "Super Soft",
            ActualTyreCompound.SOFT: "Soft",
            ActualTyreCompound.MEDIUM: "Medium",
            ActualTyreCompound.HARD: "Hard",
            ActualTyreCompound.WET_F2: "Wet (F2)",
        }[self]

    @staticmethod
    def isValid(actual_tyre_compound: int) -> bool:
        """
        Check if the input event type string maps to a valid enum value.

        Args:
            actual_tyre_compound (int): The actual tyre compound code

        Returns:
            bool: True if the event type is valid, False otherwise.
        """
        if isinstance(actual_tyre_compound, ActualTyreCompound):
            return True  # It's already an instance of ActualTyreCompound
        return any(actual_tyre_compound == member.value for member in ActualTyreCompound)

class VisualTyreCompound(Enum):
    """
    Enumeration representing different visual tyre compounds used in Formula 1 and Formula 2.

    Attributes:
        SOFT (int): Soft tyre compound
        MEDIUM (int): Medium tyre compound
        HARD (int): Hard tyre compound
        INTER (int): Intermediate tyre compound
        WET (int): Wet tyre compound
        WET_CLASSIC (int): Wet tyre compound (Classic)
        SUPER_SOFT (int): Super Soft tyre compound (F2 '19)
        SOFT_F2 (int): Soft tyre compound (F2 '19)
        MEDIUM_F2 (int): Medium tyre compound (F2 '19)
        HARD_F2 (int): Hard tyre compound (F2 '19)
        WET_F2 (int): Wet tyre compound (F2 '19)

        Note:
            Each attribute represents a unique visual tyre compound identified by an integer value.
    """

    SOFT = 16
    MEDIUM = 17
    HARD = 18
    INTER = 7
    WET = 8
    WET_CLASSIC = 8  # Same value as WET for F1 visual (Classic)
    SUPER_SOFT = 19
    SOFT_F2 = 20
    MEDIUM_F2 = 21
    HARD_F2 = 22
    WET_F2 = 15

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the visual tyre compound.

        Returns:
            str: String representation of the visual tyre compound.
        """
        return {
            VisualTyreCompound.SOFT: "Soft",
            VisualTyreCompound.MEDIUM: "Medium",
            VisualTyreCompound.HARD: "Hard",
            VisualTyreCompound.INTER: "Inters",
            VisualTyreCompound.WET: "Wet",
            # VisualTyreCompound.WET_CLASSIC: "Wet (Classic)",
            VisualTyreCompound.WET_CLASSIC: "Wet",
            VisualTyreCompound.SUPER_SOFT: "Super Soft (F2 '19)",
            VisualTyreCompound.SOFT_F2: "Soft (F2 '19)",
            VisualTyreCompound.MEDIUM_F2: "Medium (F2 '19)",
            VisualTyreCompound.HARD_F2: "Hard (F2 '19)",
            VisualTyreCompound.WET_F2: "Wet (F2 '19)",
        }[self]

    @staticmethod
    def isValid(visual_tyre_compound: int) -> bool:
        """
        Check if the input event type string maps to a valid enum value.

        Args:
            visual_tyre_compound (int): The visual tyre compound code

        Returns:
            bool: True if the event type is valid, False otherwise.
        """
        if isinstance(visual_tyre_compound, VisualTyreCompound):
            return True  # It's already an instance of VisualTyreCompound
        return any(visual_tyre_compound == member.value for member in VisualTyreCompound)

class Nationality(Enum):
    """
    Enum representing nationalities with corresponding IDs.
    """
    Unspecified = 0
    American = 1
    Argentinean = 2
    Australian = 3
    Austrian = 4
    Azerbaijani = 5
    Bahraini = 6
    Belgian = 7
    Bolivian = 8
    Brazilian = 9
    British = 10
    Bulgarian = 11
    Cameroonian = 12
    Canadian = 13
    Chilean = 14
    Chinese = 15
    Colombian = 16
    Costa_Rican = 17
    Croatian = 18
    Cypriot = 19
    Czech = 20
    Danish = 21
    Dutch = 22
    Ecuadorian = 23
    English = 24
    Emirian = 25
    Estonian = 26
    Finnish = 27
    French = 28
    German = 29
    Ghanaian = 30
    Greek = 31
    Guatemalan = 32
    Honduran = 33
    Hong_Konger = 34
    Hungarian = 35
    Icelander = 36
    Indian = 37
    Indonesian = 38
    Irish = 39
    Israeli = 40
    Italian = 41
    Jamaican = 42
    Japanese = 43
    Jordanian = 44
    Kuwaiti = 45
    Latvian = 46
    Lebanese = 47
    Lithuanian = 48
    Luxembourger = 49
    Malaysian = 50
    Maltese = 51
    Mexican = 52
    Monegasque = 53
    New_Zealander = 54
    Nicaraguan = 55
    Northern_Irish = 56
    Norwegian = 57
    Omani = 58
    Pakistani = 59
    Panamanian = 60
    Paraguayan = 61
    Peruvian = 62
    Polish = 63
    Portuguese = 64
    Qatari = 65
    Romanian = 66
    Russian = 67
    Salvadoran = 68
    Saudi = 69
    Scottish = 70
    Serbian = 71
    Singaporean = 72
    Slovakian = 73
    Slovenian = 74
    South_Korean = 75
    South_African = 76
    Spanish = 77
    Swedish = 78
    Swiss = 79
    Thai = 80
    Turkish = 81
    Uruguayan = 82
    Ukrainian = 83
    Venezuelan = 84
    Barbadian = 85
    Welsh = 86
    Vietnamese = 87

    def __str__(self) -> str:
        """
        Returns the string representation of the Enum member.
        """
        return f"{self.name.replace('_', ' ')}"

    @staticmethod
    def isValid(nationality_code: int) -> bool:
        """Check if the given nationality code is valid.

        Args:
            nationality_code (int): The nationality code to be validated.

        Returns:
            bool: True if valid.
        """
        if isinstance(nationality_code, Nationality):
            return True  # It's already an instance of Nationality
        return any(nationality_code == member.value for member in Nationality)

class Platform(Enum):
    """
    Enumeration representing different gaming platforms.
    """
    STEAM = 1
    PLAYSTATION = 3
    XBOX = 4
    ORIGIN = 6
    UNKNOWN = 255

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the gaming platform.

        Returns:
            str: String representation of the gaming platform.
        """
        return {
            Platform.STEAM: "Steam",
            Platform.PLAYSTATION: "PlayStation",
            Platform.XBOX: "Xbox",
            Platform.ORIGIN: "Origin",
            Platform.UNKNOWN: "Unknown",
        }[self]

    @staticmethod
    def isValid(platform_type_code: int):
        """Check if the given session type code is valid.

        Args:
            platform_type_code (int): The platform type code to be validated.
                Also supports type Platform. Returns true in this case

        Returns:
            bool: true if valid
        """
        if isinstance(platform_type_code, Platform):
            return True  # It's already an instance of Platform
        return any(platform_type_code == member.value for member in Platform)

class TeamID(Enum):
    """
    Enumeration representing the TeamID setting for the player.
    """

    MERCEDES = 0
    FERRARI = 1
    RED_BULL_RACING = 2
    WILLIAMS = 3
    ASTON_MARTIN = 4
    ALPINE = 5
    ALPHA_TAURI = 6
    HAAS = 7
    MCLAREN = 8
    ALFA_ROMEO = 9
    MERCEDES_2020 = 85
    FERRARI_2020 = 86
    RED_BULL_2020 = 87
    WILLIAMS_2020 = 88
    RACING_POINT_2020 = 89
    RENAULT_2020 = 90
    ALPHA_TAURI_2020 = 91
    HAAS_2020 = 92
    MCLAREN_2020 = 93
    ALFA_ROMEO_2020 = 94
    ASTON_MARTIN_DB11_V12 = 95
    ASTON_MARTIN_VANTAGE_F1_EDITION = 96
    ASTON_MARTIN_VANTAGE_SAFETY_CAR = 97
    FERRARI_F8_TRIBUTO = 98
    FERRARI_ROMA = 99
    MCLAREN_720S = 100
    MCLAREN_ARTURA = 101
    MERCEDES_AMG_GT_BLACK_SERIES_SAFETY_CAR = 102
    MERCEDES_AMG_GTR_PRO = 103
    F1_CUSTOM_TEAM = 104
    PREMA_21 = 106
    UNI_VIRTUOSI_21 = 107
    CARLIN_21 = 108
    HITECH_21 = 109
    ART_GP_21 = 110
    MP_MOTORSPORT_21 = 111
    CHAROUZ_21 = 112
    DAMS_21 = 113
    CAMPOS_21 = 114
    BWT_21 = 115
    TRIDENT_21 = 116
    MERCEDES_AMG_GT_BLACK_SERIES = 117
    MERCEDES_22 = 118
    FERRARI_22 = 119
    RED_BULL_RACING_22 = 120
    WILLIAMS_22 = 121
    ASTON_MARTIN_22 = 122
    ALPINE_22 = 123
    ALPHA_TAURI_22 = 124
    HAAS_22 = 125
    MCLAREN_22 = 126
    ALFA_ROMEO_22 = 127
    KONNERSPORT_22 = 128
    KONNERSPORT = 129
    PREMA_22 = 130
    VIRTUOSI_22 = 131
    CARLIN_22 = 132
    MP_MOTORSPORT_22 = 133
    CHAROUZ_22 = 134
    DAMS_22 = 135
    CAMPOS_22 = 136
    VAN_AMERSFOORT_RACING_22 = 137
    TRIDENT_22 = 138
    HITECH_22 = 139
    ART_GP_22 = 140

    @staticmethod
    def isValid(team_id: int) -> bool:
        """Check if the given team ID is valid.

        Args:
            team_id (int): The team ID to be validated.

        Returns:
            bool: True if valid.
        """
        if isinstance(team_id, TeamID):
            return True  # It's already an instance of TeamID
        return any(team_id == member.value for member in TeamID)

    def __str__(self) -> str:
        """Return the string representation of the driver.

        Returns:
            str: String representation of the driver.
        """
        teams_mapping = {
            0: "Mercedes", 1: "Ferrari", 2: "Red Bull Racing",
            3: "Williams", 4: "Aston Martin", 5: "Alpine",
            6: "Alpha Tauri", 7: "Haas", 8: "McLaren",
            9: "Alfa Romeo", 85: "Mercedes 2020", 86: "Ferrari 2020",
            87: "Red Bull 2020", 88: "Williams 2020", 89: "Racing Point 2020",
            90: "Renault 2020", 91: "Alpha Tauri 2020", 92: "Haas 2020",
            93: "McLaren 2020", 94: "Alfa Romeo 2020", 95: "Aston Martin DB11 V12",
            96: "Aston Martin Vantage F1 Edition", 97: "Aston Martin Vantage Safety Car",
            98: "Ferrari F8 Tributo", 99: "Ferrari Roma", 100: "McLaren 720S",
            101: "McLaren Artura", 102: "Mercedes AMG GT Black Series Safety Car",
            103: "Mercedes AMG GTR Pro", 104: "F1 Custom Team",
            106: "Prema '21", 107: "Uni-Virtuosi '21", 108: "Carlin '21",
            109: "Hitech '21", 110: "Art GP '21", 111: "MP Motorsport '21",
            112: "Charouz '21", 113: "Dams '21", 114: "Campos '21",
            115: "BWT '21", 116: "Trident '21", 117: "Mercedes AMG GT Black Series",
            118: "Mercedes '22", 119: "Ferrari '22", 120: "Red Bull Racing '22",
            121: "Williams '22", 122: "Aston Martin '22", 123: "Alpine '22",
            124: "Alpha Tauri '22", 125: "Haas '22", 126: "McLaren '22",
            127: "Alfa Romeo '22", 128: "Konnersport '22", 129: "Konnersport",
            130: "Prema '22", 131: "Virtuosi '22", 132: "Carlin '22",
            133: "MP Motorsport '22", 134: "Charouz '22", 135: "Dams '22",
            136: "Campos '22", 137: "Van Amersfoort Racing '22", 138: "Trident '22",
            139: "Hitech '22", 140: "Art GP '22"
        }
        return teams_mapping.get(self.value, "---")

class TrackID(Enum):
    """
    Enum class representing F1 track IDs and their corresponding names.
    """
    Melbourne = 0
    Paul_Ricard = 1
    Shanghai = 2
    Sakhir_Bahrain = 3
    Catalunya = 4
    Monaco = 5
    Montreal = 6
    Silverstone = 7
    Hockenheim = 8
    Hungaroring = 9
    Spa = 10
    Monza = 11
    Singapore = 12
    Suzuka = 13
    Abu_Dhabi = 14
    Texas = 15
    Brazil = 16
    Austria = 17
    Sochi = 18
    Mexico = 19
    Baku_Azerbaijan = 20
    Sakhir_Short = 21
    Silverstone_Short = 22
    Texas_Short = 23
    Suzuka_Short = 24
    Hanoi = 25
    Zandvoort = 26
    Imola = 27
    Portimao = 28
    Jeddah = 29
    Miami = 30
    Las_Vegas = 31
    Losail = 32

    def __str__(self):
        """
        Returns a string representation of the track.
        """
        return {
            "Paul_Ricard": "Paul Ricard",
            "Sakhir_Bahrain": "Sakhir (Bahrain)",
            "Abu_Dhabi": "Abu Dhabi",
            "Baku_Azerbaijan": "Baku (Azerbaijan)",
            "Portimao": "Portimão"
        }.get(self.name, self.name.replace("_", " "))

    @staticmethod
    def isValid(track: int):
        """Check if the given circuit code is valid.

        Args:
            track (int): The circuit code to be validated.
                Also supports type TrackID. Returns true in this case

        Returns:
            bool: true if valid
        """
        if isinstance(track, TrackID):
            return True  # It's already an instance of TrackID
        min_value = min(member.value for member in TrackID)
        max_value = max(member.value for member in TrackID)
        return min_value <= track <= max_value

class F1Utils:
    """
    Utility class for Formula 1-related operations.

    Constants:
        INDEX_REAR_LEFT (int): Index for the rear-left position in tyre/brake arrays/lists.
        INDEX_REAR_RIGHT (int): Index for the rear-right position in tyre/brake arrays/lists.
        INDEX_FRONT_LEFT (int): Index for the front-left position in tyre/brake arrays/lists.
        INDEX_FRONT_RIGHT (int): Index for the front-right position in tyre/brake arrays/lists.
        PLAYER_INDEX_INVALID (int): The constant representing invalid player index

    Methods:
        millisecondsToMinutesSecondsMilliseconds(milliseconds) -> str:
            Convert milliseconds to a formatted string in the format "MM:SS.SSS".

        millisecondsToSecondsMilliseconds(milliseconds) -> str:
            Convert milliseconds to a formatted string in the format "SS.SSS".

        millisecondsToSecondsMilliseconds(milliseconds) -> str:
            Convert milliseconds to a formatted string in the format "SS.SSS".

        secondsToMinutesSecondsMilliseconds(seconds) -> str:
            Convert seconds to a formatted string in the format "MM:SS.SSS".

        floatSecondsToMinutesSecondsMilliseconds(seconds) -> str:
            Convert float seconds to a formatted string in the format "MM:SS.SSS".

        timeStrToMilliseconds(time_str: str) -> int:
            Convert a time string in the format "MM:SS.SSS" to milliseconds.

        floatToStr(float_val : float, num_dec_places : Optional[int] = 2) -> str:
            Convert a float to a string with a specified number of decimal places.
    """

    # These are the indices for tyre/brake arrays/lists
    INDEX_REAR_LEFT = 0
    INDEX_REAR_RIGHT = 1
    INDEX_FRONT_LEFT = 2
    INDEX_FRONT_RIGHT = 3
    PLAYER_INDEX_INVALID = 255

    # TRACKS_WHERE_FINISH_LINE_BEFORE_PIT_GARAGE : Set[TrackID] = {
    #     TrackID.Sakhir_Bahrain, # Yes
    #     TrackID.Jeddah, # Yes
    #     # TrackID.Melbourne,
    #     TrackID.Baku_Azerbaijan, # Yes
    #     TrackID.Miami, # Yes
    #     TrackID.Imola, # Yes
    #     # TrackID.Monaco,
    #     TrackID.Catalunya, # Yes
    #     # TrackID.Montreal,
    #     TrackID.Austria, # Yes
    #     TrackID.Silverstone, # Yes
    #     TrackID.Hungaroring, # Yes
    #     TrackID.Spa, # Yes
    #     TrackID.Zandvoort, # Yes
    #     TrackID.Monza, # Yes
    #     TrackID.Singapore, # Yes
    #     TrackID.Suzuka, # Yes
    #     # TrackID.Losail,
    #     TrackID.Texas, # Yes
    #     TrackID.Mexico, # Yes
    #     TrackID.Brazil, # Yes
    #     TrackID.Las_Vegas, # Yes
    #     TrackID.Abu_Dhabi, # Yes
    #     TrackID.Shanghai, # Yes
    #     # TrackID.Paul_Ricard,
    #     TrackID.Portimao, # Yes
    # }

    TRACKS_WHERE_FINISH_LINE_AFTER_PIT_GARAGE : Set[TrackID] = {
        TrackID.Melbourne,
        TrackID.Monaco,
        TrackID.Montreal,
        TrackID.Losail,
        TrackID.Paul_Ricard,
    }

    @staticmethod
    def millisecondsToMinutesSecondsMilliseconds(milliseconds: int) -> str:
        """
        Convert milliseconds to a formatted string in the format "MM:SS.SSS".

        Args:
            milliseconds (int): The input time in milliseconds.

        Returns:
            str: The formatted time string.
        """
        if not isinstance(milliseconds, int):
            raise ValueError("Input must be an integer representing milliseconds")

        if milliseconds < 0:
            raise ValueError("Input must be a non-negative integer")

        total_seconds, milliseconds = divmod(milliseconds, 1000)
        minutes, seconds = divmod(total_seconds, 60)

        return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

    @staticmethod
    def millisecondsToSecondsMilliseconds(milliseconds: int) -> str:
        """
        Convert milliseconds to a formatted string in the format "SS.SSS".

        Args:
            milliseconds (int): The input time in milliseconds.

        Returns:
            str: The formatted time string.
        """
        if not isinstance(milliseconds, int):
            raise ValueError("Input must be an integer representing milliseconds")

        if milliseconds < 0:
            raise ValueError("Input must be a non-negative integer")

        seconds, milliseconds = divmod(milliseconds, 1000)

        return f"{seconds}.{milliseconds:03}"

    @staticmethod
    def secondsToMinutesSecondsMilliseconds(seconds: float) -> str:
        """
        Convert seconds to a formatted string in the format "MM:SS.SSS".

        Args:
            seconds (float): The input time in seconds.

        Returns:
            str: The formatted time string.
        """
        if not isinstance(seconds, float):
            raise ValueError("Input must be a float representing seconds")

        if seconds < 0:
            raise ValueError("Input must be a non-negative float")

        total_milliseconds = int(seconds * 1000)
        minutes, seconds = divmod(total_milliseconds // 1000, 60)
        milliseconds = total_milliseconds % 1000

        return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

    @staticmethod
    def floatSecondsToMinutesSecondsMilliseconds(seconds: float) -> str:
        """
        Convert float seconds to a formatted string in the format "MM:SS.SSS".

        Args:
            seconds (float): The input time in seconds.

        Returns:
            str: The formatted time string.
        """
        if not isinstance(seconds, float):
            raise ValueError("Input must be a float representing seconds")

        if seconds < 0:
            raise ValueError("Input must be a non-negative float")

        total_milliseconds = int(seconds * 1000)
        minutes, seconds = divmod(total_milliseconds // 1000, 60)
        milliseconds = total_milliseconds % 1000

        return f"{minutes:02}:{seconds:02}.{milliseconds:03}"

    @staticmethod
    def floatSecondsToSecondsMilliseconds(seconds: float) -> str:
        """
        Convert float seconds to a formatted string in the format "MM:SS.SSS".

        Args:
            seconds (float): The input time in seconds.

        Returns:
            str: The formatted time string.
        """
        if not isinstance(seconds, float):
            raise ValueError("Input must be a float representing seconds")

        if seconds < 0:
            raise ValueError("Input must be a non-negative float")

        total_milliseconds = int(seconds * 1000)
        _, seconds = divmod(total_milliseconds // 1000, 60)
        milliseconds = total_milliseconds % 1000

        return f"{seconds}.{milliseconds:03}"

    @staticmethod
    def timeStrToMilliseconds(time_str: str) -> int:
        """
        Convert a time string in the format "MM:SS.SSS" to milliseconds.

        Args:
            time_str (str): The input time string.

        Returns:
            int: The time in milliseconds.
        """
        minutes, seconds_with_milliseconds = [str(item) for item in time_str.split(':')]
        seconds, milliseconds = [int(item) for item in seconds_with_milliseconds.split('.')]
        total_milliseconds = int(minutes) * 60 * 1000 + seconds * 1000 + milliseconds
        return total_milliseconds

    @staticmethod
    def floatToStr(float_val : float, num_dec_places : Optional[int] = 2) -> str:
        """
        Convert a float to a string with a specified number of decimal places.

        Parameters:
        - float_val (float): The float value to convert.
        - num_dec_places (Optional[int]): Number of decimal places (default is 2).

        Returns:
        - str: The formatted string.
        """
        format_string = "{:." + str(num_dec_places) + "f}"
        return format_string.format(float_val)

    @staticmethod
    def isFinishLineAfterPitGarage(track_id: TrackID) -> bool:
        """In this track, is the finish line after the pit garage?

        Args:
            track_id (TrackID): The track ID enum (assumed to be valid)

        Returns:
            bool: True if finish line after pit garage, else False
        """

        return (track_id in F1Utils.TRACKS_WHERE_FINISH_LINE_AFTER_PIT_GARAGE)

# -------------------- HEADER PARSING ------------------------------------------

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

    PACKET_FORMAT = ("<"
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
    PACKET_LEN: int = struct.calcsize(PACKET_FORMAT)

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
        unpacked_data = struct.unpack(self.PACKET_FORMAT, data)

        # Assign values to individual variables
        self.m_packetFormat, self.m_gameYear, self.m_gameMajorVersion, self.m_gameMinorVersion, \
        self.m_packetVersion, self.m_packetId, self.m_sessionUID, self.m_sessionTime, \
        self.m_frameIdentifier, self.m_overallFrameIdentifier, self.m_playerCarIndex, \
        self.m_secondaryPlayerCarIndex = unpacked_data

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
