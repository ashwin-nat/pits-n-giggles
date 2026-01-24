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

SESSION_INFO_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        # ---- base_rsp (top-level) ----
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
                "session-ended": {"type": ["boolean", "null"]},
            },
            "additionalProperties": False,
        },

        # ---- session progress ----
        "progress": {
            "type": "object",
            "properties": {
                "current_lap": {"type": ["integer", "null"]},
                "total_laps": {"type": ["integer", "null"]},
                "duration_elapsed_sec": {"type": ["number", "null"]},
                "time_remaining_sec": {"type": ["number", "null"]},
            },
            "additionalProperties": False,
        },

        # ---- environment ----
        "environment": {
            "type": "object",
            "properties": {
                "air_temperature_c": {"type": ["number", "null"]},
                "track_temperature_c": {"type": ["number", "null"]},
                "weather_forecast": {
                    "type": ["array", "null"],
                    "items": {"type": "object"},
                },
            },
            "additionalProperties": False,
        },

        # ---- race control ----
        "race_control": {
            "type": "object",
            "properties": {
                "is_spectating": {"type": ["boolean", "null"]},
                "safety_car_status": {"type": ["string", "null"]},
                "safety_car_deployments": {"type": ["integer", "null"]},
                "virtual_safety_car_deployments": {"type": ["integer", "null"]},
                "red_flag_count": {"type": ["integer", "null"]},
            },
            "additionalProperties": False,
        },
    },

    # base_rsp fields should *always* exist
    "required": [
        "available",
        "connected",
        "ok",
    ],

    # Allow future expansion / extra base_rsp fields
    "additionalProperties": True,
}


# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_session_info(logger: logging.Logger) -> Dict[str, Any]:
    """Get session info from state data.

    Arguments:
        logger (logging.Logger): Logger instance.

    Returns:
        Dict[str, Any]: Session info dictionary.
    """
    telemetry_update, base_rsp = _get_race_table_context(logger)

    if telemetry_update is None:
        return base_rsp

    return {
        **base_rsp,

        "identity": {
            "session_uid": telemetry_update.get("session-uid"),
            "session_type": telemetry_update.get("event-type"),
            "formula_type": telemetry_update.get("formula"),
            "circuit_name": telemetry_update.get("circuit"),
            "session-ended": telemetry_update.get("race-ended"),
        },

        "progress": {
            "current_lap": telemetry_update.get("current-lap"),
            "total_laps": telemetry_update.get("total-laps"),
            "duration_elapsed_sec": telemetry_update.get("session-duration-so-far"),
            "time_remaining_sec": telemetry_update.get("session-time-left"),
        },

        "environment": {
            "air_temperature_c": telemetry_update.get("air-temperature"),
            "track_temperature_c": telemetry_update.get("track-temperature"),
            "weather_forecast": telemetry_update.get("weather-forecast-samples"),
        },

        "race_control": {
            "is_spectating": telemetry_update.get("is-spectating"),
            "safety_car_status": telemetry_update.get("safety-car-status"),
            "safety_car_deployments": telemetry_update.get("num-sc"),
            "virtual_safety_car_deployments": telemetry_update.get("num-vsc"),
            "red_flag_count": telemetry_update.get("num-red-flags"),
        },
    }
