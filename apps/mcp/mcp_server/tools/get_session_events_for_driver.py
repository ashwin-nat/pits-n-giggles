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

from pydantic import BaseModel, Field

from lib.child_proc_mgmt import report_ipc_port_from_child
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.f1_types import F1Utils

from .common import fetch_driver_info, _DRIVER_INFO_REQ_STATUS_SCHEMA
import aiohttp

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_RACE_CONTROL_MESSAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": ["integer", "string", "null"],
            "description": "Unique race control message identifier",
        },
        "lap_num": {
            "type": ["integer", "null"],
            "description": "Lap number associated with this message",
        },
        "timestamp": {
            "type": ["number", "null"],
            "description": "Timestamp when the message was issued (as provided by telemetry)",
        },
        "message": {
            "type": "string",
            "description": "Race control message rendered in plain English",
        },
    },
    "required": ["message"],
    "additionalProperties": False,
}


DRIVER_SESSION_EVENTS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {

        # ---- status (always present) ----
        **_DRIVER_INFO_REQ_STATUS_SCHEMA,

        # ---- race control messages ----
        "race_ctrl_msgs": {
            "type": "array",
            "description": "List of race control messages relevant to the driver",
            "items": _RACE_CONTROL_MESSAGE_SCHEMA,
        },
    },

    # status must always exist (even on error)
    "required": ["status"],

    # allow future additions (summaries, counts, filters, etc.)
    "additionalProperties": True,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def get_session_events_for_driver(
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
        "race_ctrl_msgs" : [
            _get_race_ctrl_msg(msg)
            for msg in rsp.get("data", {}).get("race-control", [])
        ],
        "status": status,
    }

def _get_race_ctrl_msg(msg: Dict[str, Any]) -> Dict[str, Any]:

    return {
        "id": msg.get("id"),
        "lap_num": msg.get("lap-number"),
        "timestamp": msg.get("timestamp"),
        "message": render_details_cell(msg), # This is a string containing the message details in simple english
    }

def render_details_cell(msg):
    """Render event details based on message type."""

    message_type = msg.get('message-type')

    if message_type == 'SESSION_START':
        return '---'

    elif message_type == 'SESSION_END':
        return '---'

    elif message_type == 'FASTEST_LAP':
        d = msg.get('driver-info')
        ms = msg.get('lap-time-ms')
        return f"Driver: {get_driver_details_str(d)}, Lap Time: {F1Utils.millisecondsToMinutesSecondsMilliseconds(ms)}"

    elif message_type == 'RETIREMENT':
        d = msg.get('driver-info')
        return f"Driver: {get_driver_details_str(d)}"

    elif message_type == 'DRS_ENABLED':
        return '---'

    elif message_type == 'DRS_DISABLED':
        reason = msg.get('reason')
        return f"Reason: {reason}"

    elif message_type == 'CHEQUERED_FLAG':
        return '---'

    elif message_type == 'RACE_WINNER':
        d = msg.get('driver-info')
        return get_driver_details_str(d)

    elif message_type == 'PENALTY':
        d = msg.get('driver-info')
        pt = msg.get('penalty-type')
        it = msg.get('infringement-type')
        od = msg.get('other-driver-info')
        base = f"{get_driver_details_str(d, short=True)}, {pt} - {it}"
        return f"{base}, other driver: {get_driver_details_str(od, short=True)}" if od else base

    elif message_type == 'SPEED_TRAP_RECORD':
        d = msg.get('driver-info')
        speed = msg.get('speed')
        return f"Driver: {get_driver_details_str(d)}, Speed: {F1Utils.formatFloat(speed)} km/h"

    elif message_type == 'START_LIGHTS':
        num_lights = msg.get('num-lights')
        return f"Number of lights: {num_lights}"

    elif message_type == 'LIGHTS_OUT':
        return '---'

    elif message_type == 'DRIVE_THROUGH_SERVED':
        d = msg.get('driver-info')
        return f"Driver: {get_driver_details_str(d)}"

    elif message_type == 'STOP_GO_SERVED':
        d = msg.get('driver-info')
        stop_time = msg.get('stop-time')
        return f"Driver: {get_driver_details_str(d)} - Stop Time: {F1Utils.formatFloat(stop_time)} s"

    elif message_type == 'RED_FLAG':
        return '---'

    elif message_type == 'OVERTAKE':
        overtaker = msg.get('overtaker-info')
        overtaken = msg.get('overtaken-info')
        return f"{get_driver_details_str(overtaker)} overtook {get_driver_details_str(overtaken)}"

    elif message_type == 'SAFETY_CAR':
        sc_type = msg.get('sc-type')
        event_type = msg.get('event-type')
        return f"{sc_type} - {event_type}"

    elif message_type == 'COLLISION':
        d1 = msg.get('driver-1-info')
        d2 = msg.get('driver-2-info')
        return f"{get_driver_details_str(d1)} and {get_driver_details_str(d2)}"

    elif message_type == 'PITTING':
        d = msg.get('driver-info')
        lap = msg.get('lap-number')
        return f"Driver: {get_driver_details_str(d)}, Lap: {lap}"

    elif message_type == 'CAR_DAMAGE':
        part = msg.get('damaged-part')
        old_value = msg.get('old-value')
        new_value = msg.get('new-value')
        d = msg.get('driver-info')

        part_map = {
            'm_frontLeftWingDamage': 'Front Wing (Left)',
            'm_frontRightWingDamage': 'Front Wing (Right)',
            'm_rearWingDamage': 'Rear Wing',
        }
        part_str = part_map.get(part, 'Unknown')
        base = f"Part: {part_str}, Old Value: {old_value}, New Value: {new_value}"
        return f"Driver: {get_driver_details_str(d)} - {base}" if d else base

    elif message_type == 'WING_CHANGE':
        d = msg.get('driver-info')
        lap = msg.get('lap-number')
        return f"Driver: {get_driver_details_str(d)}, Lap: {lap}"

    elif message_type == 'TYRE_CHANGE':
        d = msg.get('driver-info')
        lap = msg.get('lap-number')
        old_compound = msg.get('old-tyre-compound')
        old_index = msg.get('old-tyre-index')
        new_compound = msg.get('new-tyre-compound')
        new_index = msg.get('new-tyre-index')
        return f"Driver: {get_driver_details_str(d)}, Lap: {lap} - {old_compound}({old_index}) → {new_compound}({new_index})"

    elif message_type == 'DRIVER_AI_STATUS_CHANGE':
        d = msg.get('driver-info')
        lap = msg.get('lap-number')
        old_state = msg.get('old-state')
        new_state = msg.get('new-state')

        state_label = lambda s: "AI" if s else "Player"
        return f"Driver: {get_driver_details_str(d)}, Lap: {lap} - State changed from {state_label(old_state)} to {state_label(new_state)}"

    elif message_type == 'FLASHBACK':
        return '---'

    else:
        # DEFAULT case
        return f"Type: {message_type} - Placeholder details."

def get_driver_details_str(driver_info, short=False):
    """Format driver information as a string."""
    if driver_info:
        name = driver_info.get("name")
        team = driver_info.get("team")
        driver_number = driver_info.get("driver-number")

        if short:
            return f"{name} ({team} {driver_number})"
        return f"{name} - {team} #{driver_number}"
    else:
        return "Unknown Driver"
