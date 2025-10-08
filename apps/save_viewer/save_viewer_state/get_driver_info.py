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

from typing import Dict, Any

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _getDriverInfo(json_data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Get the driver info for the given index

    Args:
        json_data (Dict[str, Any]): JSON data from save file
        index (int): Index of the driver.

    Returns:
        Dict[str, Any]: Driver info.
    """
    final_json = {}
    if not json_data:
        return final_json

    driver_data = next(
        (
            driver
            for driver in json_data["classification-data"]
            if driver["index"] == index
        ),
        None,
    )
    if not driver_data:
        return final_json

    final_json["index"] = index
    final_json["is-player"] = driver_data["is-player"]
    final_json["driver-name"] = driver_data["driver-name"]
    final_json["team"] = driver_data["team"]
    final_json["track-position"] = driver_data["track-position"]
    final_json["telemetry-settings"] = driver_data["participant-data"]["telemetry-setting"]
    final_json["car-damage"] = driver_data["car-damage"]
    final_json["car-status"] = driver_data["car-status"]
    final_json["session-history"] = driver_data["session-history"]
    if "lap-time-history" in driver_data:
        final_json["lap-time-history"] = driver_data["lap-time-history"]
    final_json["final-classification"] = driver_data["final-classification"]
    final_json["lap-data"] = driver_data["lap-data"]

    final_json["participant-data"] = driver_data["participant-data"]
    final_json["tyre-sets"] = driver_data["tyre-sets"]

    # Insert the tyre set history
    final_json["tyre-set-history"]= driver_data["tyre-set-history"]
    _fill_missing_tyre_set(final_json["tyre-set-history"], driver_data)

    # Insert the per lap backup
    final_json["per-lap-info"] = driver_data["per-lap-info"]

    # Insert the warnings and penalties
    if "warning-penalty-history" in driver_data:
        final_json["warning-penalty-history"] = driver_data["warning-penalty-history"]
    else:
        final_json["warning-penalty-history"] = []

    # collisions
    final_json["collisions"] = driver_data["collisions"] if "collisions" in driver_data else {}

    # Race control
    if race_ctrl := driver_data.get("race-control"):
        final_json["race-control"] = race_ctrl

    # Return this fully prepped JSON
    return final_json

def _fill_missing_tyre_set(tyre_set_history: Dict[str, Any], driver_data: Dict[str, Any]) -> None:
    """Ensure tyre set history exists for all stints. Fills into the given JSON"""

    # There is a bug in the backend where sometimes the tyre set data will be missing from this key
    # Insert it in such cases
    if not tyre_set_history:
        return

    for stint in tyre_set_history:
        if not stint.get("tyre-set-data"):
            fitted_index = stint.get("fitted-index")
            tyre_sets = driver_data.get("tyre-sets", {}).get("tyre-set-data")
            if fitted_index is not None:
                # Check if fitted index is valid
                if 0 <= fitted_index < len(tyre_sets):
                    stint["tyre-set-data"] = tyre_sets[fitted_index]
                else:
                    stint["tyre-set-data"] = None
