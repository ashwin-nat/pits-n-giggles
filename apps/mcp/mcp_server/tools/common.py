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
import aiohttp

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

async def fetch_driver_info(
        core_server_port: int,
        logger: logging.Logger,
        driver_index: int,
) -> Dict[str, Any]:
    """
    Fetch /driver-info from telemetry core.

    One connection per call.
    Never raises.
    Centralizes all HTTP / network / decoding errors.
    """

    url = f"http://localhost:{core_server_port}/driver-info"

    params = {"index": driver_index}

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=3)
        ) as session:
            async with session.get(url, params=params) as resp:

                if resp.status != 200:
                    body = await resp.text()
                    logger.error(
                        f"[fetch_driver_info] HTTP {resp.status} | "
                        f"driver_index={driver_index} | body={body}"
                    )
                    return {
                        "status": {
                            "ok": False,
                            "error": "core_server_http_error",
                            "status": resp.status,
                            "details": body,
                        },
                        "data": None,
                    }

                try:
                    data = await resp.json()
                except Exception as e:
                    logger.error(
                        f"[fetch_driver_info] Invalid JSON response: {e}"
                    )
                    return {
                        "status": {
                            "ok": False,
                            "error": "invalid_json",
                            "status": resp.status,
                            "details": str(e),
                        },
                        "data": None,
                    }

                return {
                    "status": {
                        "ok": True,
                        "error": None,
                        "status": resp.status,
                        "details": None,
                    },
                    "data": data,
                }

    except asyncio.TimeoutError:
        logger.error(
            f"[fetch_driver_info] Timeout | driver_index={driver_index}"
        )
        return {
            "status": {
                "ok": False,
                "error": "core_server_timeout",
                "status": None,
                "details": "Core server did not respond in time",
            },
            "data": None,
        }

    except aiohttp.ClientConnectionError as e:
        logger.error(
            f"[fetch_driver_info] Connection error: {e}"
        )
        return {
            "status": {
                "ok": False,
                "error": "core_server_unreachable",
                "status": None,
                "details": str(e),
            },
            "data": None,
        }

    except aiohttp.ClientError as e:
        logger.error(
            f"[fetch_driver_info] Client error: {e}"
        )
        return {
            "status": {
                "ok": False,
                "error": "client_error",
                "status": None,
                "details": str(e),
            },
            "data": None,
        }

    except Exception as e:
        logger.exception(
            "[fetch_driver_info] Unexpected error"
        )
        return {
            "status": {
                "ok": False,
                "error": "unknown_error",
                "status": None,
                "details": str(e),
            },
            "data": None,
        }
