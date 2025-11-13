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

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtGui import QIcon

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def load_icon(relative_path: str) -> QIcon:
    """
    Load an icon that works in both dev and PyInstaller builds.

    Args:
        relative_path: Path to the icon file, relative to the project root or build bundle.

    Returns:
        QIcon: The loaded icon, or an empty QIcon if loading fails.
    """
    try:
        if hasattr(sys, "_MEIPASS"):
            # Running inside a PyInstaller bundle
            base_path = sys._MEIPASS
        else:
            # Running from source
            base_path = os.path.abspath(".")

        # TODO - caching
        full_path = os.path.join(base_path, relative_path)
        icon = QIcon(full_path)
        return icon

    except Exception as e:  # pylint: disable=broad-except
        return QIcon()

# ------------------------------------------------
# Session type helpers
# ------------------------------------------------

def is_race_type_session(session_type: str) -> bool:
    """Helper to determine if the session type is a race type session."""
    return "Race" in session_type

def is_tt_session(session_type: str) -> bool:
    """Helper to determine if the session type is a time trial session."""
    return session_type == "Time Trial"

def is_practice_session(session_type: str) -> bool:
    """Helper to determine if the session type is a practice session."""
    return session_type == "Practice"

def is_qualifying_session(session_type: str) -> bool:
    """Helper to determine if the session type is a qualifying session."""
    substr = {"Qualifying" or "Shootout"}
    for sub in substr:
        if sub in session_type:
            return True
    return False

# ------------------------------------------------
# Race table helpers
# ------------------------------------------------

def get_ref_row_index(self, data: Dict[str, Any]) -> Optional[int]:
    """Helper to get the reference row index from incoming race table data.

    Args:
        data (Dict[str, Any]): The incoming data from the server (top level, including all keys)

    Returns:
        Optional[int]: The index of the reference row, or None if not found.
    """
    if not data or "table-entries" not in data or not data["table-entries"]:
        return None

    is_spectating = data.get("is-spectating", False)
    spectator_index = data.get("spectator-car-index")

    if is_spectating and spectator_index is not None:
        if 0 <= spectator_index < len(data["table-entries"]):
            return spectator_index
        self.logger.warning(f"Warning: Spectator index {spectator_index} is out of bounds.")
        return None

    return next(
        (
            index
            for index, row in enumerate(data["table-entries"])
            if row.get("driver-info", {}).get("is-player") is True
        ),
        None,
    )

def get_ref_row(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Helper to get the reference row from incoming race table data.

    Args:
        data (Dict[str, Any]): The incoming data from the server (top level, including all keys)

    Returns:
        Optional[Dict[str, Any]]: The reference row, or None if not found.
    """

    ref_index = get_ref_row_index(data)
    return None if ref_index is None else data["table-entries"][ref_index]

def get_relevant_race_table_rows(
    sorted_table_entries: Dict[str, Any],
    ref_index: int,
    num_adjacent_cars: int
) -> List[Dict[str, Any]]:
    ref_row = next(
        (row for row in sorted_table_entries if row["driver-info"]["index"] == ref_index),
        None
    )
    if not ref_row:
        return []

    ref_position = ref_row["driver-info"]["position"]
    total_cars = len(sorted_table_entries)
    lower_bound, upper_bound = get_adjacent_positions(ref_position, total_cars, num_adjacent_cars)

    if lower_bound is None:
        return []

    lower_index = lower_bound - 1
    result = sorted_table_entries[lower_index:upper_bound]

    if total_cars >= 5:
        assert len(result) == 5
    else:
        assert len(result) == total_cars

    return result

def get_adjacent_positions(position: int, total_cars: int, num_adjacent_cars: int) -> Optional[Tuple[int, int]]:
    """Helper to get the lower and upper bounds of the window of num_adjacent_cars on each side of the position.

    Args:
        position (int): The position of the reference car.
        total_cars (int): The total number of cars in the race.
        num_adjacent_cars (int): The number of adjacent cars to include in the window.

    Returns:
        Optional[Tuple[int, int]]: The lower and upper bounds of the window of num_adjacent_cars on each side of the position,
        or None if the position is out of bounds.
    """
    if not (1 <= position <= total_cars):
        return None, None

    min_valid_lower_bound = 1
    max_valid_upper_bound = total_cars

    # Calculate a window of num_adjacent_cars on each side of the position (inclusive bounds).
    # If the window exceeds valid bounds, shift it towards the center while capping at boundaries
    # to ensure lower_bound stays >= 1 and upper_bound stays <= total_cars.
    lower_bound = position - num_adjacent_cars
    upper_bound = position + num_adjacent_cars

    # Adjust if window exceeds boundaries
    if lower_bound < min_valid_lower_bound:
        shift = min_valid_lower_bound - lower_bound
        lower_bound = min_valid_lower_bound
        upper_bound = min(upper_bound + shift, max_valid_upper_bound)

    if upper_bound > max_valid_upper_bound:
        shift = upper_bound - max_valid_upper_bound
        upper_bound = max_valid_upper_bound
        lower_bound = max(lower_bound - shift, min_valid_lower_bound)

    return lower_bound, upper_bound

def insert_relative_deltas_race(relevant_rows, ref_index) -> None:
    if ref_index is None:
        return

    # Map driver index --> position in relevant_rows
    index_to_pos = {
        row["driver-info"]["index"]: i for i, row in enumerate(relevant_rows)
    }

    ref_pos = index_to_pos.get(ref_index)
    if ref_pos is None:
        return

    # For each car, sum the deltas between it and the reference car;
    # cars ahead get negative values, cars behind get positive values.
    for i, row in enumerate(relevant_rows):
        if i == ref_pos:
            row["delta-info"]["relative-delta"] = 0
            continue

        if i < ref_pos:
            # Car(s) ahead of reference
            total_delta = sum(
                relevant_rows[j + 1]["delta-info"]["delta-to-car-in-front"]
                for j in range(i, ref_pos)
            )
            row["delta-info"]["relative-delta"] = -total_delta
        else:
            total_delta = sum(
                relevant_rows[j + 1]["delta-info"]["delta-to-car-in-front"]
                for j in range(ref_pos, i)
            )
            row["delta-info"]["relative-delta"] = total_delta

