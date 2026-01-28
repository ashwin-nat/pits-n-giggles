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
from typing import Any, Dict

from .common import _get_race_table_context

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

DRIVERS_LIST_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        # ---- base_rsp ----
        "available": {"type": "boolean"},
        "connected": {"type": "boolean"},
        "last-update-timestamp": {"type": ["number", "null"]},

        "ok": {"type": "boolean"},
        "error": {"type": ["string", "null"]},

        # ---- session identity ----
        "identity": {
            "type": "object",
            "properties": {
                "session_uid": {"type": ["integer", "null"]},
                "session_type": {"type": ["string", "null"]},
                "formula_type": {"type": ["string", "null"]},
                "circuit_name": {"type": ["string", "null"]},
                "session_ended": {"type": ["boolean", "null"]},
                "is_spectating": {"type": ["boolean", "null"]},
            },
            "additionalProperties": False,
        },

        # ---- drivers list----
        "drivers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {

                    # ---- driver info ----
                    "driver_name": {"type": ["string", "null"]},
                    "team_name": {"type": ["string", "null"]},
                    "index": {"type": ["integer", "null"]},
                    "is_player": {"type": ["boolean", "null"]},
                    "grid_position": {"type": ["integer", "null"]},
                    "telemetry_setting": {"type": ["string", "null"]},
                    "driver_number": {"type": ["integer", "null"]},

                },
                "additionalProperties": False,
            },
        },
    },

    # base fields always exist
    "required": ["available", "connected", "ok"],

    # allow future expansion (extra base_rsp fields, versioning, etc.)
    "additionalProperties": True,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_drivers_list(logger: logging.Logger) -> Dict[str, Any]:
    """Get race table from state data.

    Arguments:
        logger (logging.Logger): Logger instance.

    Returns:
        Dict[str, Any]: Session info dictionary.
    """
    telemetry_update, base_rsp = _get_race_table_context(logger)

    if telemetry_update is None:
        return base_rsp

    table_entries = telemetry_update.get("table-entries", [])
    if not table_entries:
        logger.debug("get_race_table: No table entries found in telemetry update")
        return base_rsp

    base_rsp["ok"] = True
    ret = {
        **base_rsp,

        "identity": {
            "session_uid": telemetry_update.get("session-uid"),
            "session_type": telemetry_update.get("event-type"),
            "formula_type": telemetry_update.get("formula"),
            "circuit_name": telemetry_update.get("circuit"),
            "session_ended": telemetry_update.get("race-ended"),
            "is_spectating": telemetry_update.get("is-spectating"),
        },

        "drivers": [
            _get_driver_info(entry)
            for entry in table_entries
        ],
    }
    return ret

def _get_driver_info(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Get race table info driver."""
    driver_info: Dict[str, Any] = entry.get("driver-info", {})

    return{
        "driver_name": driver_info.get("name"),
        "team_name": driver_info.get("team"),
        "index": driver_info.get("index"),
        "grid_position": driver_info.get("grid-position"),
        "is_player": driver_info.get("is-player"),
        "telemetry_setting": driver_info.get("telemetry-setting"),
        "driver_number": driver_info.get("driver-number"),
    }
