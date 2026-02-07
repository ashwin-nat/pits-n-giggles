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

RACE_TABLE_OUTPUT_SCHEMA = {
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

        # ---- race standings ----
        "standings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {

                    # ---- driver info ----
                    "driver_info": {
                        "type": "object",
                        "properties": {
                            "driver_name": {"type": ["string", "null"]},
                            "team_name": {"type": ["string", "null"]},
                            "dnf_status": {"type": ["string", "null"]},
                            "position": {"type": ["integer", "null"]},
                            "index": {"type": ["integer", "null"]},
                            "is_player": {"type": ["boolean", "null"]},
                            "delta_to_leader_ms": {"type": ["number", "null"]},
                        },
                        "additionalProperties": False,
                    },

                    # ---- lap info ----
                    "lap_info": {
                        "type": "object",
                        "properties": {
                            "last_lap_time_ms": {"type": ["number", "null"]},
                            "best_lap_time_ms": {"type": ["number", "null"]},
                            "speed_trap_record_kmph": {"type": ["number", "null"]},
                            "top_speed_kmph": {"type": ["number", "null"]},
                        },
                        "additionalProperties": False,
                    },

                    # ---- tyre info ----
                    "tyre_info": {
                        "type": "object",
                        "properties": {
                            "current_wear_percent": {"type": ["number", "null"]},
                            "tyre_compound": {"type": ["string", "null"]},
                            "tyre_age": {"type": ["integer", "null"]},

                            "curr_tyre_wear": {
                                "type": "object",
                                "properties": {
                                    "fl_wear_pct": {"type": ["number", "null"]},
                                    "fr_wear_pct": {"type": ["number", "null"]},
                                    "rl_wear_pct": {"type": ["number", "null"]},
                                    "rr_wear_pct": {"type": ["number", "null"]},
                                },
                                "additionalProperties": False,
                            },

                            "tyre_wear_per_lap": {
                                "type": "object",
                                "properties": {
                                    "available": {"type": "boolean"},
                                    "fl_rate_pct_per_lap": {"type": ["number", "null"]},
                                    "fr_rate_pct_per_lap": {"type": ["number", "null"]},
                                    "rl_rate_pct_per_lap": {"type": ["number", "null"]},
                                    "rr_rate_pct_per_lap": {"type": ["number", "null"]},
                                },
                                "additionalProperties": False,
                            },
                        },
                        "additionalProperties": False,
                    },

                    # ---- car info ----
                    "car_info": {
                        "type": "object",
                        "properties": {
                            "curr_fuel_rate": {"type": ["number", "null"]},
                            "fuel_surplus_laps_builtin_est": {"type": ["number", "null"]},
                            "fuel_surplus_laps_live_est": {"type": ["number", "null"]},
                            "last_lap_fuel_consumption": {"type": ["number", "null"]},
                            "ers_percent": {"type": ["number", "null"]},
                            "ers_mode": {"type": ["string", "null"]},
                        },
                        "additionalProperties": False,
                    },

                    # ---- damage info ----
                    "damage_info": {
                        "type": "object",
                        "properties": {
                            "fl_wing_damage": {"type": ["number", "null"]},
                            "fr_wing_damage": {"type": ["number", "null"]},
                        },
                        "additionalProperties": False,
                    },
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

def get_race_table(logger: logging.Logger) -> Dict[str, Any]:
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
        },

        "progress": {
            "current_lap": telemetry_update.get("current-lap"),
            "total_laps": telemetry_update.get("total-laps"),
            "duration_elapsed_sec": telemetry_update.get("session-duration-so-far"),
            "time_remaining_sec": telemetry_update.get("session-time-left"),
        },

        "standings": [
            _get_race_table_info_driver(entry)
            for entry in table_entries
        ],
    }
    return ret

def _get_race_table_info_driver(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Get race table info driver."""
    driver_info: Dict[str, Any] = entry.get("driver-info", {})

    lap_info_dict: Dict[str, Any] = entry.get("lap-info", {})
    last_lap_dict: Dict[str, Any] = lap_info_dict.get("last-lap", {})
    best_lap_dict: Dict[str, Any] = lap_info_dict.get("best-lap", {})
    delta_info_dict: Dict[str, Any] = entry.get("delta-info", {})

    tyre_info_dict: Dict[str, Any] = entry.get("tyre-info", {})
    current_wear_info: Dict[str, Any] = tyre_info_dict.get("current-wear", {})
    wear_prediction_dict: Dict[str, Any] = tyre_info_dict.get("wear-prediction", {})
    wear_rate_dict: Dict[str, Any] = wear_prediction_dict.get("rate", {})
    fuel_info_dict: Dict[str, Any] = entry.get("fuel-info", {})
    ers_info_dict: Dict[str, Any] = entry.get("ers-info", {})
    damage_info_dict: Dict[str, Any] = entry.get("damage-info", {})

    return{
        "driver_info" : {
            "driver_name": driver_info.get("name"),
            "team_name": driver_info.get("team"),
            "dnf_status": driver_info.get("dnf-status"),
            "position": driver_info.get("position"),
            "index": driver_info.get("index"),
            "is_player": driver_info.get("is-player"),
            "delta_to_leader_ms": delta_info_dict.get("delta-to-leader-ms"),
        },
        "lap_info": {
            "last_lap_time_ms": last_lap_dict.get("lap-time-ms"),
            "best_lap_time_ms": best_lap_dict.get("lap-time-ms"),
            "speed_trap_record_kmph": lap_info_dict.get("speed-trap-record-kmph"),
            "top_speed_kmph": lap_info_dict.get("top-speed-kmph"),
        },
        "tyre_info": {
            "current_wear_percent": current_wear_info.get("wear-percent"),
            "tyre_compound": tyre_info_dict.get("visual-tyre-compound"),
            "tyre_age": tyre_info_dict.get("tyre-age"),
            "curr_tyre_wear" : {
                "fl_wear_pct": current_wear_info.get("front-left-wear"),
                "fr_wear_pct": current_wear_info.get("front-right-wear"),
                "rl_wear_pct": current_wear_info.get("rear-left-wear"),
                "rr_wear_pct": current_wear_info.get("rear-right-wear"),
            },
            "tyre_wear_per_lap" : {
                "available": wear_prediction_dict.get("status", False),
                "fl_rate_pct_per_lap": wear_rate_dict.get("front-left"),
                "fr_rate_pct_per_lap": wear_rate_dict.get("front-right"),
                "rl_rate_pct_per_lap": wear_rate_dict.get("rear-left"),
                "rr_rate_pct_per_lap": wear_rate_dict.get("rear-right"),
            },
        },
        "car_info": {
            "curr_fuel_rate": fuel_info_dict.get("current-fuel-rate"),
            "fuel_surplus_laps_builtin_est": fuel_info_dict.get("surplus-laps-game"),
            "fuel_surplus_laps_live_est": fuel_info_dict.get("surplus-laps-png"),
            "last_lap_fuel_consumption": fuel_info_dict.get("last-lap-fuel-used"),
            "ers_percent": ers_info_dict.get("ers-percent-float"),
            "ers_mode": ers_info_dict.get("ers-mode"),
        },
        "damage_info": {
            "fl_wing_damage": damage_info_dict.get("fl-wing-damage"),
            "fr_wing_damage": damage_info_dict.get("fr-wing-damage"),
        }
    }
