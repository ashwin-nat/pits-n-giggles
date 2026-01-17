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
from typing import Any, Dict, Optional, Tuple

from lib.child_proc_mgmt import report_ipc_port_from_child
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.ipc import IpcServerAsync

from apps.mcp.state import get_state_data

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

    logger.debug(
        "_get_race_table_context: connected=%s, telemetry_update_entry=%s",
        connected, telemetry_update_entry,
    )

    base_rsp: Dict[str, Any] = {
        "available": False,
        "connected": connected,
        "last-update-timestamp": None,
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
