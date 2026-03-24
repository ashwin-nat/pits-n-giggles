# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

import json
from pathlib import Path
from typing import Dict, Iterator, Optional

from .segments import TrackSegments
from .types import BaseSegmentInfo

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

class TrackSegmentsDatabase:
    """
    Loads all JSON track-segment files from a directory and provides lookup
    by circuit name.

    Parameters
    ----------
    path : str | Path
        Directory containing JSON files, each with the structure expected by
        :meth:`TrackSegments.load_track_data`.
    """

    def __init__(self, path: "str | Path") -> None:
        self._db: Dict[str, TrackSegments] = {}
        for json_file in Path(path).glob("*.json"):
            with json_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            ts = TrackSegments()
            ts.load_track_data(data)
            if ts.circuit_name is not None:
                self._db[ts.circuit_name] = ts

    def get_segment_info(self, circuit_name: str, lap_distance: float) -> Optional[BaseSegmentInfo]:
        """
        Return segment info for *circuit_name* at *lap_distance*, or ``None``
        if the circuit is unknown or the position falls outside any segment.
        """
        ts = self._db.get(circuit_name)
        if ts is None:
            return None
        return ts.get_segment_info(lap_distance)

    def get(self, circuit_name: str) -> Optional[TrackSegments]:
        """Return the :class:`TrackSegments` for *circuit_name*, or ``None``."""
        return self._db.get(circuit_name)

    def __getitem__(self, circuit_name: str) -> TrackSegments:
        return self._db[circuit_name]

    def __contains__(self, circuit_name: str) -> bool:
        return circuit_name in self._db

    def __iter__(self) -> Iterator[str]:
        return iter(self._db)

    def __len__(self) -> int:
        return len(self._db)
