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

from lib.ipc import IpcDealerAsync, PngAppId

from apps.mcp_server.state import get_state_data

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_DRIVER_INFO_REQ_STATUS_SCHEMA = {
    "status": {
        "type": "object",
        "properties": {
            "ok": {"type": "boolean"},
            "error": {"type": ["string", "null"]},
            "status": {"type": ["integer", "null"]},
            "details": {"type": ["string", "null"]},
        },
        "required": ["ok"],
        "additionalProperties": False,
    },
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------
def _get_race_table_context(
    logger: logging.Logger,
) -> tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Common preflight for race-table-derived tools.

    Returns:
        telemetry_update (Dict | None)
        base_response    (Dict)
    """
    telemetry_update_entry = get_state_data("race-table-update")
    connected_entry = get_state_data("connected", False)

    assert connected_entry is not None, "Connected state data missing"
    connected: bool = connected_entry.data

    base_rsp: Dict[str, Any] = {
        "available": False,
        "connected": connected,
        "last-update-timestamp": None,
        "ok": False,
    }

    if telemetry_update_entry is None:
        logger.debug("_get_race_table_context: telemetry update entry is None")
        return None, base_rsp

    telemetry_update: Dict[str, Any] = telemetry_update_entry.data

    session_uid = telemetry_update.get("session-uid")
    if not session_uid:
        logger.debug("_get_race_table_context: session UID missing")
        return None, base_rsp

    base_rsp["last-update-timestamp"] = telemetry_update_entry.ts
    base_rsp["available"] = True
    return telemetry_update, base_rsp

async def fetch_driver_info(
        dealer: IpcDealerAsync,
        logger: logging.Logger,
        driver_index: int,
) -> Dict[str, Any]:
    """
    Fetch driver info from the backend via ZMQ DEALER request-response.

    Never raises.
    Centralizes all transport and backend errors.
    """

    reply = await dealer.send(
        str(PngAppId.BACKEND),
        "driver-info-request",
        {"index": driver_index},
    )

    if reply.get("status") == "error":
        reason = reply.get("reason", "unknown")
        error_key = "core_server_timeout" if "timeout" in reason else "core_server_unreachable"
        logger.error("[fetch_driver_info] dealer error: %s", reason)
        return {
            "status": {"ok": False, "error": error_key, "status": None, "details": reason},
            "data": None,
        }

    if not reply.get("ok"):
        logger.error("[fetch_driver_info] backend returned not-ok: %s", reply)
        return {
            "status": {"ok": False, "error": "backend_error", "status": None, "details": str(reply)},
            "data": None,
        }

    return {
        "status": {"ok": True, "error": None, "status": 200, "details": None},
        "data": reply.get("data"),
    }
