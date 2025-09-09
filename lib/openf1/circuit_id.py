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
from typing import Dict

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

_CIRCUIT_ID_MAP: Dict[TrackID, OpenF1CircuitID] = {
    TrackID.Sakhir_Bahrain: OpenF1CircuitID.SAKHIR,
    TrackID.Jeddah: OpenF1CircuitID.JEDDAH,
    TrackID.Melbourne: OpenF1CircuitID.MELBOURNE,
    TrackID.Suzuka: OpenF1CircuitID.SUZUKA,
    TrackID.Shanghai: OpenF1CircuitID.SHANGHAI,
    TrackID.Miami: OpenF1CircuitID.MIAMI,
    TrackID.Imola: OpenF1CircuitID.IMOLA,
    TrackID.Monaco: OpenF1CircuitID.MONTE_CARLO,
    TrackID.Montreal: OpenF1CircuitID.MONTREAL,
    TrackID.Catalunya: OpenF1CircuitID.CATALUNYA,
    TrackID.Austria: OpenF1CircuitID.SPIELBERG,
    TrackID.Silverstone: OpenF1CircuitID.SILVERSTONE,
    TrackID.Hungaroring: OpenF1CircuitID.HUNGARORING,
    TrackID.Spa: OpenF1CircuitID.SPA_FRANCORCHAMPS,
    TrackID.Zandvoort: OpenF1CircuitID.ZANDVOORT,
    TrackID.Monza: OpenF1CircuitID.MONZA,
    TrackID.Baku_Azerbaijan: OpenF1CircuitID.BAKU,
    TrackID.Singapore: OpenF1CircuitID.SINGAPORE,
    TrackID.Texas: OpenF1CircuitID.AUSTIN,
    TrackID.Mexico: OpenF1CircuitID.MEXICO_CITY,
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
