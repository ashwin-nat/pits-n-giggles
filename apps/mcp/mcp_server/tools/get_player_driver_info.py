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

from apps.hud.common import get_ref_row, is_race_type_session

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

PLAYER_DRIVER_INFO_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        # ---- base_rsp (top-level) ----
        "available": {"type": "boolean"},
        "connected": {"type": "boolean"},
        "last-update-timestamp": {"type": ["number", "null"]},

        "ok": {"type": "boolean"},
        "error": {"type": ["string", "null"]},

        # ---- operation status ----
        "status": {
            "type": "string",
            "enum": ["ok", "error"],
        },

        # ---- session info ----
        "session_info": {
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

        # ---- player driver info ----
        "driver_info": {
            "type": "object",
            "properties": {
                "driver_index": {"type": ["integer", "null"]},
                "name": {"type": ["string", "null"]},
                "team": {"type": ["string", "null"]},
                "is_player": {"type": "boolean"},
                "is_spectating": {"type": "boolean"},
                "telemetry_setting": {"type": ["string", "null"]},
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

    # allow partial payloads on early returns
    "additionalProperties": True,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_player_driver_info(logger: logging.Logger) -> Dict[str, Any]:
    """Get session info from state data.

    Arguments:
        logger (logging.Logger): Logger instance.

    Returns:
        Dict[str, Any]: Session info dictionary.
    """
    telemetry_update, base_rsp = _get_race_table_context(logger)

    if telemetry_update is None:
        return base_rsp

    session_info = {
        "session_uid": telemetry_update.get("session-uid"),
        "session_type": telemetry_update.get("event-type"),
        "formula_type": telemetry_update.get("formula"),
        "circuit_name": telemetry_update.get("circuit"),
        "session_ended": telemetry_update.get("race-ended"),
    }

    ret = {
        **base_rsp,
        "session_info": session_info,
    }

    ref_row = get_ref_row(telemetry_update)
    if not ref_row:
        ret["status"] = "error"
        ret["error"] = "No reference row found in telemetry update"
        return ret

    driver_info = ref_row.get("driver-info", {})

    ret["driver_info"] = {
        "driver_index": driver_info.get("index"),
        "name": driver_info.get("name"),
        "team": driver_info.get("team"),
        "is_player": driver_info.get("is-player", False),
        "is_spectating": not driver_info.get("is-player", False),
        "telemetry_setting": driver_info.get("telemetry-setting"),
    }
    ret["status"] = "ok"
    ret["error"] = None

    return ret
