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

from typing import Any, Dict, List

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _getRaceInfo(json_data: Dict[str, Any]) -> Dict[str, Any]:

    if not json_data:
        return {}

    ret = {
        "session-info" : json_data["session-info"],
        "records" : json_data.get("records", None),
        "overtakes" : json_data.get("overtakes", None),
        "custom-markers" : json_data.get("custom-markers", []),
        "position-history" : json_data.get("position-history", []),
        "speed-trap-records" : json_data.get("speed-trap-records", []),
    }

    if new_style := json_data.get("tyre-stint-history-v2"):
        ret["tyre-stint-history-v2"] = new_style
    else:
        ret["tyre-stint-history"] = _getTyreStintHistoryJSON(json_data)

    return ret

def _getTyreStintHistoryJSON(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get tyre stint history. (Assumes lock is already acquired)"""
    if not json_data:
        return []

    old_style = json_data.get("tyre-stint-history", [])
    for driver_entry in old_style:
        if not (driver_data := _getDriverByNameTeam(
            driver_entry["name"], driver_entry["team"], json_data["classification-data"])):
            # if required data is not available for any of the drivers, return empty list
            # TODO: bring logging
            # png_logger.debug(f"Driver data not available for {driver_entry['name']}")
            return []
        # Insert position, grid position, proper delta, result status
        if "position" not in driver_entry:
            driver_entry["position"] = driver_data["final-classification"]["position"]
        if "grid-position" not in driver_entry:
            driver_entry["grid-position"] = driver_data["final-classification"]["grid-position"]
        if "result-status" not in driver_entry:
            driver_entry["result-status"] = driver_data["final-classification"]["result-status"]
        if "telemetry-settings" not in driver_entry:
            driver_entry["telemetry-settings"] = driver_data["telemetry-settings"]

    return sorted(old_style, key=lambda x: x["position"])

def _getDriverByNameTeam(name: str, team: str, classification_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get driver by name. (assumes lock is already acquired)

    Args:
        name (str): Name of the driver
        classification_data (List[Dict[str, Any]]): Classification data
        team (str): Team name

    Returns:
        Dict[str, Any]: Driver data
    """
    return next(
        (
            driver
            for driver in classification_data
            if (driver["driver-name"] == name) and (driver["team"] == team)
        ),
        None,
    )
