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

from typing import Any, Dict, List, Optional, Tuple

from apps.hud.common import get_adjacent_positions
from lib.track_segment_info import TrackSegmentsDatabase

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def sort_by_rel_distance(
    table_entries: List[Dict[str, Any]],
    ref_lap_dist: float,
    circuit_len: float,
) -> List[Tuple[float, Dict[str, Any]]]:
    """Return (rel_dist, row) sorted ascending: most ahead (negative) → ref (0) → most behind (positive).

    rel_dist = ref_pos - other_pos, normalized to (-circuit_len/2, +circuit_len/2] to handle lap boundary wrap.
    """
    ref_norm = ref_lap_dist % circuit_len
    half_len = circuit_len / 2
    result = []
    for row in table_entries:
        lap_dist = row.get("lap-info", {}).get("lap-distance")
        if lap_dist is None:
            continue
        rel = ref_norm - (lap_dist % circuit_len)
        if rel > half_len:
            rel -= circuit_len
        elif rel < -half_len:
            rel += circuit_len
        result.append((rel, row))
    result.sort(key=lambda x: x[0])
    return result


def get_traffic_window(
    sorted_entries: List[Tuple[float, Dict[str, Any]]],
    ref_pos: int,
    num_adjacent: int,
) -> List[Tuple[float, Dict[str, Any]]]:
    """Return up to num_adjacent ahead + ref + num_adjacent behind, clamped to available cars."""
    total = len(sorted_entries)
    lower_bound, upper_bound = get_adjacent_positions(ref_pos + 1, total, num_adjacent)
    if lower_bound is None:
        return [sorted_entries[ref_pos]]
    return sorted_entries[lower_bound - 1 : upper_bound]


def resolve_location(
    tracks_db: TrackSegmentsDatabase,
    circuit_num: Optional[int],
    lap_dist: Optional[float],
    sector: Optional[Any] = None,
) -> str:
    """Resolve a lap distance to a human-readable track location label (e.g. 'T3', 'T8-10').

    Falls back to sector if no segment is found.
    """
    fallback = str(sector) if sector is not None else "---"
    if circuit_num is None or lap_dist is None:
        return fallback
    segment = tracks_db.get_segment_info(circuit_num, lap_dist)
    if segment is None:
        return fallback
    match segment.TYPE:
        case "corner":
            return f"T{segment.corner_number}"
        case "complex_corner":
            first, last = segment.corner_numbers[0], segment.corner_numbers[-1]
            return f"T{first}-{last}"
        case _:
            return fallback

