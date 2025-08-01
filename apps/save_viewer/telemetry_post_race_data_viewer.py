# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
# pylint: skip-file

import asyncio
import argparse
import errno
import json
import logging
import os
import socket
import sys
import webbrowser
from http import HTTPStatus
from threading import Event, Lock, Thread, Timer
from typing import Any, Dict, List, Optional, Set, Tuple
from functools import partial

import msgpack
# pylint: disable=unused-import

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lib.overtake_analyzer as OvertakeAnalyzer
import lib.race_analyzer as RaceAnalyzer
from apps.save_viewer.logger import png_logger
from lib.child_proc_mgmt import (notify_parent_init_complete,
                                 report_pid_from_child)
from lib.error_status import PNG_ERROR_CODE_PORT_IN_USE, PNG_ERROR_CODE_UNKNOWN
from lib.f1_types import F1Utils, LapHistoryData, ResultStatus
from lib.ipc import IpcChildAsync
from lib.tyre_wear_extrapolator import TyreWearPerLap
from lib.version import get_version
from lib.port_check import is_port_available
from lib.web_server import BaseWebServer, ClientType
from quart import jsonify, render_template, request # TODO abstract away quart

def find_free_port():
    """Find an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]

class SilentLog:
    def write(self, msg):
        pass
    def flush(self):
        pass

g_json_data = {}
g_json_path = ''
g_json_lock = Lock()
g_should_open_ui = True
g_port_number = None
ui_initialized = False  # Flag to track if UI has been initialized
_race_table_clients : Set[str] = set()
_player_overlay_clients : Set[str] = set()
_server: Optional["TelemetryWebServer"] = None
g_shutdown_event = Event()

async def sendRaceTable() -> None:
    """Send race table to all connected clients
    """
    await _server.send_to_clients_of_type('race-table-update', getTelemetryInfo(), ClientType.RACE_TABLE)
    png_logger.debug("Sending race table update")

def getDeltaPlusPenaltiesPlusPit(
        delta: str,
        penalties: str,
        is_pitting: bool,
        dnf_status_code: str):
    """
    Get delta plus penalties plus pit information.

    Args:
        delta (str): Delta information.
        penalties (str): Penalties information.
        is_pitting (bool): Whether the driver is pitting.
        dnf_status_code (str): The code indicating DNF status. Empty string if driver is still racing

    Returns:
        str: Delta plus penalties plus pit information.
    """

    if dnf_status_code != "":
        return dnf_status_code
    elif is_pitting:
        return f"PIT {penalties}"
    elif delta is not None:
        return f"{delta} {penalties}"
    else:
        return "---"

def getTelemetryInfo():

    def getTyreWearJSON(data_per_driver: Dict[str, Any]):
        if "car-damage" not in data_per_driver:
            return TyreWearPerLap(
                fl_tyre_wear=None,
                fr_tyre_wear=None,
                rl_tyre_wear=None,
                rr_tyre_wear=None,
                desc="curr tyre wear"
            ).toJSON()
        else:
            return TyreWearPerLap(
                fl_tyre_wear=data_per_driver["car-damage"]["tyres-wear"][F1Utils.INDEX_FRONT_LEFT],
                fr_tyre_wear=data_per_driver["car-damage"]["tyres-wear"][F1Utils.INDEX_FRONT_RIGHT],
                rl_tyre_wear=data_per_driver["car-damage"]["tyres-wear"][F1Utils.INDEX_REAR_LEFT],
                rr_tyre_wear=data_per_driver["car-damage"]["tyres-wear"][F1Utils.INDEX_REAR_RIGHT],
                desc="curr tyre wear"
            ).toJSON()

    def getFastestLapTimeMsFromSessionHistoryJSON(session_history: Dict[str, Any]) -> int:
        fastest_lap_num = session_history["best-lap-time-lap-num"]
        if fastest_lap_num == 0:
            return 0

        fastest_lap_index = fastest_lap_num-1
        assert 0 <= fastest_lap_index < len(session_history["lap-history-data"])

        return session_history["lap-history-data"][fastest_lap_index]["lap-time-in-ms"]

    def getLastLapTimeMsFromSessionHistoryJSON(session_history: Dict[str, Any]) -> int:
        if last_lap := next(
            (entry for entry in reversed(session_history["lap-history-data"]) if entry.get("lap-time-in-ms", 0) > 0),
            None
        ):
            return last_lap["lap-time-in-ms"]
        return 0

    def getSectorStatus(
        data_per_driver: Dict[str, Any],
        sector_1_best_ms_global: Optional[int],
        # sector_1_best_ms_driver: Optional[int],
        sector_2_best_ms_global: Optional[int],
        # sector_2_best_ms_driver: Optional[int],
        sector_3_best_ms_global: Optional[int],
        # sector_3_best_ms_driver: Optional[int],
        result_status: Optional[str],
        for_best_lap: bool) -> List[Optional[int]]:
        """
        Determine sector status for either best or last lap.

        Args:
            sector_1_best_ms: Best sector 1 time in milliseconds
            sector_2_best_ms: Best sector 2 time in milliseconds
            sector_3_best_ms: Best sector 3 time in milliseconds
            for_best_lap: Whether to analyze best lap or last lap

        Returns:
            List of sector statuses (purple, green, yellow, invalid, or NA)
        """
        default_val = [
            F1Utils.SECTOR_STATUS_NA,
            F1Utils.SECTOR_STATUS_NA,
            F1Utils.SECTOR_STATUS_NA
        ]

        packet_session_history = data_per_driver.get("session-history")

        # Validate input data
        if (not packet_session_history or
            not sector_1_best_ms_global or
            # not sector_1_best_ms_driver or
            not sector_2_best_ms_global or
            # not sector_2_best_ms_driver or
            not sector_3_best_ms_global):# or
            # not sector_3_best_ms_driver):
            return default_val

        self_best_lap_num = packet_session_history["best-lap-time-lap-num"]
        self_m_best_lap_ms = getFastestLapTimeMsFromSessionHistoryJSON(packet_session_history)
        self_m_last_lap_ms = getLastLapTimeMsFromSessionHistoryJSON(packet_session_history)
        self_m_current_lap = data_per_driver["current-lap"]

        # Validate lap data
        if for_best_lap and not self_m_best_lap_ms:
            return default_val
        elif (not for_best_lap) and not self_m_last_lap_ms:
            return default_val

        # Select lap details
        if for_best_lap:
            lap_num = packet_session_history["best-lap-time-lap-num"]
        elif result_status != str(ResultStatus.ACTIVE):
            lap_num = self_m_current_lap
        else:
            lap_num = self_m_current_lap - 1

        # Validate lap number. Can have missing laps if red flag
        if not (0 <= lap_num <= len(packet_session_history["lap-history-data"])):
            return default_val

        # Get lap data
        best_sector_3_lap = packet_session_history["best-sector-3-lap-num"]
        best_sector_2_lap = packet_session_history["best-sector-2-lap-num"]
        best_sector_1_lap = packet_session_history["best-sector-1-lap-num"]
        lap_obj = packet_session_history["lap-history-data"][lap_num-1]
        lap_valid_flags = lap_obj["lap-valid-bit-flags"]

        # Analyze sector statuses
        s1_status = _get_sector_status(
            lap_obj["sector-1-time-in-ms"],
            sector_best_ms=sector_1_best_ms_global,
            is_best_sector_lap=(lap_num == best_sector_1_lap),
            sector_valid_flag=lap_valid_flags & LapHistoryData.SECTOR_1_VALID_BIT_MASK
        )

        s2_status = _get_sector_status(
            lap_obj["sector-2-time-in-ms"],
            sector_2_best_ms_global,
            lap_num == best_sector_2_lap,
            sector_valid_flag=lap_valid_flags & LapHistoryData.SECTOR_2_VALID_BIT_MASK
        )

        s3_status = _get_sector_status(
            lap_obj["sector-3-time-in-ms"],
            sector_3_best_ms_global,
            lap_num == best_sector_3_lap,
            sector_valid_flag=lap_valid_flags & LapHistoryData.SECTOR_3_VALID_BIT_MASK
        )

        return [s1_status, s2_status, s3_status]

    def _get_sector_status(
        sector_time: int,
        sector_best_ms: int,
        is_best_sector_lap: bool,
        sector_valid_flag: bool
    ) -> int:
        """
        Determine the status of a single sector.

        Args:
            sector_time: Time of the current sector
            sector_best_ms: Best time for the sector
            is_best_sector_lap: Whether this is the best lap for this sector
            sector_valid_flag: Whether the sector is valid

        Returns:
            Sector status (purple, green, yellow, invalid)
        """
        if sector_time == sector_best_ms:
            # Session best
            return F1Utils.SECTOR_STATUS_PURPLE
        elif is_best_sector_lap:
            # Personal best
            return F1Utils.SECTOR_STATUS_GREEN
        elif not sector_valid_flag:
            # Invalidated
            return F1Utils.SECTOR_STATUS_INVALID
        else:
            # Meh sector
            return F1Utils.SECTOR_STATUS_YELLOW


    # Init the global data onto the JSON repsonse
    with g_json_lock:
        if not g_json_data:
            return {
                "live-data": False,
                "circuit": "---",
                "current-lap": "---",
                "event-type": "---",
                "fastest-lap-overall": 0,
                "fastest-lap-overall-driver": "---",
                "pit-speed-limit": 0,
                "race-ended": True,
                "safety-car-status": "",
                "table-entries": [],
                "total-laps": "---",
                "track-temperature": 0,
                "air-temperature" : 0,
                "weather-forecast-samples": [],
                "f1-game-year" : None,
                "f1-packet-format" : None,
                "is-spectating" : False,
                "spectator-car-index" : None,
                "wdt-status" : False,
            }
        if "records" in g_json_data:
            if "fastest" in g_json_data["records"]:
                fastest_lap = g_json_data["records"]["fastest"]["lap"]["time"]
                fastest_lap_driver = g_json_data["records"]["fastest"]["lap"]['driver-name']
            else:
                fastest_lap = "---"
                fastest_lap_driver = "---"
        else:
            fastest_lap = "---"
            fastest_lap_driver = "---"
        json_response = {
            "live-data": False,
            "circuit": g_json_data["session-info"]["track-id"],
            "track-temperature": g_json_data["session-info"]["track-temperature"],
            "air-temperature" : g_json_data["session-info"]["air-temperature"],
            "event-type": g_json_data["session-info"]["session-type"],
            "session-time-left" : 0,
            "total-laps": g_json_data["session-info"]["total-laps"],
            "current-lap": g_json_data["classification-data"][0]["lap-data"]["current-lap-num"],
            "safety-car-status": g_json_data["session-info"]["safety-car-status"],
            "fastest-lap-overall": fastest_lap,
            "fastest-lap-overall-driver": fastest_lap_driver,
            "fastest-lap-overall-tyre" : None,
            "pit-speed-limit" : g_json_data["session-info"]["pit-speed-limit"],
            "weather-forecast-samples": [],
            "race-ended" : True,
            "f1-game-year" : g_json_data["game-year"],
            "f1-packet-format" : g_json_data.get("packet-format"),
            "packet-format" : g_json_data.get("packet-format"),
            "is-spectating" : False,
            "spectator-car-index" : None,
            "wdt-status" : False,
        }
        for sample in g_json_data["session-info"]["weather-forecast-samples"]:
            json_response["weather-forecast-samples"].append(
                {
                    "time-offset": str(sample["time-offset"]),
                    "weather": str(sample["weather"]),
                    "rain-probability": str(sample["rain-percentage"])
                }
            )

        json_response["table-entries"] = []
        result_str_map = {
            str(ResultStatus.DID_NOT_FINISH) : "DNF",
            str(ResultStatus.DISQUALIFIED) : "DSQ",
            str(ResultStatus.RETIRED) : "DNF"
        }
        best_s1_time = g_json_data["records"]["fastest"]["s1"]["time"]
        best_s2_time = g_json_data["records"]["fastest"]["s2"]["time"]
        best_s3_time = g_json_data["records"]["fastest"]["s3"]["time"]
        for data_per_driver in g_json_data["classification-data"]:
            index = data_per_driver["index"]
            # skip dummy/blank entries
            if data_per_driver["driver-name"] is None or data_per_driver["team"] is None:
                continue
            is_fastest = (index == g_json_data["records"]["fastest"]["lap"]["driver-index"])
            position = data_per_driver["track-position"]
            if position == 1:
                delta_relative = 0
            else:
                delta_relative = data_per_driver["lap-data"]["delta-to-race-leader-in-ms"]
            delta_to_leader = delta_relative
            dnf_status_code = result_str_map.get(data_per_driver["lap-data"]["result-status"], "")
            ers_perc = data_per_driver["car-status"]["ers-store-energy"] / data_per_driver["car-status"]["ers-max-capacity"] * 100.0

            time_pens = data_per_driver["lap-data"]["penalties"]
            num_dt = data_per_driver["lap-data"]["num-unserved-drive-through-pens"]
            num_sg = data_per_driver["lap-data"]["num-unserved-stop-go-pens"]

            json_response["table-entries"].append(
                {
                    "driver-info": {
                        "position": position,
                        "name": data_per_driver["driver-name"],
                        "team": data_per_driver["participant-data"]["team-id"],
                        "is-fastest": is_fastest,
                        "is-player": data_per_driver["is-player"],
                        "dnf-status": dnf_status_code,
                        "index": index,
                        "telemetry-setting": data_per_driver[
                            "participant-data"
                        ][
                            "telemetry-setting"
                        ],  # Already NULL checked
                        "drs": False,
                    },
                    "delta-info": {
                        "delta": delta_relative,
                        "delta-to-leader": delta_to_leader,
                    },
                    "ers-info": {
                        "ers-percent": f'{F1Utils.floatToStr(ers_perc)}%',
                        "ers-percent-float": ers_perc,
                        "ers-mode": (
                            data_per_driver["car-status"]["ers-deploy-mode"]
                            if "ers-deploy-mode"
                            in data_per_driver["car-status"]
                            else "None"
                        ),
                    },
                    "lap-info": {
                        "current-lap": None,
                        "last-lap": {
                            "lap-time-ms": getLastLapTimeMsFromSessionHistoryJSON(
                                data_per_driver["session-history"]
                            ),
                            "lap-time-ms-player": 0,
                            "sector-status": getSectorStatus(
                                data_per_driver,
                                best_s1_time,
                                best_s2_time,
                                best_s3_time,
                                data_per_driver["lap-data"]["result-status"],
                                for_best_lap=False,
                            ),
                        },
                        "best-lap": {
                            "lap-time-ms": getFastestLapTimeMsFromSessionHistoryJSON(
                                data_per_driver["session-history"]
                            ),
                            "lap-time-ms-player": 0,
                            "sector-status": getSectorStatus(
                                data_per_driver,
                                best_s1_time,
                                best_s2_time,
                                best_s3_time,
                                data_per_driver["lap-data"]["result-status"],
                                for_best_lap=True,
                            ),
                        },
                        "lap-progress": None,  # NULL is supported,
                        "speed-trap-record-kmph": (
                            data_per_driver["lap-data"][
                                "speed-trap-fastest-speed"
                            ]
                            if "speed-trap-fastest-speed"
                            in data_per_driver["lap-data"]
                            else None
                        ),
                        "top-speed-kmph": data_per_driver.get(
                            "top-speed-kmph", 0.0
                        ),
                    },
                    "warns-pens-info": {
                        "corner-cutting-warnings": data_per_driver["lap-data"][
                            "corner-cutting-warnings"
                        ],
                        "time-penalties": time_pens,
                        "num-dt": num_dt,
                        "num-sg": num_sg,
                    },
                    "tyre-info": {
                        "wear-prediction": {
                            "status": False,
                            "desc": "Insufficient data for extrapolation",
                            "predictions": [],
                            "selected-pit-stop-lap": None,
                        },
                        "current-wear": getTyreWearJSON(data_per_driver),
                        "tyre-age": data_per_driver["car-status"][
                            "tyres-age-laps"
                        ],
                        "tyre-life-remaining": None,
                        "actual-tyre-compound": data_per_driver["car-status"][
                            "actual-tyre-compound"
                        ],
                        "visual-tyre-compound": data_per_driver["car-status"][
                            "visual-tyre-compound"
                        ],
                        "num-pitstops": (
                            data_per_driver["final-classification"]["num-pit-stops"]
                            if data_per_driver.get("final-classification") is not None
                            else data_per_driver.get("lap-data", {}).get("num-pit-stops")
                        ),
                    },
                    "damage-info": {
                        "fl-wing-damage": data_per_driver["car-damage"][
                            "front-left-wing-damage"
                        ],
                        "fr-wing-damage": data_per_driver["car-damage"][
                            "front-right-wing-damage"
                        ],
                        "rear-wing-damage": data_per_driver["car-damage"][
                            "rear-wing-damage"
                        ],
                    },
                    "fuel-info": {
                        "fuel-capacity": data_per_driver["car-status"][
                            "fuel-capacity"
                        ],
                        "fuel-mix": data_per_driver["car-status"]["fuel-mix"],
                        "fuel-remaining-laps": data_per_driver["car-status"][
                            "fuel-remaining-laps"
                        ],
                        "fuel-in-tank": data_per_driver["car-status"][
                            "fuel-in-tank"
                        ],
                        "curr-fuel-rate": 0.0,
                        "last-lap-fuel-used": 0.0,
                        "target-fuel-rate-average": 0.0,
                        "target-fuel-rate-next-lap": 0.0,
                        "surplus-laps-png": 0.0,
                        "surplus-laps-game": 0.0,
                    },
                }
            )

        json_response["table-entries"].sort(key=lambda x: x["driver-info"]["position"])
        return json_response

def getDriverInfoJsonByIndex(index):

    with g_json_lock:
        final_json = {}
        global g_json_data
        if not g_json_data:
            return final_json

        driver_data = next(
            (
                driver
                for driver in g_json_data["classification-data"]
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
        final_json["track-position"] = driver_data["final-classification"]["position"]
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

        # Insert the per lap backup
        final_json["per-lap-info"] = driver_data["per-lap-info"]

        # Insert the warnings and penalties
        if "warning-penalty-history" in driver_data:
            final_json["warning-penalty-history"] = driver_data["warning-penalty-history"]
        else:
            final_json["warning-penalty-history"] = []

        # collisions
        final_json["collisions"] = driver_data["collisions"] if "collisions" in driver_data else {}

        # Return this fully prepped JSON
        return final_json

def handleDriverInfoRequest(index: str, is_str_input: bool=True) -> Tuple[Dict[str, Any], HTTPStatus]:

    # Check if only one parameter is provided
    if is_str_input:
        if not index:
            error_response = {
                'error': 'Invalid parameters',
                'message': 'Provide "index" parameter'
            }
            return error_response, HTTPStatus.BAD_REQUEST

        # Check if the provided value for index is numeric
        if not index.isdigit():
            error_response = {
                'error': 'Invalid parameter value',
                'message': '"index" parameter must be numeric'
            }
            return error_response, HTTPStatus.BAD_REQUEST

        # Process parameters and generate response
        index = int(index)
    else:
        if index is None:
            return {
                'error': 'Invalid parameters',
                'message': 'Provide index parameter'
            }

        # Check if the provided value for index is numeric
        if not isinstance(index, int) and not index.isdigit():
            return {
                'error': 'Invalid parameter value',
                'message': 'index parameter must be numeric'
            }

    driver_info = getDriverInfoJsonByIndex(index)
    if driver_info:
        return driver_info, HTTPStatus.OK
    error_response = {
        'error' : 'Invalid parameter value',
        'message' : 'Invalid index'
    }
    return error_response, HTTPStatus.NOT_FOUND

def getDriverByNameTeam(name, team, classification_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get driver by name. (assumes lock is already acquired)

    Args:
        name (str): Name of the driver
        classification_data (List[Dict[str, Any]]): Classification data

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

def getTyreStintHistoryJSON() -> List[Dict[str, Any]]:
    """Get tyre stint history. (Assumes lock is already acquired)"""
    global g_json_data
    if not g_json_data:
        return []

    old_style = g_json_data.get("tyre-stint-history", [])
    for driver_entry in old_style:
        if not (driver_data := getDriverByNameTeam(driver_entry["name"], driver_entry["team"], g_json_data["classification-data"])):
            # if required data is not available for any of the drivers, return empty list
            png_logger.debug(f"Driver data not available for {driver_entry['name']}")
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

def handleRaceInfoRequest() -> Tuple[Dict[str, Any], HTTPStatus]:

    with g_json_lock:
        global g_json_data
        global g_json_path

        if not g_json_data:
            return {}, HTTPStatus.OK

        ret = {
            "session-info" : g_json_data["session-info"],
            "records" : g_json_data.get("records", None),
            "overtakes" : g_json_data.get("overtakes", None),
            "custom-markers" : g_json_data.get("custom-markers", []),
            "position-history" : g_json_data.get("position-history", []),
            "speed-trap-records" : g_json_data.get("speed-trap-records", []),
        }

        if new_style := g_json_data.get("tyre-stint-history-v2"):
            ret["tyre-stint-history-v2"] = new_style
        else:
            ret["tyre-stint-history"] = getTyreStintHistoryJSON()

        return ret, HTTPStatus.OK

class TelemetryWebServer(BaseWebServer):
    """
    A web server class for handling telemetry-related web services and socket communications.

    This class sets up HTTP and WebSocket routes for serving telemetry data,
    static files, and managing client connections.

    Attributes:
        m_port (int): The port number on which the server will run.
        m_debug_mode (bool): Flag to enable/disable debug mode.
        m_app (Quart): The Quart web application instance.
        m_sio (socketio.AsyncServer): The Socket.IO server instance.
        m_sio_app (socketio.ASGIApp): The combined Quart and Socket.IO ASGI application.
        m_ver_str (str): The version string.
        m_logger (logging.Logger): The logger instance.
    """

    def __init__(self,
                 port: int,
                 ver_str: str,
                 logger: logging.Logger,
                 cert_path: Optional[str] = None,
                 key_path: Optional[str] = None,
                 disable_browser_autoload: bool = False,
                 debug_mode: bool = False):
        """
        Initialize the TelemetryWebServer.

        Args:
            port (int): The port number to run the server on.
            ver_str (str): The version string.
            logger (logging.Logger): The logger instance.
            cert_path (Optional[str], optional): Path to the certificate file. Defaults to None.
            key_path (Optional[str], optional): Path to the key file. Defaults to None.
            disable_browser_autoload (bool, optional): Whether to disable browser autoload. Defaults to False.
            debug_mode (bool, optional): Enable or disable debug mode. Defaults to False.
        """
        super().__init__(port, ver_str, logger, cert_path, key_path, disable_browser_autoload, debug_mode)
        self.define_routes()
        self.register_post_start_callback(self._post_start)
        self.register_on_client_connect_callback(self._on_client_connect)

    def define_routes(self) -> None:
        """
        Define all HTTP routes for the web server.

        This method calls sub-methods to set up file and data routes.
        """

        self._defineTemplateFileRoutes()
        self._defineDataRoutes()

    def _defineTemplateFileRoutes(self) -> None:
        """
        Define routes for rendering HTML templates.

        Sets up routes for the main index page and stream overlay page.
        """
        @self.http_route('/')
        async def index() -> str:
            """
            Render the main index page.

            Returns:
                str: Rendered HTML content for the index page.
            """
            return await render_template('driver-view.html', live_data_mode=False, version=self.m_ver_str)

    def _defineDataRoutes(self) -> None:
        """
        Define HTTP routes for retrieving telemetry and race-related data.

        Sets up endpoints for fetching race info, telemetry info,
        driver info, and stream overlay info.
        """
        @self.http_route('/telemetry-info')
        async def telemetryInfoHTTP() -> Tuple[str, int]:
            """
            Provide telemetry information via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return getTelemetryInfo()

        @self.http_route('/race-info')
        async def raceInfoHTTP() -> Tuple[str, int]:
            """
            Provide overall race statistics via HTTP.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return handleRaceInfoRequest()

        @self.http_route('/driver-info')
        async def driverInfoHTTP() -> Tuple[str, int]:
            """
            Provide driver information based on the index parameter.

            Returns:
                Tuple[str, int]: JSON response and HTTP status code.
            """
            return handleDriverInfoRequest(request.args.get('index'))

    def _checkUpdateRecords(self, json_data: Dict[str, Any]) -> bool:

        def _isValidJson(data):
            if isinstance(data, dict):
                return True
            try:
                json.loads(data)
                return True
            except json.JSONDecodeError:
                return False

        should_write = False

        if "records" not in json_data:
            json_data["records"] = {}
            should_write = True

        if "fastest" not in json_data["records"]:
            json_data["records"]["fastest"] = RaceAnalyzer.getFastestTimesJson(json_data)
            should_write = True
        should_recompute_fastest_records = False
        expected_fastest_record_keys = [
            'driver-index',
            'driver-name',
            'team-id',
            'lap-number',
            'time',
            'time-str'
        ]
        for category, record in json_data["records"]["fastest"].items():
            for key in expected_fastest_record_keys:
                if key not in record:
                    should_recompute_fastest_records = True
                    break
        if should_recompute_fastest_records:
            json_data["records"]["fastest"] = RaceAnalyzer.getFastestTimesJson(json_data)
            should_write = True


        if "tyre-stats" not in json_data["records"]:
            json_data["records"]["tyre-stats"] = RaceAnalyzer.getTyreStintRecordsDict(json_data)
            should_write = True
        tyre_stats_keys = ['longest-tyre-stint', 'lowest-tyre-wear-per-lap', 'highest-tyre-wear']
        should_recompute_tyre_stats = False
        for key in tyre_stats_keys:
            # Loop through the compounds
            for compound, tyre_stat_record in json_data["records"]["tyre-stats"].items():
                if key not in tyre_stat_record:
                    should_recompute_tyre_stats = True

        if should_recompute_tyre_stats:
            json_data["records"]["tyre-stats"] = RaceAnalyzer.getTyreStintRecordsDict(json_data)
            should_write = True

        should_recompute_overtakes = False
        if "overtakes" not in json_data:
            json_data["overtakes"] = {
                "records" : []
            }
            should_write = True
            should_recompute_overtakes = True

        expected_keys = [
            "number-of-overtakes",
            "most-heated-rivalries"
        ]
        for key in expected_keys:
            if key not in json_data["overtakes"]:
                should_recompute_overtakes = True

        if should_recompute_overtakes and len(json_data["overtakes"]["records"]) > 0:
            if _isValidJson(json_data["overtakes"]["records"][0]):
                overtake_analyzer_mode = OvertakeAnalyzer.OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS_JSON
            else:
                overtake_analyzer_mode = OvertakeAnalyzer.OvertakeAnalyzerMode.INPUT_MODE_LIST_CSV
            overtake_records = OvertakeAnalyzer.OvertakeAnalyzer(
                input_mode=overtake_analyzer_mode,
                input_data=json_data["overtakes"]["records"]).toJSON()
            json_data["overtakes"] = json_data["overtakes"] | overtake_records
            should_write = True

        return should_write

    async def _post_start(self) -> None:
        notify_parent_init_complete()

    async def _on_client_connect(self, client_type: ClientType) -> None:
        if client_type == ClientType.RACE_TABLE:
            await sendRaceTable()

def checkRecomputeJSON(json_data : Dict[str, Any]) -> bool:

    def _isValidJson(data):
        if isinstance(data, dict):
            return True
        try:
            json.loads(data)
            return True
        except json.JSONDecodeError:
            return False

    def _getTyreWearHistory(driver_data : Dict[str, Any], start_lap : int, end_lap : int) -> List[Dict[str, Any]]:

        tyre_wear_history = []
        range_of_laps = range(start_lap, end_lap + 1)
        if "per-lap-info" in driver_data:
            for lap_backup in driver_data["per-lap-info"]:
                lap_number = lap_backup['lap-number']
                if lap_number not in range_of_laps:
                    continue
                if "car-damage-data" in lap_backup:
                    tyre_wear_history.append({
                        'lap-number' : lap_number,
                        'front-left-wear' : lap_backup["car-damage-data"]["tyres-wear"][F1Utils.INDEX_FRONT_LEFT],
                        'front-right-wear' : lap_backup["car-damage-data"]["tyres-wear"][F1Utils.INDEX_FRONT_RIGHT],
                        'rear-left-wear' : lap_backup["car-damage-data"]["tyres-wear"][F1Utils.INDEX_REAR_LEFT],
                        'rear-right-wear' : lap_backup["car-damage-data"]["tyres-wear"][F1Utils.INDEX_REAR_RIGHT],
                    })
        return tyre_wear_history

    should_write = False
    if "classification-data" in json_data:
        for driver_data in json_data["classification-data"]:
            if "tyre-set-history" in driver_data:
                for tyre_stint in driver_data["tyre-set-history"]:
                    if "tyre-wear-history" not in tyre_stint:
                        should_write = True
                        tyre_stint["tyre-wear-history"] = _getTyreWearHistory(
                            driver_data, tyre_stint["start-lap"], tyre_stint["end-lap"])


    if "records" not in json_data:
        json_data["records"] = {
            "fastest" : RaceAnalyzer.getFastestTimesJson(json_data),
            "tyre-stats" : RaceAnalyzer.getTyreStintRecordsDict(json_data)
        }
        should_write = True

    if "fastest" not in json_data["records"]:
        json_data["records"]["fastest"] = RaceAnalyzer.getFastestTimesJson(json_data)
        should_write = True
    should_recompute_fastest_records = False
    expected_fastest_record_keys = [
        'driver-index',
        'driver-name',
        'team-id',
        'lap-number',
        'time',
        'time-str'
    ]
    for _, record in json_data["records"]["fastest"].items():
        for key in expected_fastest_record_keys:
            if key not in record:
                should_recompute_fastest_records = True
                break
    if should_recompute_fastest_records:
        json_data["records"]["fastest"] = RaceAnalyzer.getFastestTimesJson(json_data)
        should_write = True

    if "tyre-stats" not in json_data["records"]:
        json_data["records"]["tyre-stats"] = RaceAnalyzer.getTyreStintRecordsDict(json_data)
        should_write = True
    tyre_stats_keys = ['longest-tyre-stint', 'lowest-tyre-wear-per-lap', 'highest-tyre-wear']
    should_recompute_tyre_stats = False
    for key in tyre_stats_keys:
        # Loop through the compounds
        for compound, tyre_stat_record in json_data["records"]["tyre-stats"].items():
            if key not in tyre_stat_record:
                should_recompute_tyre_stats = True

    if should_recompute_tyre_stats:
        json_data["records"]["tyre-stats"] = RaceAnalyzer.getTyreStintRecordsDict(json_data)
        should_write = True

    should_recompute_overtakes = False
    if "overtakes" not in json_data:
        json_data["overtakes"] = {
            "records" : []
        }
        should_write = True
        should_recompute_overtakes = True

    expected_keys = [
        "number-of-overtakes",
        "most-heated-rivalries"
    ]
    for key in expected_keys:
        if key not in json_data["overtakes"]:
            should_recompute_overtakes = True

    if should_recompute_overtakes and len(json_data["overtakes"]["records"]) > 0:
        if _isValidJson(json_data["overtakes"]["records"][0]):
            overtake_analyzer_mode = OvertakeAnalyzer.OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS_JSON
        else:
            overtake_analyzer_mode = OvertakeAnalyzer.OvertakeAnalyzerMode.INPUT_MODE_LIST_CSV
        overtake_records = OvertakeAnalyzer.OvertakeAnalyzer(
            input_mode=overtake_analyzer_mode,
            input_data=json_data["overtakes"]["records"]).toJSON()
        json_data["overtakes"] = json_data["overtakes"] | overtake_records
        should_write = True

    return should_write

async def open_file_helper(file_path, open_webpage=True):
    try:
        with open(file_path, 'r+', encoding='utf-8') as f:
            global g_json_lock
            global g_json_data
            global g_json_path
            global g_should_open_ui
            global g_port_number
            with g_json_lock:
                g_json_data = json.load(f)
                g_json_path = file_path

                should_write = False
                should_write |= checkRecomputeJSON(g_json_data)

            await sendRaceTable()

            if g_should_open_ui and open_webpage:
                g_should_open_ui = False
                webbrowser.open(f'http://localhost:{g_port_number}', new=2)

        png_logger.info(f"Opened file: {file_path}")
        return {"status": "success"}

    except (FileNotFoundError, PermissionError) as e:
        png_logger.error(f"Failed to open file: {file_path}. Error: {e}")
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}
    except json.JSONDecodeError as e:
        png_logger.error(f"Invalid JSON in file: {file_path}. Error: {e}")
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}
    except UnicodeDecodeError as e:
        png_logger.error(f"Invalid UTF-8 in file: {file_path}. Error: {e}")
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}
    except Exception as e:
        png_logger.exception(f"Unexpected error opening file: {file_path}")
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}

def open_webpage():
    global g_should_open_ui
    global g_port_number
    g_should_open_ui = False
    webbrowser.open(f'http://localhost:{g_port_number}', new=2)

def parseArgs() -> argparse.Namespace:
    """Parse the command line args and perform validation

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description="Pits n' Giggles save data viewer")

    # Add command-line arguments with default values
    parser.add_argument("--launcher", action="store_true", help="Enable launcher mode. Input is expeected via stdin")
    parser.add_argument("--port", type=int, default=None, help="Port number for the server.")
    parser.add_argument("--ipc-port", type=int, default=None, help="Port number for the IPC server.")

    # Parse the command-line arguments
    parsed_args = parser.parse_args()

    if parsed_args.launcher and parsed_args.port is None:
        png_logger.info("Port number is required in launcher mode")
        sys.exit(1)

    return parsed_args

def start_thread(target):
    """Start a thread for the given target function

    Args:
        target (function): The target function to run in the thread
    """
    thread = Thread(target=target)
    thread.daemon = True
    thread.start()

async def handle_ipc_message(msg: dict, logger: logging.Logger) -> dict:
    """Handles incoming IPC messages and dispatches commands."""
    png_logger.info(f"Received IPC message: {msg}")

    cmd = msg.get("cmd")
    args: dict = msg.get("args", {})

    if cmd == "open-file":
        return await _handle_open_file(args)
    elif cmd == "shutdown":
        Timer(1.0, shutdown_handler, [args.get("reason", "N/A")]).start()
        return {"status": "success"}

    return {"status": "error", "message": f"Unknown command: {cmd}"}

async def _handle_open_file(args: dict) -> dict:
    """Handles the 'open-file' IPC command."""
    if not (file_path := args.get("file-path")):
        return {"status": "error", "message": "Missing or invalid file path"}
    else:
        return await open_file_helper(file_path)

def shutdown_handler(reason: str) -> None:
    """Shutdown handler function.

    Args:
        reason (str): The reason for the shutdown
    """
    png_logger.info(f"Shutting down. Reason: {reason}")
    os._exit(0)


async def main():

    png_logger.debug(f"cwd={os.getcwd()}")
    global g_port_number
    args = parseArgs()
    version = get_version()

    tasks: List[asyncio.Task] = []


    ipc_server = IpcChildAsync(args.ipc_port, "Save Viewer")
    tasks.append(ipc_server.get_task(partial(handle_ipc_message, logger=png_logger)))
    g_port_number = args.port
    if not is_port_available(g_port_number):
        png_logger.error(f"Port {g_port_number} is not available")
        sys.exit(PNG_ERROR_CODE_PORT_IN_USE)

    # Start Flask server after Tkinter UI is initialized
    png_logger.info(f"Starting server. It can be accessed at http://localhost:{str(g_port_number)} "
                    f"PID = {os.getpid()} Version = {version}")
    global _server
    _server = TelemetryWebServer(
        port=g_port_number,
        ver_str=version,
        logger=png_logger)
    tasks.append(asyncio.create_task(_server.run(), name="Web Server Task"))
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        png_logger.debug("Main task was cancelled.")
        await _server.stop()
        for task in tasks:
            task.cancel()
        raise  # Ensure proper cancellation behavior
    try:
        _server.run()
    except OSError as e:
        png_logger.error(e)
        if e.errno == errno.EADDRINUSE:
            sys.exit(PNG_ERROR_CODE_PORT_IN_USE)
        else:
            sys.exit(PNG_ERROR_CODE_UNKNOWN)

def entry_point():
    report_pid_from_child()
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except asyncio.CancelledError:
        png_logger.info("Program shutdown gracefully.")
