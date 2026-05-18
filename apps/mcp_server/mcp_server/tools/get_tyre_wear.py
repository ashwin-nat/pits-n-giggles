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

TYRE_WEAR_OUTPUT_SCHEMA = {
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

        # ---- tyre identity ----
        "tyre_compound": {
            "type": ["string", "null"],
            "description": "Visual tyre compound (e.g. Soft, Medium, Hard, Inter, Wet)",
        },
        "tyre_age_laps": {
            "type": ["integer", "null"],
            "description": "Number of laps completed on the current set of tyres",
        },

        # ---- current wear ----
        "current_wear_avg_pct": {
            "type": ["number", "null"],
            "description": "Average wear across all four tyres (%)",
        },
        "fl_wear_pct": {
            "type": ["number", "null"],
            "description": "Front-left tyre wear (%)",
        },
        "fr_wear_pct": {
            "type": ["number", "null"],
            "description": "Front-right tyre wear (%)",
        },
        "rl_wear_pct": {
            "type": ["number", "null"],
            "description": "Rear-left tyre wear (%)",
        },
        "rr_wear_pct": {
            "type": ["number", "null"],
            "description": "Rear-right tyre wear (%)",
        },

        # ---- wear rate (per lap) ----
        "wear_rate_available": {
            "type": ["boolean", "null"],
            "description": "True when at least 2 laps of data are available for regression",
        },
        "fl_rate_pct_per_lap": {
            "type": ["number", "null"],
            "description": "Front-left tyre wear rate (% per lap). Null when wear_rate_available is false.",
        },
        "fr_rate_pct_per_lap": {
            "type": ["number", "null"],
            "description": "Front-right tyre wear rate (% per lap). Null when wear_rate_available is false.",
        },
        "rl_rate_pct_per_lap": {
            "type": ["number", "null"],
            "description": "Rear-left tyre wear rate (% per lap). Null when wear_rate_available is false.",
        },
        "rr_rate_pct_per_lap": {
            "type": ["number", "null"],
            "description": "Rear-right tyre wear rate (% per lap). Null when wear_rate_available is false.",
        },
    },

    "required": ["available", "connected", "ok"],
    "additionalProperties": True,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_tyre_wear(
    logger: logging.Logger,
    driver_index: int,
) -> Dict[str, Any]:
    """Get tyre wear information for a specific driver by index.

    Args:
        logger: Logger instance.
        driver_index: Driver index (typically 0-21, depends on grid size).

    Returns:
        Dict[str, Any]: Tyre wear response dict.
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

    return _build_tyre_wear_payload(base_rsp, row)


def _none_if_zero(value: Optional[float]) -> Optional[float]:
    """Return None for a 0.0 sentinel (indicates no data yet from backend)."""
    if value is None or value == 0.0:
        return None
    return value


def _find_row_by_index(
    telemetry_update: Dict[str, Any],
    driver_index: int,
) -> Optional[Dict[str, Any]]:
    """Return the table-entry row whose driver-info.index matches driver_index."""
    for row in telemetry_update.get("table-entries", []):
        if row.get("driver-info", {}).get("index") == driver_index:
            return row
    return None


def _build_tyre_wear_payload(
    base_rsp: Dict[str, Any],
    row: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the tyre wear response from a resolved table-entry row."""
    driver_info: Dict[str, Any] = row.get("driver-info", {})
    tyre: Dict[str, Any] = row.get("tyre-info", {})
    current_wear: Dict[str, Any] = tyre.get("current-wear", {})
    wear_prediction: Dict[str, Any] = tyre.get("wear-prediction", {})
    wear_rate: Dict[str, Any] = wear_prediction.get("rate", {})
    rate_available: bool = wear_prediction.get("status", False)

    return {
        **base_rsp,
        "ok": True,

        "driver_index": driver_info.get("index"),
        "driver_name": driver_info.get("name"),

        "tyre_compound": tyre.get("visual-tyre-compound"),
        "tyre_age_laps": tyre.get("tyre-age"),

        "current_wear_avg_pct": current_wear.get("average"),
        "fl_wear_pct": current_wear.get("front-left-wear"),
        "fr_wear_pct": current_wear.get("front-right-wear"),
        "rl_wear_pct": current_wear.get("rear-left-wear"),
        "rr_wear_pct": current_wear.get("rear-right-wear"),

        "wear_rate_available": rate_available,
        "fl_rate_pct_per_lap": _none_if_zero(wear_rate.get("front-left")) if rate_available else None,
        "fr_rate_pct_per_lap": _none_if_zero(wear_rate.get("front-right")) if rate_available else None,
        "rl_rate_pct_per_lap": _none_if_zero(wear_rate.get("rear-left")) if rate_available else None,
        "rr_rate_pct_per_lap": _none_if_zero(wear_rate.get("rear-right")) if rate_available else None,
    }
