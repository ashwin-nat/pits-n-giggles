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

## NOTE: Please refer to the F1 UDP specification document to understand fully how the telemetry data works.
## All classes in supported in this library are documented with the members, but it is still recommended to read the
## official document.
## F1 23 - https://answers.ea.com/t5/General-Discussion/F1-23-UDP-Specification/m-p/12633159
## F1 24 - https://answers.ea.com/t5/General-Discussion/F1-24-UDP-Specification/td-p/13745220
## F1 25 - https://forums.ea.com/blog/f1-games-game-info-hub-en/ea-sports%E2%84%A2-f1%C2%AE25-udp-specification/12187347

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from abc import abstractmethod
from typing import List, Optional, Set

from .base_pkt import F1BaseEnum, F1CompareableEnum

# -------------------- COMMON CLASSES ----------------------------------------------------------------------------------

class ResultStatus(F1BaseEnum):
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

class ResultReason(F1BaseEnum):
    """
    Enumeration representing the result reason of a driver after a racing session.
    """

    INVALID = 0
    RETIRED = 1
    FINISHED = 2
    TERMINAL_DAMAGE = 3
    INACTIVE = 4
    NOT_ENOUGH_LAPS_COMPLETED = 5
    BLACK_FLAGGED = 6
    RED_FLAGGED = 7
    MECHANICAL_FAILURE = 8
    SESSION_SKIPPED = 9
    SESSION_SIMULATED = 10

    def __str__(self) -> str:
        """String representation

        Returns:
            str: String representation
        """
        return self.name.lower()

class SessionType(F1BaseEnum):

    @abstractmethod
    def isFpTypeSession(self) -> bool:
        """
        Check if the session type is a free practice session.

        Returns:
            bool: True if the session type is a free practice session, False otherwise.
        """
        pass

    @abstractmethod
    def isQualiTypeSession(self) -> bool:
        """
        Check if the session type is a qualifying session.

        Returns:
            bool: True if the session type is a qualifying session, False otherwise.
        """
        pass

    @abstractmethod
    def isRaceTypeSession(self) -> bool:
        """
        Check if the session type is a race session.

        Returns:
            bool: True if the session type is a race session, False otherwise.
        """
        pass

    @abstractmethod
    def isTimeTrialTypeSession(self) -> bool:
        """
        Check if the session type is a time trial session.

        Returns:
            bool: True if the session type is a time trial session, False otherwise.
        """
        pass

class SessionType23(SessionType):
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

    def __str__(self) -> str:
        """String representation

        Returns:
            str: String representation
        """
        return self.name.title()

    def isFpTypeSession(self) -> bool:
        """
        Check if the session type is a free practice session.

        Returns:
            bool: True if the session type is a free practice session, False otherwise.
        """
        return self in {
            SessionType23.PRACTICE_1,
            SessionType23.PRACTICE_2,
            SessionType23.PRACTICE_3,
            SessionType23.SHORT_PRACTICE,
        }

    def isQualiTypeSession(self) -> bool:
        """
        Check if the session type is a qualifying session.

        Returns:
            bool: True if the session type is a qualifying session, False otherwise.
        """
        return self in {
            SessionType23.QUALIFYING_1,
            SessionType23.QUALIFYING_2,
            SessionType23.QUALIFYING_3,
            SessionType23.SHORT_QUALIFYING,
            SessionType23.ONE_SHOT_QUALIFYING,
        }

    def isRaceTypeSession(self) -> bool:
        """
        Check if the session type is a race session.

        Returns:
            bool: True if the session type is a race session, False otherwise.
        """
        return self in {
            SessionType23.RACE,
            SessionType23.RACE_2,
            SessionType23.RACE_3,
        }

    def isTimeTrialTypeSession(self) -> bool:
        """
        Check if the session type is a time trial session.

        Returns:
            bool: True if the session type is a time trial session, False otherwise.
        """
        return self == SessionType23.TIME_TRIAL

class SessionType24(SessionType):
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
    SPRINT_SHOOTOUT_1 = 10
    SPRINT_SHOOTOUT_2 = 11
    SPRINT_SHOOTOUT_3 = 12
    SHORT_SPRINT_SHOOTOUT = 13
    ONE_SHOT_SPRINT_SHOOTOUT = 14
    RACE = 15
    RACE_2 = 16
    RACE_3 = 17
    TIME_TRIAL = 18

    def __str__(self):
        """
        Return a string representation of the SessionType24 with spaces.

        Returns:
            str: String representation of the SessionType24.
        """
        return self.name.replace('_', ' ').title()

    def isFpTypeSession(self) -> bool:
        """
        Check if the session type is a free practice session.

        Returns:
            bool: True if the session type is a free practice session, False otherwise.
        """
        return self in {
            SessionType24.PRACTICE_1,
            SessionType24.PRACTICE_2,
            SessionType24.PRACTICE_3,
            SessionType24.SHORT_PRACTICE,
        }

    def isQualiTypeSession(self) -> bool:
        """
        Check if the session type is a qualifying session.

        Returns:
            bool: True if the session type is a qualifying session, False otherwise.
        """
        return self in {
            SessionType24.QUALIFYING_1,
            SessionType24.QUALIFYING_2,
            SessionType24.QUALIFYING_3,
            SessionType24.SHORT_QUALIFYING,
            SessionType24.ONE_SHOT_QUALIFYING,
            SessionType24.SPRINT_SHOOTOUT_1,
            SessionType24.SPRINT_SHOOTOUT_2,
            SessionType24.SPRINT_SHOOTOUT_3,
            SessionType24.SHORT_SPRINT_SHOOTOUT,
            SessionType24.ONE_SHOT_SPRINT_SHOOTOUT,
        }

    def isRaceTypeSession(self) -> bool:
        """
        Check if the session type is a race session.

        Returns:
            bool: True if the session type is a race session, False otherwise.
        """
        return self in {
            SessionType24.RACE,
            SessionType24.RACE_2,
            SessionType24.RACE_3,
        }

    def isTimeTrialTypeSession(self) -> bool:
        """
        Check if the session type is a time trial session.

        Returns:
            bool: True if the session type is a time trial session, False otherwise.
        """
        return self == SessionType24.TIME_TRIAL

class SessionLength(F1BaseEnum):
    """
    Enum class representing F1 session lengths.
    """
    NONE = 0
    VERY_SHORT = 2
    SHORT = 3
    MEDIUM = 4
    MEDIUM_LONG = 5
    LONG = 6
    FULL = 7

    def __str__(self):
        """
        Return a string representation of the SessionType23 with spaces.

        Returns:
            str: String representation of the SessionType23.
        """
        return self.name.replace('_', ' ').title()

class ActualTyreCompound(F1BaseEnum):
    """
    Enumeration representing different tyre compounds used in Formula 1 and Formula 2.

    Attributes:
        C6 (int): F1 Modern - C6
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

    C6 = 22
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
    UNKNOWN = 255

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the tyre compound.

        Returns:
            str: String representation of the tyre compound.
        """
        return {
            ActualTyreCompound.C6: "C6",
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
            ActualTyreCompound.UNKNOWN: "Unknown",
        }[self]

class VisualTyreCompound(F1BaseEnum):
    """
    Enumeration representing different visual tyre compounds used in Formula 1 and Formula 2.

    Attributes:
        SOFT (int): Soft tyre compound
        MEDIUM (int): Medium tyre compound
        HARD (int): Hard tyre compound
        INTER (int): Intermediate tyre compound
        WET (int): Wet tyre compound
        WET_CLASSIC (int): Wet tyre compound (Classic)
        SUPER_SOFT (int): Super Soft tyre compound
        SOFT_F2 (int): Soft tyre compound
        MEDIUM_F2 (int): Medium tyre compound
        HARD_F2 (int): Hard tyre compound
        WET_F2 (int): Wet tyre compound

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
    UNKNOWN = 255

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
            VisualTyreCompound.WET_CLASSIC: "Wet",
            VisualTyreCompound.SUPER_SOFT: "Super Soft",
            VisualTyreCompound.SOFT_F2: "Soft",
            VisualTyreCompound.MEDIUM_F2: "Medium",
            VisualTyreCompound.HARD_F2: "Hard",
            VisualTyreCompound.WET_F2: "Wet",
            VisualTyreCompound.UNKNOWN: "Unknown",
        }[self]

class SafetyCarType(F1CompareableEnum):
    """
    Enumeration representing different safety car statuses.

    Attributes:
        NO_SAFETY_CAR (int): No safety car on the track.
        FULL_SAFETY_CAR (int): Full safety car deployed.
        VIRTUAL_SAFETY_CAR (int): Virtual safety car deployed.
        FORMATION_LAP (int): Formation lap in progress.

        Note:
            Each attribute represents a unique safety car status identified by an integer value.
    """

    NO_SAFETY_CAR = 0
    FULL_SAFETY_CAR = 1
    VIRTUAL_SAFETY_CAR = 2
    FORMATION_LAP = 3

class SafetyCarEventType(F1BaseEnum):
    """
    Enumeration representing different safety car statuses.

    Attributes:
        DEPLOYED (int): Safety car deployed
        RETURNING (int): Safety car returning
        RETURNED (int): Safety car returned
        RESUME_RACE (int): Resume race

        Note:
            Each attribute represents a unique safety car status identified by an integer value.
    """

    DEPLOYED = 0
    RETURNING = 1
    RETURNED = 2
    RESUME_RACE = 3

class Nationality(F1BaseEnum):
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

class Platform(F1BaseEnum):
    """
    Enumeration representing different gaming platforms.
    """
    NONE = 0
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
            Platform.NONE: "N/A",
            Platform.STEAM: "Steam",
            Platform.PLAYSTATION: "PlayStation",
            Platform.XBOX: "Xbox",
            Platform.ORIGIN: "Origin",
            Platform.UNKNOWN: "Unknown",
        }[self]

class TelemetrySetting(F1BaseEnum):
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
        return self.name.title()

    def __bool__(self) -> bool:
        """
        Returns True if the telemetry setting is public, False otherwise.

        Returns:
            bool: True if public, False otherwise.
        """
        return self == TelemetrySetting.PUBLIC

class TractionControlAssistMode(F1BaseEnum):
    """
    Enumeration representing different Traction Control Assist modes.

    Attributes:
        OFF: Off
        MEDIUM: Medium
        FULL: Full

        Note:
            Each attribute represents a unique ERS deployment mode identified by an integer value.
    """

    OFF = 0
    MEDIUM = 1
    FULL = 2

class GearboxAssistMode(F1BaseEnum):
    """
    Enumeration representing different Gearbox Control Assist modes.

    Attributes:
        MANUAL: Off
        MANUAL_WITH_SUGGESTED_GEAR: Manual Transmission with suggested gear
        AUTO: Full assist

        Note:
            Each attribute represents a unique ERS deployment mode identified by an integer value.
    """

    MANUAL = 1
    MANUAL_WITH_SUGGESTED_GEAR = 2
    AUTO = 3
    UNKNOWN = 0

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the Traction Control Assist mode.

        Returns:
            str: String representation of the Traction Control Assist mode.
        """
        return self.name.replace('_', ' ').title()

class TeamID(F1BaseEnum):
    """Base Enum class for Team ID's"""
    pass
class TeamID23(TeamID):
    """
    Enumeration representing the TeamID setting for the player (F1 2023)
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
    MY_TEAM = 255

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
            139: "Hitech '22", 140: "Art GP '22", 255: "MY_TEAM"
        }
        return teams_mapping.get(self.value, "---")

class TeamID24(TeamID):
    """
    Enumeration representing the TeamID setting for the player (F1 2023)
    """
    MERCEDES = 0
    FERRARI = 1
    RED_BULL_RACING = 2
    WILLIAMS = 3
    ASTON_MARTIN = 4
    ALPINE = 5
    RB = 6
    HAAS = 7
    MCLAREN = 8
    SAUBER = 9
    F1_GENERIC = 41
    F1_CUSTOM_TEAM = 104
    ART_GP_23 = 143
    CAMPOS_23 = 144
    CARLIN_23 = 145
    PHM_23 = 146
    DAMS_23 = 147
    HITECH_23 = 148
    MP_MOTORSPORT_23 = 149
    PREMA_23 = 150
    TRIDENT_23 = 151
    VAN_AMERSFOORT_RACING_23 = 152
    VIRTUOSI_23 = 153
    MY_TEAM = 255

    def __str__(self) -> str:
        """
        Returns the string representation of the enum member with each word capitalized.
        """

        teams_mapping = {
            0: "Mercedes", 1: "Ferrari", 2: "Red Bull Racing",
            3: "Williams", 4: "Aston Martin", 5: "Alpine",
            6: "VCARB", 7: "Haas", 8: "McLaren",
            9: "Sauber", 41: "Generic", 104: "Custom",
            255: "MY_TEAM"
        }
        return teams_mapping.get(self.value,
                                 ' '.join(word.capitalize() for word in self.name.split('_')))

class TeamID25(TeamID):
    MERCEDES = 0
    FERRARI = 1
    RED_BULL_RACING = 2
    WILLIAMS = 3
    ASTON_MARTIN = 4
    ALPINE = 5
    RB = 6
    HAAS = 7
    MCLAREN = 8
    SAUBER = 9
    F1_GENERIC = 41
    F1_CUSTOM_TEAM = 104
    KONNERSPORT = 129
    APXGP_24 = 142
    APXGP_25 = 154
    KONNERSPORT_24 = 155
    ART_GP_24 = 158
    CAMPOS_24 = 159
    RODIN_MOTORSPORT_24 = 160
    AIX_RACING_24 = 161
    DAMS_24 = 162
    HITECH_24 = 163
    MP_MOTORSPORT_24 = 164
    PREMA_24 = 165
    TRIDENT_24 = 166
    VAN_AMERSFOORT_RACING_24 = 167
    INVICTA_24 = 168
    MERCEDES_24 = 185
    FERRARI_24 = 186
    RED_BULL_RACING_24 = 187
    WILLIAMS_24 = 188
    ASTON_MARTIN_24 = 189
    ALPINE_24 = 190
    RB_24 = 191
    HAAS_24 = 192
    MCLAREN_24 = 193
    SAUBER_24 = 194
    MY_TEAM = 255

    def __str__(self):
        if self.value == 255:
            return self.name
        # Specific handling for RB
        if self.value == 6:
            return "RB"
        return self.name.replace("_", " ").title().replace("Gp", "GP").replace("24", "'24").replace("25", "'25")

class TrackID(F1BaseEnum):
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
    Silverstone_Reverse = 39
    Austria_Reverse = 40
    Zandvoort_Reverse = 41

    def __str__(self):
        """
        Returns a string representation of the track.
        """
        return {
            "Paul_Ricard": "Paul Ricard",
            "Sakhir_Bahrain": "Sakhir",
            "Abu_Dhabi": "Abu Dhabi",
            "Baku_Azerbaijan": "Baku",
            "Silverstone_Reverse": "Silverstone_Reverse",
            "Austria_Reverse": "Austria_Reverse",
            "Zandvoort_Reverse": "Zandvoort_Reverse",
        }.get(self.name, self.name.replace("_", " "))

class GameMode(F1BaseEnum):
    """
    Enum representing various game modes.

    Attributes:
        EVENT_MODE (int): Event Mode
        GRAND_PRIX (int): Grand Prix
        GRAND_PRIX_23 (int): Grand Prix ‘23
        TIME_TRIAL (int): Time Trial
        SPLITSCREEN (int): Splitscreen
        ONLINE_CUSTOM (int): Online Custom
        ONLINE_LEAGUE (int): Online League
        CAREER_INVITATIONAL (int): Career Invitational
        CHAMPIONSHIP_INVITATIONAL (int): Championship Invitational
        CHAMPIONSHIP (int): Championship
        ONLINE_CHAMPIONSHIP (int): Online Championship
        ONLINE_WEEKLY_EVENT (int): Online Weekly Event
        STORY_MODE (int): Story Mode
        CAREER_22 (int): Career ‘22
        CAREER_22_ONLINE (int): Career '22 Online
        CAREER_23 (int): Career ‘23
        CAREER_23_ONLINE (int): Career '23 Online
        DRIVER_CAREER_24 (int): Driver Career ‘24
        CAREER_24_ONLINE (int): Career '24 Online
        MY_TEAM_CAREER_24 (int): My Team Career ‘24
        CURATED_CAREER_24 (int): Curated Career ‘24
        BENCHMARK (int): Benchmark
    """

    EVENT_MODE = 0
    GRAND_PRIX = 3
    GRAND_PRIX_23 = 4
    TIME_TRIAL = 5
    SPLITSCREEN = 6
    ONLINE_CUSTOM = 7
    ONLINE_LEAGUE = 8
    CAREER_INVITATIONAL = 11
    CHAMPIONSHIP_INVITATIONAL = 12
    CHAMPIONSHIP = 13
    ONLINE_CHAMPIONSHIP = 14
    ONLINE_WEEKLY_EVENT = 15
    STORY_MODE = 17
    CAREER_22 = 19
    CAREER_22_ONLINE = 20
    CAREER_23 = 21
    CAREER_23_ONLINE = 22
    DRIVER_CAREER_24 = 23
    CAREER_24_ONLINE = 24
    MY_TEAM_CAREER_24 = 25
    CURATED_CAREER_24 = 26
    MY_TEAM_CAREER_25 = 27
    DRIVER_CAREER_25 = 28
    CAREER_25_ONLINE = 29
    CHALLENGE_CAREER = 30
    APEX_STORY = 75
    BENCHMARK = 127

    def __str__(self) -> str:
        """Return a user-friendly string representation of the mode."""
        return self.name.replace("_", " ").title()

    def isOnlineMode(self) -> bool:
        """Check if the mode is an online mode."""
        return self in {
            GameMode.ONLINE_CUSTOM,
            GameMode.ONLINE_LEAGUE,
            GameMode.ONLINE_CHAMPIONSHIP,
            GameMode.ONLINE_WEEKLY_EVENT,
            GameMode.CAREER_22_ONLINE,
            GameMode.CAREER_23_ONLINE,
            GameMode.CAREER_24_ONLINE,
            GameMode.CAREER_25_ONLINE,
        }

class RuleSet(F1BaseEnum):
    """
    Enum representing various rulesets.

    Attributes:
        PRACTICE_QUALIFYING (int): Practice & Qualifying
        RACE (int): Race
        TIME_TRIAL (int): Time Trial
        TIME_ATTACK (int): Time Attack
        CHECKPOINT_CHALLENGE (int): Checkpoint Challenge
        AUTOCROSS (int): Autocross
        DRIFT (int): Drift
        AVERAGE_SPEED_ZONE (int): Average Speed Zone
        RIVAL_DUEL (int): Rival Duel
    """

    PRACTICE_QUALIFYING = 0
    RACE = 1
    TIME_TRIAL = 2
    TIME_ATTACK = 4
    CHECKPOINT_CHALLENGE = 6
    AUTOCROSS = 8
    DRIFT = 9
    AVERAGE_SPEED_ZONE = 10
    RIVAL_DUEL = 11

    def __str__(self) -> str:
        """Return a user-friendly string representation of the ruleset."""
        return self.name.replace("_", " & ").title()

class F1Utils:
    """
    Utility class for Formula 1-related operations.

    Constants:
        INDEX_REAR_LEFT (int): Index for the rear-left position in tyre/brake arrays/lists.
        INDEX_REAR_RIGHT (int): Index for the rear-right position in tyre/brake arrays/lists.
        INDEX_FRONT_LEFT (int): Index for the front-left position in tyre/brake arrays/lists.
        INDEX_FRONT_RIGHT (int): Index for the front-right position in tyre/brake arrays/lists.
        PLAYER_INDEX_INVALID (int): The constant representing invalid player index

        TRACKS_WHERE_FINISH_LINE_AFTER_PIT_GARAGE (Set[TrackID]):
            A set of track IDs where the finish line is after the pit garage.

        SECTOR_STATUS_NA (int): The constant representing sector status not available.
        SECTOR_STATUS_INVALID (int): The constant representing sector status invalid.
        SECTOR_STATUS_YELLOW (int): The constant representing sector status that is not PB or session best.
        SECTOR_STATUS_GREEN (int): The constant representing sector status PB but not session best.
        SECTOR_STATUS_PURPLE (int): The constant representing sector status session best.

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

    SECTOR_STATUS_NA = -2
    SECTOR_STATUS_INVALID = -1
    SECTOR_STATUS_YELLOW = 0
    SECTOR_STATUS_GREEN = 1
    SECTOR_STATUS_PURPLE = 2

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
        return int(minutes) * 60 * 1000 + seconds * 1000 + milliseconds

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
    def getLapTimeStrSplit(minutes_part: int, milliseconds_part: int) -> str:
        """Format the lap time string. (What a fuck all system of representing lap time)

        Args:
            minutes_part (int): The minutes part of the lap time
            milliseconds_part (int): The remainder of the lap time, in milliseconds

        Returns:
            str: String in the format of MM:SS.MS
        """

        # Convert total milliseconds to seconds and the remaining milliseconds
        total_seconds = milliseconds_part / 1000.0

        # Get the seconds part (without minutes)
        seconds = int(total_seconds)

        # Get the remaining milliseconds part
        remaining_milliseconds = int(milliseconds_part % 1000)

        # Format the string
        if minutes_part == 0:
            return f"{seconds}.{remaining_milliseconds:03}"
        return f"{minutes_part:02}:{seconds:02}.{remaining_milliseconds:03}"

    @staticmethod
    def getLapTimeStr(milliseconds: int) -> str:
        """Format the lap time string. (What a fuck all system of representing lap time)

        Args:
            milliseconds (int): The time in milliseconds

        Returns:
            str: String in the format of MM:SS.MS
        """

        seconds, ms = divmod(milliseconds, 1000)  # Get seconds and remaining milliseconds
        minutes, seconds = divmod(seconds, 60)    # Get minutes and remaining seconds

        if minutes > 0:
            return f"{int(minutes):02}:{int(seconds):02}.{int(ms):03}"
        return f"{int(seconds):02}.{int(ms):03}"

    @staticmethod
    def isFinishLineAfterPitGarage(track_id: TrackID) -> bool:
        """In this track, is the finish line after the pit garage?

        Args:
            track_id (TrackID): The track ID enum (assumed to be valid)

        Returns:
            bool: True if finish line after pit garage, else False
        """

        return (track_id in F1Utils.TRACKS_WHERE_FINISH_LINE_AFTER_PIT_GARAGE)

    @staticmethod
    def transposeLapPositions(lap_major: List[List[int]]) -> List[List[int]]:
        """
        Transpose a 2D list of lap position data from lap-major to car-major order.

        The input list is expected to have the format:
            lap_major[lap_index][car_index] -> position

        The output list will have the format:
            car_major[car_index][lap_index] -> position

        Args:
            lap_major (List[List[int]]): 2D list where each inner list represents
                                        the positions of all cars for a single lap.

        Returns:
            List[List[int]]: Transposed 2D list where each inner list represents
                            the positions of one car across all laps.

        Example:
            lap_major = [
                [1, 2, 3],  # lap 0
                [2, 1, 3],  # lap 1
            ]

            Result:
            [
                [1, 2],  # car 0
                [2, 1],  # car 1
                [3, 3],  # car 2
            ]
        """
        # Transpose using zip and map. zip(*lap_major) groups values per car index.
        return [list(car_lap_positions) for car_lap_positions in zip(*lap_major)]
