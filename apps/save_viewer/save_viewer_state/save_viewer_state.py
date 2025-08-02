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

import json
import logging
from lib.ipc import IpcChildAsync
from typing import List
from functools import partial
import webbrowser
from typing import Dict, Any, Optional

from lib.f1_types import F1Utils, ResultStatus, LapHistoryData
from lib.tyre_wear_extrapolator import TyreWearPerLap
import lib.race_analyzer as RaceAnalyzer
import lib.overtake_analyzer as OvertakeAnalyzer

from .get_telemetry_info import _getTelemetryInfo
from .get_race_info import _getRaceInfo
from .get_driver_info import _getDriverInfo

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_json_data: Dict[str, Any] = {}
_logger: logging.Logger = None
_port_number: int = None
_should_open_ui: bool = True

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_state(logger: logging.Logger, port: int) -> None:
    global _logger
    global _port_number
    _logger = logger

def getTelemetryInfo() -> Dict[str, Any]:
    """
    Main function to retrieve and format complete telemetry information.

    Returns:
        Complete telemetry data structure with session info and driver entries
    """
    global _json_data
    return _getTelemetryInfo(_json_data)

def getRaceInfo() -> Dict[str, Any]:
    global _json_data
    return _getRaceInfo(_json_data)

def getDriverInfo(index: int) -> Dict[str, Any]:
    # TODO: validation in caller side
    global _json_data
    return _getDriverInfo(_json_data, index)

async def open_file_helper(file_path, open_webpage=True):
    try:
        with open(file_path, 'r+', encoding='utf-8') as f:
            global _json_data
            global _should_open_ui
            global _port_number
            _json_data = json.load(f)

            should_write = False
            should_write |= _check_recompute_json(_json_data)

            # await sendRaceTable() # TODO: move to IPC layer

            # TODO - move to IPC layer
            if _should_open_ui and open_webpage:
                _should_open_ui = False
                webbrowser.open(f'http://localhost:{_port_number}', new=2)

        _logger.info(f"Opened file: {file_path}")
        return {"status": "success"}

    except (FileNotFoundError, PermissionError) as e:
        _logger.error(f"Failed to open file: {file_path}. Error: {e}")
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}
    except json.JSONDecodeError as e:
        _logger.error(f"Invalid JSON in file: {file_path}. Error: {e}")
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}
    except UnicodeDecodeError as e:
        _logger.error(f"Invalid UTF-8 in file: {file_path}. Error: {e}")
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}
    except Exception as e:
        _logger.exception(f"Unexpected error opening file: {file_path}")
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}

# -------------------------------------- HELPER FUNCTIONS --------------------------------------------------------------

def _check_recompute_json(json_data: Dict[str, Any]) -> bool:
    """
    Checks and fills in missing derived fields in race JSON data.

    Args:
        json_data (Dict[str, Any]): Parsed race JSON data.

    Returns:
        bool: True if any part of the JSON was updated, else False.
    """
    updated = False

    updated |= _fill_missing_tyre_wear(json_data)
    updated |= _ensure_records_container(json_data)
    updated |= _ensure_fastest_records(json_data)
    updated |= _ensure_tyre_stats(json_data)
    updated |= _ensure_overtake_records(json_data)

    return updated

def _is_valid_json(data: Any) -> bool:
    """Check if the input is valid JSON."""
    if isinstance(data, dict):
        return True
    try:
        json.loads(data)
        return True
    except json.JSONDecodeError:
        return False

def _get_tyre_wear_history(driver_data: Dict[str, Any], start_lap: int, end_lap: int) -> List[Dict[str, Any]]:
    """Extract tyre wear data between specified laps from driver data."""
    tyre_wear_history = []
    if "per-lap-info" in driver_data:
        for lap_backup in driver_data["per-lap-info"]:
            lap_number = lap_backup['lap-number']
            if not (start_lap <= lap_number <= end_lap):
                continue
            if "car-damage-data" in lap_backup:
                wear = lap_backup["car-damage-data"]["tyres-wear"]
                tyre_wear_history.append({
                    'lap-number': lap_number,
                    'front-left-wear': wear[F1Utils.INDEX_FRONT_LEFT],
                    'front-right-wear': wear[F1Utils.INDEX_FRONT_RIGHT],
                    'rear-left-wear': wear[F1Utils.INDEX_REAR_LEFT],
                    'rear-right-wear': wear[F1Utils.INDEX_REAR_RIGHT],
                })
    return tyre_wear_history

def _fill_missing_tyre_wear(json_data: Dict[str, Any]) -> bool:
    """Ensure tyre wear history exists for all stints."""
    updated = False
    if "classification-data" in json_data:
        for driver_data in json_data["classification-data"]:
            if not (tyre_set_history := driver_data.get("tyre-set-history")):
                continue
            for stint in tyre_set_history:
                if "tyre-wear-history" not in stint:
                    stint["tyre-wear-history"] = _get_tyre_wear_history(
                        driver_data, stint["start-lap"], stint["end-lap"]
                    )
                    updated = True
    return updated


def _ensure_fastest_records(json_data: Dict[str, Any]) -> bool:
    """Ensure fastest lap records are complete and valid."""
    updated = False
    if "fastest" not in json_data["records"]:
        json_data["records"]["fastest"] = RaceAnalyzer.getFastestTimesJson(json_data)
        return True

    expected_keys = ['driver-index', 'driver-name', 'team-id', 'lap-number', 'time', 'time-str']
    for record in json_data["records"]["fastest"].values():
        if any(key not in record for key in expected_keys):
            json_data["records"]["fastest"] = RaceAnalyzer.getFastestTimesJson(json_data)
            return True
    return updated

def _ensure_tyre_stats(json_data: Dict[str, Any]) -> bool:
    """Ensure tyre stats exist and are complete."""
    updated = False
    if "tyre-stats" not in json_data["records"]:
        json_data["records"]["tyre-stats"] = RaceAnalyzer.getTyreStintRecordsDict(json_data)
        return True

    required_keys = ['longest-tyre-stint', 'lowest-tyre-wear-per-lap', 'highest-tyre-wear']
    for compound_stats in json_data["records"]["tyre-stats"].values():
        if any(key not in compound_stats for key in required_keys):
            json_data["records"]["tyre-stats"] = RaceAnalyzer.getTyreStintRecordsDict(json_data)
            return True
    return updated

def _ensure_overtake_records(json_data: Dict[str, Any]) -> bool:
    """Ensure overtake data is valid and enriched."""
    updated = False

    if "overtakes" not in json_data:
        json_data["overtakes"] = {"records": []}
        return True

    required_keys = ["number-of-overtakes", "most-heated-rivalries"]
    if any(key not in json_data["overtakes"] for key in required_keys):
        updated = True

    records = json_data["overtakes"].get("records", [])
    if updated and len(records) > 0:
        mode = (
            OvertakeAnalyzer.OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS_JSON
            if _is_valid_json(records[0])
            else OvertakeAnalyzer.OvertakeAnalyzerMode.INPUT_MODE_LIST_CSV
        )
        enriched = OvertakeAnalyzer.OvertakeAnalyzer(
            input_mode=mode,
            input_data=records
        ).toJSON()
        json_data["overtakes"] = json_data["overtakes"] | enriched
        return True

    return updated

def _ensure_records_container(json_data: Dict[str, Any]) -> bool:
    """Ensure the 'records' dictionary exists in the data."""
    if "records" not in json_data:
        json_data["records"] = {
            "fastest": RaceAnalyzer.getFastestTimesJson(json_data),
            "tyre-stats": RaceAnalyzer.getTyreStintRecordsDict(json_data)
        }
        return True
    return False

