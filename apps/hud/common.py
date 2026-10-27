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

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union

from lib.config import TimingTowerTyreInfoMode
from lib.f1_types import F1Utils


# -------------------------------------- TYPES -------------------------------------------------------------------------

JSONType = Union[dict, list, str, int, float, bool, None]

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

ERS_MODE_COLOR_DEFAULT = "#444444"
ERS_MODE_COLORS: defaultdict = defaultdict(lambda: ERS_MODE_COLOR_DEFAULT, {
    "Medium":   "#e6d800",
    "Hotlap":   "#00e676",
    "Overtake": "#ff1744",
})

def get_ers_mode_color(ers_mode: str, is_f126: bool = False, overtake_active: bool = False) -> str:
    """Return ERS mode colour. In 2026, Overtake colour depends on overtake_active."""
    if is_f126 and ers_mode == "Overtake":
        return "#41bff3" if overtake_active else "#ff1744"
    return ERS_MODE_COLORS[ers_mode]

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

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
    substrings = {"Qualifying", "Shootout"}
    return any(sub in session_type for sub in substrings)

# ------------------------------------------------
# Race table helpers
# ------------------------------------------------

def get_ref_row_index(data: Dict[str, Any]) -> Optional[int]:
    """Helper to get the reference row index from incoming race table data.

    Args:
        data (Dict[str, Any]): The incoming data from the server (top level, including all keys)

    Returns:
        Optional[int]: The index of the reference row, or None if not found.
    """
    if not data or "table-entries" not in data or not data["table-entries"]:
        return None

    pre_computed_idx = data.get("ref-row-index")
    if pre_computed_idx is not None:
        return pre_computed_idx

    is_spectating = data.get("is-spectating", False)
    spectator_index = data.get("spectator-car-index")

    if is_spectating and spectator_index is not None:
        return next(
            (
                index
                for index, row in enumerate(data["table-entries"])
                if row.get("driver-info", {}).get("index") == spectator_index
            ),
            None,
        )

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

    table_entries = data.get("table-entries")
    ref_index = get_ref_row_index(data)
    if ref_index is None:
        return None

    return table_entries[ref_index]

def get_relevant_race_table_rows(
    sorted_table_entries: Dict[str, Any],
    num_adjacent_cars: int,
    ref_index: Optional[int] = None
) -> List[Dict[str, Any]]:

    if ref_index is None:
        ref_row = get_ref_row(sorted_table_entries)
    else:
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

# ------------------------------------------------
# Race table cell formatters (shared by timing tower and rivals status)
# ------------------------------------------------

def get_overtake_bar_active(row: Dict[str, Any]) -> bool:
    """DRS (pre-2026) or overtake available (2026+) for a race table row."""
    regs_2026_info = row["2026-regs-info"]
    if not regs_2026_info["2026-regs-enabled"]:
        return row["driver-info"]["drs"]
    return regs_2026_info["overtake-avlb"]

def get_overtake_bar_color(row: Dict[str, Any]) -> str:
    """Overtake bar colour: grey when inactive, blue in 2026+, green for DRS before that."""
    if not get_overtake_bar_active(row):
        return "#333333"
    return "#00b0ff" if row["2026-regs-info"]["2026-regs-enabled"] else "#00e676"

def format_ers(ers_info: Dict[str, Any], telemetry_public: bool) -> str:
    """ERS store percentage, or N/A when the driver's telemetry is private."""
    if not telemetry_public:
        return "N/A"
    ers_perc = ers_info.get("ers-percent-float", 0.0)
    return f"{F1Utils.formatFloat(ers_perc, precision=0, signed=False)}%"

def get_ers_cell_fields(row: Dict[str, Any], telemetry_public: bool) -> Dict[str, str]:
    """QML role values for the ERS/DRS column: ers, ersMode, ersColor, overtakeBarColor."""
    ers_info: Dict[str, Any] = row["ers-info"]
    regs_info: Dict[str, Any] = row["2026-regs-info"]
    ers_mode = ers_info["ers-mode"]
    return {
        "ers": format_ers(ers_info, telemetry_public),
        "ersMode": ers_mode,
        "ersColor": get_ers_mode_color(
            ers_mode, regs_info["2026-regs-enabled"], regs_info["overtake-active"]),
        "overtakeBarColor": get_overtake_bar_color(row),
    }

def format_wing_dmg(dmg_info: Dict[str, Any], telemetry_public: bool) -> str:
    """Front wing damage as 'left-right', or N/A when the driver's telemetry is private."""
    if not telemetry_public:
        return "N/A"
    return f"{dmg_info.get('fl-wing-damage', '---')}-{dmg_info.get('fr-wing-damage', '---')}"

def get_wing_dmg_cell_fields(dmg_info: Dict[str, Any], telemetry_public: bool) -> Dict[str, str]:
    """QML role values for the wing damage column: wingDmg, wingDmgColor."""
    wing_dmg = format_wing_dmg(dmg_info, telemetry_public)
    return {"wingDmg": wing_dmg, "wingDmgColor": "#666666" if wing_dmg == "N/A" else "#ff9944"}

def format_tyre_wear(tyre_info: Dict[str, Any], telemetry_public: bool, mode: TimingTowerTyreInfoMode) -> str:
    """Tyre column text per the tyre info mode. tyre-info keys are subscripted on purpose: the producer guarantees them."""
    if mode is TimingTowerTyreInfoMode.TYRE_AGE:
        return f"{tyre_info['tyre-age']}L"

    wear = tyre_info["current-wear"]
    if telemetry_public and wear:
        max_wear = F1Utils.getMaxTyreWear(wear)
        return f"{F1Utils.formatFloat(max_wear['max-wear'], 0)}%"

    # Wear is unavailable. Hybrid falls back to age, wear-only mode shows a dash.
    if mode is TimingTowerTyreInfoMode.TYRE_WEAR:
        return "--"

    return f"{tyre_info['tyre-age']}L"
