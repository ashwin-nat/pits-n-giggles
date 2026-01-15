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
from .common import _get_race_table_context

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
