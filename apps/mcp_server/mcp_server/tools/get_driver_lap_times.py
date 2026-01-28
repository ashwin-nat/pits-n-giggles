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
from typing import Any, Dict, List

from lib.f1_types import LapHistoryData

from .common import _DRIVER_INFO_REQ_STATUS_SCHEMA, fetch_driver_info

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

DRIVER_LAP_TIMES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {

        # ---- status (always present) ----
        **_DRIVER_INFO_REQ_STATUS_SCHEMA,

        # ---- lap time history ----
        "lap_time_history": {
            "type": "object",
            "properties": {
                "best_lap_time_lap_num": {"type": ["integer", "null"]},
                "best_sector_1_lap_num": {"type": ["integer", "null"]},
                "best_sector_2_lap_num": {"type": ["integer", "null"]},
                "best_sector_3_lap_num": {"type": ["integer", "null"]},
                "curr_lap_num": {"type": ["integer", "null"]},

                "lap_history_data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "lap_num": {"type": "integer"},

                            "lap_time_str": {"type": ["string", "null"]},
                            "s1_time_str": {"type": ["string", "null"]},
                            "s2_time_str": {"type": ["string", "null"]},
                            "s3_time_str": {"type": ["string", "null"]},
                            "top_speed_kmph": {"type": ["number", "null"]},

                            # validity flags (bitmask results)
                            "lap_valid": {"type": "integer"},
                            "s1_valid": {"type": "integer"},
                            "s2_valid": {"type": "integer"},
                            "s3_valid": {"type": "integer"},
                        },
                        "required": ["lap_num"],
                        "additionalProperties": False,
                    },
                },
            },
            "additionalProperties": False,
        },
    },

    # status must always exist
    "required": ["status"],

    # allow future additions (eg. summary fields)
    "additionalProperties": True,
}



# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def get_driver_lap_times(
        core_server_port: int,
        logger: logging.Logger,
        driver_index: int) -> Dict[str, Any]:
    """Get race table from state data.

    Arguments:
        core_server_port (int): Telemetry Core HTTP server port.
        logger (logging.Logger): Logger instance.
        driver_index (int): Driver index.

    Returns:
        Dict[str, Any]: Session info dictionary.
    """

    rsp = await fetch_driver_info(
        core_server_port=core_server_port,
        logger=logger,
        driver_index=driver_index,
    )

    status = rsp["status"]
    if not status["ok"]:
        return rsp  # pass-through error



    return {
        "lap_time_history" : _get_lap_time_history_rsp(rsp.get("data", {})),
        "status": status,
    }

def _get_lap_time_history_rsp(data: Dict[str, Any]) -> Dict[str, Any]:

    lap_time_history_dict: Dict[str, Any] = data.get("lap-time-history", {})
    lap_history_data_list: List[Dict[str, Any]] = lap_time_history_dict.get("lap-history-data", [])
    if not lap_time_history_dict:
        return {}

    ret = {
        "best_lap_time_lap_num" : lap_time_history_dict.get("best-lap-time-lap-num"),
        "best_sector_1_lap_num" : lap_time_history_dict.get("best-sector-1-lap-num"),
        "best_sector_2_lap_num" : lap_time_history_dict.get("best-sector-2-lap-num"),
        "best_sector_3_lap_num" : lap_time_history_dict.get("best-sector-3-lap-num"),
        "curr_lap_num": data.get("curr-lap-num"),
        "lap_history_data": [
            {
                "lap_num": (index + 1),
                **_lap_history_data_entry(entry)
            }
            for index, entry in enumerate(lap_history_data_list)
        ]
    }

    return ret

def _lap_history_data_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    valid_flags = entry.get("lap-valid-bit-flags", 0xFFFF)
    return {
        "lap_time_str": entry.get("lap-time-str"),
        "s1_time_str": entry.get("sector-1-time-str"),
        "s2_time_str": entry.get("sector-2-time-str"),
        "s3_time_str": entry.get("sector-3-time-str"),
        "top_speed_kmph": entry.get("top-speed-kmph"),

        "lap_valid": valid_flags & LapHistoryData.FULL_LAP_VALID_BIT_MASK,
        "s1_valid": valid_flags & LapHistoryData.SECTOR_1_VALID_BIT_MASK,
        "s2_valid": valid_flags & LapHistoryData.SECTOR_2_VALID_BIT_MASK,
        "s3_valid": valid_flags & LapHistoryData.SECTOR_3_VALID_BIT_MASK,
    }
