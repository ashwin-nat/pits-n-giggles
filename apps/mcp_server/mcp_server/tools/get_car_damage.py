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

from lib.f1_types import F1Utils

from .common import _DRIVER_INFO_REQ_STATUS_SCHEMA, fetch_driver_info

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

CAR_DAMAGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {

        # ---- status (always present) ----
        **_DRIVER_INFO_REQ_STATUS_SCHEMA,

        # ---- car damage ----
        "car_damage": {
            "type": "object",
            "properties": {

                # per-tyre float (0–100 typically)
                "tyre_wear": {
                    "type": "object",
                    "properties": {
                        "fl": {"type": ["number", "null"]},
                        "fr": {"type": ["number", "null"]},
                        "rl": {"type": ["number", "null"]},
                        "rr": {"type": ["number", "null"]},
                    },
                    "additionalProperties": False,
                },

                # per-tyre int (0–100)
                "tyre_damage": {
                    "type": "object",
                    "properties": {
                        "fl": {"type": ["integer", "null"]},
                        "fr": {"type": ["integer", "null"]},
                        "rl": {"type": ["integer", "null"]},
                        "rr": {"type": ["integer", "null"]},
                    },
                    "additionalProperties": False,
                },

                "brakes_damage": {
                    "type": "object",
                    "properties": {
                        "fl": {"type": ["integer", "null"]},
                        "fr": {"type": ["integer", "null"]},
                        "rl": {"type": ["integer", "null"]},
                        "rr": {"type": ["integer", "null"]},
                    },
                    "additionalProperties": False,
                },

                # aero / body
                "front_left_wing_damage": {"type": ["integer", "null"]},
                "front_right_wing_damage": {"type": ["integer", "null"]},
                "rear_wing_damage": {"type": ["integer", "null"]},
                "floor_damage": {"type": ["integer", "null"]},
                "diffuser_damage": {"type": ["integer", "null"]},
                "sidepod_damage": {"type": ["integer", "null"]},

                # systems
                "drs_fault": {"type": ["boolean", "null"]},
                "ers_fault": {"type": ["boolean", "null"]},
                "gear_box_damage": {"type": ["integer", "null"]},

                # engine
                "engine_damage": {"type": ["integer", "null"]},
                "engine_mguh_wear": {"type": ["integer", "null"]},
                "engine_es_wear": {"type": ["integer", "null"]},
                "engine_ce_wear": {"type": ["integer", "null"]},
                "engine_ice_wear": {"type": ["integer", "null"]},
                "engine_mguk_wear": {"type": ["integer", "null"]},
                "engine_tc_wear": {"type": ["integer", "null"]},

                "engine_blown": {"type": ["boolean", "null"]},
                "engine_seized": {"type": ["boolean", "null"]},
            },

            # car_damage itself may be empty if no data
            "additionalProperties": False,
        },
    },

    # status must always exist
    "required": ["status"],

    # allow future additions (eg. summary fields)
    "additionalProperties": True,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def get_car_damage(
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
        "car_damage" : _get_car_damage_rsp(rsp.get("data", {})),
        "status": status,
    }

def _get_car_damage_rsp(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get car damage response."""
    car_dmg_dict: Dict[str, Any] = data.get("car-damage", {})
    if not car_dmg_dict:
        return {}

    return {
        "tyre_wear" : _list_to_per_tyre_dict(car_dmg_dict.get("tyres-wear")), # list[float]
        "tyre_damage" : _list_to_per_tyre_dict(car_dmg_dict.get("tyres-damage")), # list[int]
        "brakes_damage" : _list_to_per_tyre_dict(car_dmg_dict.get("brakes-damage")), # list[int]
        "front_left_wing_damage" : car_dmg_dict.get("front-left-wing-damage"), # int
        "front_right_wing_damage" : car_dmg_dict.get("front-right-wing-damage"), # int
        "rear_wing_damage" : car_dmg_dict.get("rear-wing-damage"), # int
        "floor_damage" : car_dmg_dict.get("floor-damage"), # int
        "diffuser_damage" : car_dmg_dict.get("diffuser-damage"), # int
        "sidepod_damage" : car_dmg_dict.get("sidepod-damage"), # int
        "drs_fault" : car_dmg_dict.get("drs-fault"), # int
        "ers_fault" : car_dmg_dict.get("ers-fault"), # int
        "gear_box_damage" : car_dmg_dict.get("gear-box-damage"), # int
        "engine_damage" : car_dmg_dict.get("engine-damage"), # int
        "engine_mguh_wear" : car_dmg_dict.get("engine-mguh-wear"), # int
        "engine_es_wear" : car_dmg_dict.get("engine-es-wear"), # int
        "engine_ce_wear" : car_dmg_dict.get("engine-ce-wear"), # int
        "engine_ice_wear" : car_dmg_dict.get("engine-ice-wear"), # int
        "engine_mguk_wear" : car_dmg_dict.get("engine-mguk-wear"), # int
        "engine_tc_wear" : car_dmg_dict.get("engine-tc-wear"), # int
        "engine_blown" : car_dmg_dict.get("engine-blown"), # bool
        "engine_seized" : car_dmg_dict.get("engine-seized"), # bool
    }

def _list_to_per_tyre_dict(data: List[Any]) -> Dict[str, Any]:
    """Convert list to per tyre dict."""
    if not data or len(data) != 4:
        return {
            "fl" : None,
            "fr" : None,
            "rl" : None,
            "rr" : None,
        }
    return {
        "fl" : data[F1Utils.INDEX_FRONT_LEFT],
        "fr" : data[F1Utils.INDEX_FRONT_RIGHT],
        "rl" : data[F1Utils.INDEX_REAR_LEFT],
        "rr" : data[F1Utils.INDEX_REAR_RIGHT],
    }
