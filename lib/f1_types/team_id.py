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

from typing import Type, Union

from .base_pkt import F1BaseEnum

# ----------------------------- BASE ---------------------------------------------------------------------------------

class TeamID(F1BaseEnum):
    """Base Enum class for Team IDs."""
    pass

# ----------------------------- F1 2023 ------------------------------------------------------------------------------

class TeamID23(TeamID):
    """Team IDs for F1 2023."""

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

# ----------------------------- F1 2024 ------------------------------------------------------------------------------

class TeamID24(TeamID):
    """Team IDs for F1 2024."""

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
        teams_mapping = {
            0: "Mercedes", 1: "Ferrari", 2: "Red Bull Racing",
            3: "Williams", 4: "Aston Martin", 5: "Alpine",
            6: "VCARB", 7: "Haas", 8: "McLaren",
            9: "Sauber", 41: "Generic", 104: "Custom",
            255: "MY_TEAM"
        }
        return teams_mapping.get(self.value,
                                 ' '.join(word.capitalize() for word in self.name.split('_')))

# ----------------------------- F1 2025 ------------------------------------------------------------------------------

class TeamID25(TeamID):
    """Team IDs for F1 2025."""

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

    def __str__(self) -> str:
        if self.value == 255:
            return self.name
        if self.value == 6:
            return "RB"
        return (
            self.name.replace("_", " ").title()
            .replace("Gp", "GP")
            .replace(" 24", " '24")
            .replace(" 25", " '25")
        )

# ----------------------------- F1 2026 ------------------------------------------------------------------------------

class TeamID26(TeamID):
    """Team IDs for the F1 25: 2026 Season Pack."""

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
    ART_GP_25 = 465
    CAMPOS_25 = 466
    RODIN_MOTORSPORT_25 = 467
    AIX_RACING_25 = 468
    DAMS_25 = 469
    HITECH_25 = 470
    MP_MOTORSPORT_25 = 471
    PREMA_25 = 472
    TRIDENT_25 = 473
    VAN_AMERSFOORT_RACING_25 = 474
    INVICTA_25 = 475
    MERCEDES_26 = 476
    FERRARI_26 = 477
    RED_BULL_RACING_26 = 478
    WILLIAMS_26 = 479
    ASTON_MARTIN_26 = 480
    ALPINE_26 = 481
    RB_26 = 482
    HAAS_26 = 483
    MCLAREN_26 = 484
    AUDI_26 = 485
    CADILLAC_26 = 486

    def __str__(self) -> str:
        if self.value == 255:
            return self.name
        if self.value in {6, 482}:
            return "RB"
        return (
            self.name.replace("_", " ").title()
            .replace("Gp", "GP")
            .replace("Rb", "RB")
            .replace(" 24", " '24")
            .replace(" 25", " '25")
            .replace(" 26", " '26")
        )

# ----------------------------- FACTORY FUNCTIONS --------------------------------------------------------------------

def get_team_id(value: int, packet_format: int) -> Union[TeamID23, TeamID24, TeamID25, TeamID26]:
    """Cast a raw integer to the appropriate TeamID enum for the given packet format.

    Args:
        value: Raw integer team ID from the UDP packet.
        packet_format: The packet format year (e.g. 2023, 2024, 2025, 2026).

    Returns:
        The corresponding TeamID enum member, or the raw value if unrecognised.
    """
    return get_team_id_class(packet_format).safeCast(value)


def get_team_id_class(packet_format: int) -> Type[TeamID]:
    """Return the TeamID enum class for the given packet format.

    Useful when you need the full set of valid IDs for a season, e.g.
    ``random.choice(list(get_team_id_class(2026)))``.

    Args:
        packet_format: The packet format year (e.g. 2023, 2024, 2025, 2026).

    Returns:
        The TeamID subclass corresponding to that season.
    """
    if packet_format == 2023:
        return TeamID23
    if packet_format == 2024:
        return TeamID24
    if packet_format == 2025:
        return TeamID25
    return TeamID26  # 2026+
