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

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from lib.child_proc_mgmt import report_ipc_port_from_child
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.ipc import IpcServerAsync

from .common import _get_race_table_context

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

    rsp_table_entries = []
    for entry in table_entries:
        driver_info: Dict[str, Any] = entry.get("driver-info", {})

        lap_info_dict: Dict[str, Any] = entry.get("lap-info", {})
        last_lap_dict = lap_info_dict.get("last-lap", {})
        best_lap_dict = lap_info_dict.get("best-lap", {})
        delta_info_dict = entry.get("delta-info", {})

        tyre_info_dict: Dict[str, Any] = entry.get("tyre-info", {})
        current_wear_info: Dict[str, Any] = tyre_info_dict.get("current-wear", {})
        wear_prediction_dict: Dict[str, Any] = tyre_info_dict.get("wear-prediction", {})
        wear_rate_dict: Dict[str, Any] = wear_prediction_dict.get("rate", {})


        rsp_table_entries.append({
            "driver-info" : {
                "driver_name": driver_info.get("name"),
                "team_name": driver_info.get("team"),
                "dnf_status": driver_info.get("dnf-status"),
                "position": driver_info.get("position"),
                "index": driver_info.get("index"),
                "is_player": driver_info.get("is-player"),
                "delta-to-leader-ms": delta_info_dict.get("delta-to-leader-ms"),
            },
            "lap-info": {
                "last_lap_time_ms": last_lap_dict.get("lap-time-ms"),
                "best_lap_time_ms": best_lap_dict.get("best-lap-ms"),
                "speed_trap_record_kmph": lap_info_dict.get("speed-trap-record-kmph"),
                "top_speed_kmph": lap_info_dict.get("top-speed-kmph"),
            },
            "tyre-info": {
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
        })

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

        "standings": rsp_table_entries,
    }
