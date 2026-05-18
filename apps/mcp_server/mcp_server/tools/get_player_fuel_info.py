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
from typing import Any, Dict

from apps.hud.common import get_ref_row

from .common import _get_race_table_context
from .get_fuel_info import FUEL_INFO_OUTPUT_SCHEMA, _build_fuel_payload

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

PLAYER_FUEL_INFO_OUTPUT_SCHEMA = FUEL_INFO_OUTPUT_SCHEMA

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def get_player_fuel_info(logger: logging.Logger) -> Dict[str, Any]:
    """Get fuel information for the player/reference driver.

    In player/driver mode the player's own data is returned.
    In spectator mode the currently spectated driver's data is returned.

    Args:
        logger: Logger instance.

    Returns:
        Dict[str, Any]: Fuel info response dict.
    """
    telemetry_update, base_rsp = _get_race_table_context(logger)

    if telemetry_update is None:
        return base_rsp

    row = get_ref_row(telemetry_update)
    if row is None:
        return {
            **base_rsp,
            "ok": False,
            "error": "No reference/player row found in telemetry update.",
        }

    return _build_fuel_payload(base_rsp, row)
