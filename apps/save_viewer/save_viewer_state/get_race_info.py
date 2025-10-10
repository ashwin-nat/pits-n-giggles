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

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _getRaceInfo(json_data: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """Get the race info.

    Args:
        json_data (Dict[str, Any]): JSON data
        logger (logging.Logger): Logger

    Returns:
        Dict[str, Any]: Race info
    """

    if not json_data:
        return {}

    ret = {
        "session-info" : json_data["session-info"],
        "records" : json_data.get("records"),
        "overtakes" : json_data.get("overtakes"),
        "custom-markers" : json_data.get("custom-markers", []),
        "position-history" : json_data.get("position-history", []),
        "speed-trap-records" : json_data.get("speed-trap-records", []),
    }

    if new_style := json_data.get("tyre-stint-history-v2"):
        _fill_missing_tyre_set_data(new_style, json_data)
        ret["tyre-stint-history-v2"] = new_style
    else:
        old_style = _getTyreStintHistoryJSON(json_data, logger)
        _fill_missing_tyre_set_data(old_style, json_data)
        ret["tyre-stint-history"] = old_style

    if race_ctrl := json_data.get("race-control"):
        ret["race-control"] = race_ctrl

    return ret

def _getTyreStintHistoryJSON(json_data: Dict[str, Any], logger: logging.Logger) -> List[Dict[str, Any]]:
    """Get tyre stint history.

    Args:
        json_data (Dict[str, Any]): JSON data
        logger (logging.Logger): Logger

    Returns:
        List[Dict[str, Any]]: The tyre stint history JSON
    """
    if not json_data:
        return []

    old_style = json_data.get("tyre-stint-history", [])
    classification_data = json_data.get("classification-data", [])
    for driver_entry in old_style:
        driver_data = _getDriverData(driver_entry, classification_data)
        if not driver_data:
            # if required data is not available for any of the drivers, return empty list
            logger.debug(f"Driver data not available for {driver_entry['name']}")
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

def _getDriverData(driver_entry: Dict[str, Any], classification_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get driver data. Search based on index if available, else name/team pair

    Args:
        driver_entry (Dict[str, Any]): Driver entry
        classification_data (List[Dict[str, Any]]): Classification data

    Returns:
        Dict[str, Any]: Driver data
    """
    # Index may not always be available, since it was added only from v2.13.1 onwards
    index = driver_entry.get("index")
    if index is not None and 0 <= index < len(classification_data):
        return classification_data[index]
    # Index not available/valid, search by name and team
    return _getDriverByNameTeam(driver_entry["name"], driver_entry["team"], classification_data)

def _getDriverByNameTeam(name: str, team: str, classification_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get driver by name.

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

def _fill_missing_tyre_set_data (tyre_set_history: List[Dict[str, Any]], full_json_data: Dict[str, Any]) -> None:
    """Ensure tyre set history exists for all stints. Fills into the given JSON"""

    # There is a bug in the backend where sometimes the tyre set data will be missing from this key
    # Insert it in such cases
    if not tyre_set_history:
        return

    classification_data = full_json_data.get("classification-data")
    if not classification_data:
        return

    for driver_entry in tyre_set_history:
        driver_data = _getDriverData(driver_entry, classification_data)
        if not driver_data:
            continue
        if driver_data["telemetry-settings"] == "Public":
            _fill_missing_tyre_set_data_driver(driver_entry, driver_data)

def _fill_missing_tyre_set_data_driver(driver_entry: Dict[str, Any], driver_data: Dict[str, Any]) -> None:
    """Ensure tyre set history exists for all stints for curr driver entry. Fills into the given JSON"""

    # There is a bug in the backend where sometimes the tyre set data will be missing from this key
    # Insert it in such cases
    tyre_stint_history = driver_entry.get("tyre-stint-history", [])
    if not tyre_stint_history:
        return

    tyre_set_data_ref = driver_data.get("tyre-sets", {}).get("tyre-set-data")

    for stint in tyre_stint_history:
        tyre_set_data = stint.get("tyre-set-data")
        if not tyre_set_data:
            fitted_index = stint.get("fitted-index")
            if (fitted_index is None) or not (0 <= fitted_index < len(tyre_set_data_ref)):
                # Fitted index must be valid
                continue
            stint["tyre-set-data"] = tyre_set_data_ref[fitted_index]

