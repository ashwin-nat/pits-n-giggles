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

import logging
from typing import Any, Dict, Optional

from .common import _get_race_table_context

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

FUEL_INFO_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        # ---- base_rsp ----
        "available": {"type": "boolean"},
        "connected": {"type": "boolean"},
        "last-update-timestamp": {"type": ["number", "null"]},

        "ok": {"type": "boolean"},
        "error": {"type": ["string", "null"]},

        # ---- resolved driver ----
        "driver_index": {"type": ["integer", "null"]},
        "driver_name": {"type": ["string", "null"]},

        # ---- raw fuel state ----
        "fuel_in_tank_kg": {
            "type": ["number", "null"],
            "description": "Current fuel mass remaining in tank (kg)",
        },
        "fuel_capacity_kg": {
            "type": ["number", "null"],
            "description": "Total fuel tank capacity (kg)",
        },
        "fuel_mix": {
            "type": ["string", "null"],
            "description": "Current fuel mix setting (Lean / Standard / Rich / Max)",
        },

        # ---- burn history ----
        "last_lap_fuel_used_kg": {
            "type": ["number", "null"],
            "description": "Actual fuel consumed during the last completed lap (kg)",
        },
        "avg_burn_rate_kg_per_lap": {
            "type": ["number", "null"],
            "description": (
                "Rolling average fuel burn rate computed from racing laps "
                "(excludes safety-car laps). Null when data_sufficient is false."
            ),
        },

        # ---- targets ----
        "target_burn_rate_kg_per_lap": {
            "type": ["number", "null"],
            "description": (
                "Burn rate required to reach the end of the race on exactly the minimum "
                "reserve fuel. Null when data_sufficient is false or in non-race sessions."
            ),
        },
        "target_next_lap_fuel_kg": {
            "type": ["number", "null"],
            "description": (
                "Smoothed target fuel consumption for the next lap, "
                "blending the required average rate with the current trend. "
                "Null when data_sufficient is false or in non-race sessions."
            ),
        },

        # ---- surplus estimates ----
        "surplus_laps_live": {
            "type": ["number", "null"],
            "description": (
                "Fuel surplus expressed as laps, computed from the rolling burn average. "
                "Positive = fuel to spare; negative = deficit. "
                "Available in race sessions only when data_sufficient is true."
            ),
        },
        "surplus_laps_builtin": {
            "type": ["number", "null"],
            "description": (
                "Fuel remaining expressed as laps, as estimated by the game's own fuel model. "
                "Available in all session types."
            ),
        },

        # ---- data quality ----
        "data_sufficient": {
            "type": ["boolean", "null"],
            "description": (
                "True when at least 2 racing laps have been completed and the rolling "
                "burn average is reliable. False means live estimates and targets are unavailable."
            ),
        },
    },

    "required": ["available", "connected", "ok"],
    "additionalProperties": True,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_fuel_info(
    logger: logging.Logger,
    driver_index: int,
) -> Dict[str, Any]:
    """Get fuel information for a specific driver by index.

    Args:
        logger: Logger instance.
        driver_index: Driver index (typically 0-21, depends on grid size).

    Returns:
        Dict[str, Any]: Fuel info response dict.
    """
    telemetry_update, base_rsp = _get_race_table_context(logger)

    if telemetry_update is None:
        return base_rsp

    row = _find_row_by_index(telemetry_update, driver_index)
    if row is None:
        return {
            **base_rsp,
            "ok": False,
            "error": f"No driver found with index {driver_index}.",
        }

    return _build_fuel_payload(base_rsp, row)


def _find_row_by_index(
    telemetry_update: Dict[str, Any],
    driver_index: int,
) -> Optional[Dict[str, Any]]:
    """Return the table-entry row whose driver-info.index matches driver_index."""
    for row in telemetry_update.get("table-entries", []):
        if row.get("driver-info", {}).get("index") == driver_index:
            return row
    return None


def _build_fuel_payload(
    base_rsp: Dict[str, Any],
    row: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the fuel info response from a resolved table-entry row."""
    driver_info: Dict[str, Any] = row.get("driver-info", {})
    fuel: Dict[str, Any] = row.get("fuel-info", {})

    # Live fields are non-zero only when FuelRateRecommender has enough racing laps.
    avg_rate = fuel.get("curr-fuel-rate")
    data_sufficient = avg_rate is not None and avg_rate != 0.0

    return {
        **base_rsp,
        "ok": True,

        "driver_index": driver_info.get("index"),
        "driver_name": driver_info.get("name"),

        "fuel_in_tank_kg": fuel.get("fuel-in-tank"),
        "fuel_capacity_kg": fuel.get("fuel-capacity"),
        "fuel_mix": fuel.get("fuel-mix"),

        "last_lap_fuel_used_kg": _none_if_zero(fuel.get("last-lap-fuel-used")),

        "avg_burn_rate_kg_per_lap": avg_rate if data_sufficient else None,
        "target_burn_rate_kg_per_lap": (
            fuel.get("target-fuel-rate-average") if data_sufficient else None
        ),
        "target_next_lap_fuel_kg": (
            fuel.get("target-fuel-rate-next-lap") if data_sufficient else None
        ),

        "surplus_laps_live": (
            fuel.get("surplus-laps-png") if data_sufficient else None
        ),
        "surplus_laps_builtin": fuel.get("surplus-laps-game"),

        "data_sufficient": data_sufficient,
    }


def _none_if_zero(value: Optional[float]) -> Optional[float]:
    """Return None for a 0.0 sentinel (indicates no data yet from backend)."""
    if value is None or value == 0.0:
        return None
    return value
