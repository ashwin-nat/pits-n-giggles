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
from typing import Any, Dict, List

from lib.child_proc_mgmt import report_ipc_port_from_child
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.ipc import IpcServerAsync

from apps.mcp.state import get_state_data

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_session_info(logger: logging.Logger) -> Dict[str, Any]:
    """Get session info from state data.

    Arguments:
        logger (logging.Logger): Logger instance.

    Returns:
        Dict[str, Any]: Session info dictionary.
    """
    telemetry_update_entry = get_state_data("race-table-update")
    connected_entry = get_state_data("connected", False)
    assert connected_entry is not None, "Connected state data missing"
    connected: bool = connected_entry.data
    logger.debug("get_session_info: connected=%s, telemetry_update_entry=%s",
                 connected, telemetry_update_entry)
    data_unavailable_rsp = {
        "available": False,
        "connected": connected,
    }
    if telemetry_update_entry is None:
        logger.debug("get_session_info: telemetry update entry is None")
        return data_unavailable_rsp

    telemetry_update: Dict[str, Any] = telemetry_update_entry.data
    session_uid = telemetry_update.get("session-uid")
    if not session_uid:
        logger.debug("get_session_info: session UID is missing or empty")
        return data_unavailable_rsp

    return {
        "available": True,
        "connected": connected,
        "last-update-timestamp": telemetry_update_entry.ts,

        "identity": {
            "session_uid": session_uid,
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
            # each forecast sample contains:
            #   session_type
            #   time_offset
            #   weather
            #   track_temperature
            #   track_temperature_change
            #   air_temperature
            #   air_temperature_change
            #   rain_percentage
        },

        "race_control": {
            "is_spectating": telemetry_update.get("is-spectating"),
            "safety_car_status": telemetry_update.get("safety-car-status"),
            "safety_car_deployments": telemetry_update.get("num-sc"),
            "virtual_safety_car_deployments": telemetry_update.get("num-vsc"),
            "red_flag_count": telemetry_update.get("num-red-flags"),
        },
    }
