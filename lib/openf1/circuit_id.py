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

from enum import Enum
from lib.f1_types import TrackID

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class OpenF1CircuitID(Enum):
    SAKHIR = 63
    JEDDAH = 149
    MELBOURNE = 10
    SUZUKA = 46
    SHANGHAI = 49
    MIAMI = 151
    IMOLA = 6
    MONTE_CARLO = 22
    MONTREAL = 23
    CATALUNYA = 15
    SPIELBERG = 19
    SILVERSTONE = 2
    HUNGARORING = 4
    SPA_FRANCORCHAMPS = 7
    ZANDVOORT = 55
    MONZA = 39
    BAKU = 144
    SINGAPORE = 61
    AUSTIN = 9
    MEXICO_CITY = 65
    INTERLAGOS = 14
    LAS_VEGAS = 152
    LUSAIL = 150
    YAS_MARINA_CIRCUIT = 70

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_CIRCUIT_ID_MAP = {
    OpenF1CircuitID.SAKHIR: TrackID.Sakhir_Bahrain,
    OpenF1CircuitID.JEDDAH: TrackID.Jeddah,
    OpenF1CircuitID.MELBOURNE: TrackID.Melbourne,
    OpenF1CircuitID.SUZUKA: TrackID.Suzuka,
    OpenF1CircuitID.SHANGHAI: TrackID.Shanghai,
    OpenF1CircuitID.MIAMI: TrackID.Miami,
    OpenF1CircuitID.IMOLA: TrackID.Imola,
    OpenF1CircuitID.MONTE_CARLO: TrackID.Monaco,
    OpenF1CircuitID.MONTREAL: TrackID.Montreal,
    OpenF1CircuitID.CATALUNYA: TrackID.Catalunya,
    OpenF1CircuitID.SPIELBERG: TrackID.Austria,
    OpenF1CircuitID.SILVERSTONE: TrackID.Silverstone,
    OpenF1CircuitID.HUNGARORING: TrackID.Hungaroring,
    OpenF1CircuitID.SPA_FRANCORCHAMPS: TrackID.Spa,
    OpenF1CircuitID.ZANDVOORT: TrackID.Zandvoort,
    OpenF1CircuitID.MONZA: TrackID.Monza,
    OpenF1CircuitID.BAKU: TrackID.Baku_Azerbaijan,
    OpenF1CircuitID.SINGAPORE: TrackID.Singapore,
    OpenF1CircuitID.AUSTIN: TrackID.Texas,
    OpenF1CircuitID.MEXICO_CITY: TrackID.Mexico,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def to_openf1(track_id: TrackID) -> OpenF1CircuitID:
    """Get the OpenF1CircuitID for a given TrackID

    Args:
        track_id (TrackID): The track ID

    Returns:
        OpenF1CircuitID: OpenF1 API friendly circuit ID
    """
    return _CIRCUIT_ID_MAP.get(track_id)
