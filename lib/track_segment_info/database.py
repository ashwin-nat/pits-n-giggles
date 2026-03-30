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
    by circuit number.

    Parameters
    ----------
    path : str | Path
        Directory containing JSON files, each with the structure expected by
        :meth:`TrackSegments.load_track_data`.
    """

    def __init__(self, path: "str | Path") -> None:
        base_path = Path(path)
        if not base_path.exists():
            raise FileNotFoundError(f"Track segments directory does not exist: {base_path}")
        if not base_path.is_dir():
            raise NotADirectoryError(f"Track segments path is not a directory: {base_path}")

        self._db: Dict[int, TrackSegments] = {}
        for json_file in base_path.glob("*.json"):
            with json_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            ts = TrackSegments()
            ts.load_track_data(data)
            if ts.circuit_number is not None:
                self._db[ts.circuit_number] = ts

    def get_segment_info(self, circuit_number: int, lap_distance: float) -> Optional[BaseSegmentInfo]:
        """
        Return segment info for *circuit_number* at *lap_distance*, or ``None``
        if the circuit is unknown or the position falls outside any segment.
        """
        ts = self._db.get(circuit_number)
        if ts is None:
            return None
        return ts.get_segment_info(lap_distance)

    def get(self, circuit_number: int) -> Optional[TrackSegments]:
        """Return the :class:`TrackSegments` for *circuit_number*, or ``None``."""
        return self._db.get(circuit_number)

    def __getitem__(self, circuit_number: int) -> TrackSegments:
        return self._db[circuit_number]

    def __contains__(self, circuit_number: int) -> bool:
        return circuit_number in self._db

    def __iter__(self) -> Iterator[int]:
        return iter(self._db)

    def __len__(self) -> int:
        return len(self._db)
