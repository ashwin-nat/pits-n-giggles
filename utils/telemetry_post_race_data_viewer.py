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

from typing import Dict, Any, List, Set, Tuple, Optional
from http import HTTPStatus
import logging
import json
from threading import Lock, Thread
import sys
import os
import tkinter as tk
from tkinter import filedialog
import time
import webbrowser
import socket
# pylint: disable=unused-import
from engineio.async_drivers import gevent

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.f1_types import F1Utils, LapData, ResultStatus
import lib.race_analyzer as RaceAnalyzer
import lib.overtake_analyzer as OvertakeAnalyzer
from lib.tyre_wear_extrapolator import TyreWearPerLap
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

g_json_data = {}
g_json_path = ''
g_json_lock = Lock()
ui_initialized = False  # Flag to track if UI has been initialized
_race_table_clients : Set[str] = set()
_player_overlay_clients : Set[str] = set()
_server: Optional["TelemetryWebServer"] = None

def sendRaceTable():

    if len(_race_table_clients) > 0:
        _server.m_socketio.emit('race-table-update', getTelemetryInfo())
        print("Sending race table update")

def _getPenaltyString(penalties_sec: int, num_dt: int, num_sg: int) -> str:
    """Computes and returns a printable string capturing all penalties

    Args:
        penalties_sec (int): The time penalty in second
        num_dt (int): Number of drive through penalties
        num_sg (int): Number of stop/go penalties

    Returns:
        str: The penalty string
    """

    if penalties_sec == 0 and num_dt == 0 and num_sg == 0:
        return ""
    penalty_string = "("
    started_filling = False
    if penalties_sec > 0:
        penalty_string += "+" + str(penalties_sec) + " sec"
        started_filling = True
    if num_dt > 0:
        if started_filling:
            penalty_string += " + "
        penalty_string += str(num_dt) + "DT"
        started_filling = True
    if num_sg:
        if started_filling:
            penalty_string += " + "
        penalty_string += str(num_sg) + "SG"
    penalty_string += ")"
    return penalty_string

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

    if len(dnf_status_code) > 0:
        return dnf_status_code
    elif is_pitting:
        return "PIT " + penalties
    elif delta is not None:
        return delta + " " + penalties
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
        return session_history["lap-history-data"][-1]["lap-time-in-ms"]


    # Init the global data onto the JSON repsonse
    with g_json_lock:
        if not g_json_data:
            return {
                "circuit": "---",
                "current-lap": "---",
                "event-type": "---",
                "fastest-lap-overall": 0,
                "pit-speed-limit": "---",
                "race-ended": False,
                "safety-car-status": "",
                "table-entries": [],
                "total-laps": "---",
                "track-temperature": "---",
                "air-temperature" : "---",
                "weather-forecast-samples": []
            }
        if "records" in g_json_data:
            if "fastest" in g_json_data["records"]:
                fastest_lap = g_json_data["records"]["fastest"]["lap"]["time"]
            else:
                fastest_lap = "---"
        else:
            fastest_lap = "---"
        json_response = {
            "circuit": g_json_data["session-info"]["track-id"],
            "track-temperature": g_json_data["session-info"]["track-temperature"],
            "air-temperature" : g_json_data["session-info"]["air-temperature"],
            "event-type": g_json_data["session-info"]["session-type"],
            "session-time-left" : 0,
            "total-laps": g_json_data["session-info"]["total-laps"],
            "current-lap": g_json_data["classification-data"][0]["lap-data"]["current-lap-num"],
            "safety-car-status": g_json_data["session-info"]["safety-car-status"],
            "fastest-lap-overall": fastest_lap,
            "pit-speed-limit" : g_json_data["session-info"]["pit-speed-limit"],
            "weather-forecast-samples": [],
            "race-ended" : True
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
            ResultStatus.DID_NOT_FINISH : "DNF",
            ResultStatus.DISQUALIFIED : "DSQ",
            ResultStatus.RETIRED : "DNF"
        }
        for data_per_driver in g_json_data["classification-data"]:
            index = data_per_driver["index"]
            if index == g_json_data["records"]["fastest"]["lap"]["driver-index"]:
                is_fastest = True
            else:
                is_fastest = False
            position = data_per_driver["final-classification"]["position"]
            if position == 1:
                delta_relative = "---"
            else:
                delta_relative = F1Utils.millisecondsToSecondsMilliseconds(data_per_driver["lap-data"]["delta-to-race-leader-in-ms"])
            delta_to_leader = delta_relative
            penalties = _getPenaltyString(
                penalties_sec=data_per_driver["lap-data"]["penalties"],
                num_dt=data_per_driver["lap-data"]["num-unserved-drive-through-pens"],
                num_sg=data_per_driver["lap-data"]["num-unserved-stop-go-pens"]
            )
            is_pitting = True if data_per_driver["lap-data"]["pit-status"] in \
                [str(LapData.PitStatus.PITTING),
                str(LapData.PitStatus.IN_PIT_AREA),
                str(LapData.PitStatus.PITTING.value),
                str(LapData.PitStatus.IN_PIT_AREA.value)] else False
            dnf_status_code = result_str_map.get(data_per_driver["lap-data"]["result-status"], "")
            ers_perc = data_per_driver["car-status"]["ers-store-energy"] / data_per_driver["car-status"]["ers-max-capacity"] * 100.0

            time_pens = data_per_driver["lap-data"]["penalties"]
            num_dt = data_per_driver["lap-data"]["num-unserved-drive-through-pens"]
            num_sg = data_per_driver["lap-data"]["num-unserved-stop-go-pens"]

            json_response["table-entries"].append(
                {
                    "driver-info" : {
                        "position": position,
                        "name": data_per_driver["driver-name"],
                        "team": data_per_driver["participant-data"]["team-id"],
                        "is-fastest": is_fastest,
                        "is-player": data_per_driver["is-player"],
                        "dnf-status" : dnf_status_code,
                        "index" : index,
                        "telemetry-setting" : data_per_driver["participant-data"]["telemetry-setting"], # Already NULL checked
                        "drs": False,
                    },
                    "delta-info" : {
                        "delta": getDeltaPlusPenaltiesPlusPit(delta_relative, penalties, is_pitting, dnf_status_code),
                        "delta-to-leader" : getDeltaPlusPenaltiesPlusPit(
                                                delta_to_leader, penalties, is_pitting, dnf_status_code),
                    },
                    "ers-info" : {
                        "ers-percent": F1Utils.floatToStr(ers_perc) + '%',
                    },
                    "lap-info" : {
                        "last-lap-ms" : getFastestLapTimeMsFromSessionHistoryJSON(data_per_driver["session-history"]),
                        "best-lap-ms" : getLastLapTimeMsFromSessionHistoryJSON(data_per_driver["session-history"]),
                        "last-lap-ms-player" : 0,
                        "best-lap-ms-overall" : 0,
                        "lap-progress" : None, # NULL is supported,
                        "speed-trap-record-kmph" : data_per_driver["lap-data"]["speed-trap-fastest-speed"] \
                            if "speed-trap-fastest-speed" in data_per_driver["lap-data"] else None
                    },
                    "warns-pens-info" : {
                        "corner-cutting-warnings" : data_per_driver["lap-data"]["corner-cutting-warnings"],
                        "time-penalties" : time_pens,
                        "num-dt" : num_dt,
                        "num-sg" : num_sg,
                    },
                    "tyre-info" : {
                        "wear-prediction" : [],
                        "current-wear" : getTyreWearJSON(data_per_driver),
                        "tyre-age": data_per_driver["car-status"]["tyres-age-laps"],
                        "tyre-life-remaining" : None,
                        "actual-tyre-compound" : data_per_driver["car-status"]["actual-tyre-compound"],
                        "visual-tyre-compound" : data_per_driver["car-status"]["visual-tyre-compound"],
                        "num-pitstops": data_per_driver["final-classification"]["num-pit-stops"],
                    },
                    "damage-info" : {
                        "fl-wing-damage" : data_per_driver["car-damage"]["front-left-wing-damage"],
                        "fr-wing-damage" : data_per_driver["car-damage"]["front-right-wing-damage"],
                        "rear-wing-damage" : data_per_driver["car-damage"]["rear-wing-damage"],
                    }
                }
            )

        return json_response

def getDriverInfoJsonByIndex(index):

    with g_json_lock:
        final_json = {}
        global g_json_data
        if not g_json_data:
            return final_json

        driver_data = None
        for driver in g_json_data["classification-data"]:
            if driver["index"] == index:
                driver_data = driver
                break

        if not driver_data:
            return final_json

        final_json["index"] = index
        final_json["is-player"] = driver_data["is-player"]
        final_json["driver-name"] = driver_data["driver-name"]
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
                'message': f'Provide index parameter'
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
    else:
        error_response = {
            'error' : 'Invalid parameter value',
            'message' : 'Invalid index'
        }
        return error_response, HTTPStatus.BAD_REQUEST

def handleRaceInfoRequest() -> Tuple[Dict[str, Any], HTTPStatus]:

    with g_json_lock:
        global g_json_data
        global g_json_path

        if not g_json_data:
            return {}, HTTPStatus.OK

        return {
            "records" : g_json_data.get("records", None),
            "classification-data" : g_json_data.get("classification-data", None),
            "overtakes" : g_json_data.get("overtakes", None),
            "custom-markers" : g_json_data.get("custom-markers", []),
            "position-history" : g_json_data.get("position-history", []),
        }, HTTPStatus.OK

class TelemetryWebServer:
    def __init__(self,
        port: int):
        """
        Initialize TelemetryServer.

        Args:
            port (int): Port number for the server.
        """
        self.m_app = Flask(__name__, template_folder='../src/templates')
        self.m_app.config['PROPAGATE_EXCEPTIONS'] = True
        self.m_app.config["EXPLAIN_TEMPLATE_LOADING"] = True
        self.m_port = port
        self.m_socketio = SocketIO(
            app=self.m_app,
            async_mode="gevent",
        )

        @self.m_app.route('/favicon.ico')
        def favicon():
            """Return the favicon file

            Returns:
                file: Favicon file
            """
            return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

        # Render the HTML page
        @self.m_app.route('/')
        def index():
            """
            Endpoint for the index page.

            Returns:
                str: HTML page content.
            """

            print('received request')
            return render_template('index.html',
                packet_capture_enabled=False,
                player_only_telemetry=False,
                live_data_mode=False)

        # Define your endpoint
        @self.m_app.route('/telemetry-info')
        def telemetryInfo() -> Dict[str, Any]:
            """
            Endpoint for telemetry information.

            Returns:
                str: Telemetry data in JSON format.
            """
            return getTelemetryInfo()

        @self.m_app.route('/driver-info', methods=['GET'])
        def driverInfo() -> Dict[str, Any]:
            """
            Endpoint for saving telemetry packet capture.

            Returns:
                str: JSON response indicating success or failure.
            """
            # Access parameters using request.args
            return handleDriverInfoRequest(request.args.get('index'))

        @self.m_app.route('/race-info', methods=['GET'])
        def raceInfo() -> Dict[str, Any]:
            return handleRaceInfoRequest()

        # Socketio endpoints
        @self.m_socketio.on('connect')
        def handleConnect():
            """SocketIO endpoint for handling client connection
            """
            print("Client connected")

        @self.m_socketio.on('disconnect')
        def handleDisconnect():
            """SocketIO endpoint for handling client disconnection
            """
            print("Client disconnected")
            _player_overlay_clients.discard(request.sid)
            _race_table_clients.discard(request.sid)

        @self.m_socketio.on('race-info')
        # pylint: disable=unused-argument
        def handeRaceInfo(dummy_arg: Any):
            """SocketIO endpoint to handle race info request
            """
            # TODO
            emit("race-info-response", handleRaceInfoRequest(), broadcast=False)

        @self.m_socketio.on('driver-info')
        def handleDriverInfo(data: Dict[str, Any]):
            """SocketIO endpoint to handle driver info request

            Args:
                data (Dict[str, Any]): The JSON response. Will contain the key "error" in case of failure
            """
            index = data.get("index", None)
            driver_info, _ = handleDriverInfoRequest(index, is_str_input=False)
            emit("driver-info-response", driver_info, broadcast=False)

        @self.m_socketio.on('register-client')
        def handleClientRegistration(data):
            """SocketIO endpoint to handle client registration
            """
            print('Client registered. SID = %s Type = %s', request.sid, data['type'])
            if data['type'] == 'player-stream-overlay':
                _player_overlay_clients.add(request.sid)
            elif data['type'] == 'race-table':
                _race_table_clients.add(request.sid)
                sendRaceTable()

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

        if should_recompute_overtakes:
            if len(json_data["overtakes"]["records"]) > 0:
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

    def run(self):
        """
        Run the TelemetryServer.
        """

        # Disable Werkzeug request logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logging.getLogger('socketio').setLevel(logging.ERROR)
        logging.getLogger('engineio').setLevel(logging.ERROR)
        logging.getLogger('gevent').setLevel(logging.ERROR)
        logging.getLogger('websocket').setLevel(logging.ERROR)

        self.m_socketio.run(
            app=self.m_app,
            debug=False,
            port=self.m_port,
            use_reloader=False)

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

    if should_recompute_overtakes:
        if len(json_data["overtakes"]["records"]) > 0:
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

def open_file_helper(file_path):
    with open(file_path, 'r+', encoding='utf-8') as f:
        global g_json_lock
        global g_json_data
        global g_json_path
        with g_json_lock:
            g_json_data = json.load(f)
            g_json_path = file_path

            should_write = False
            should_write |= checkRecomputeJSON(g_json_data)
        sendRaceTable()
    print("Opened file: " + file_path)

def open_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        status_label.config(text=f"Selected file: {file_path}")
        open_file_helper(file_path)
    else:
        status_label.config(text="No file selected")

def start_ui():
    global ui_initialized
    if not ui_initialized:
        ui_initialized = True  # Set flag to True
        # Create the main window
        print("UI thread")
        root = tk.Tk()
        root.title("F1 Post race analyzer")

        # Create a frame for the content
        frame = tk.Frame(root)
        frame.pack(padx=10, pady=10)

        # Create a label for status
        global status_label
        status_label = tk.Label(frame, text="No file selected")
        status_label.pack()

        # Create a button to open a file dialog
        open_button = tk.Button(frame, text="Open File", command=open_file)
        open_button.pack()

        # Run the Tkinter event loop
        root.protocol("WM_DELETE_WINDOW", on_closing)  # Call on_closing when window is closed
        root.mainloop()

def on_closing():
    print("UI done")
    os._exit(0)


def openWebPage(port_number : int) -> None:
    """Open the webpage on a new browser tab.

    Args:
        port_number (int) : The port number of the server

    """
    time.sleep(1)
    webbrowser.open('http://localhost:' + str(port_number), new=2)

def find_free_port():
    """Find an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]

def main():

    # Get port number
    port_number = find_free_port()

    # Start Tkinter UI
    ui_thread = Thread(target=start_ui)
    ui_thread.start()

    # Open the webpage
    webpage_thread = Thread(target=openWebPage, args=(port_number,))
    webpage_thread.start()

    # Start Flask server after Tkinter UI is initialized
    print("Starting server. It can be accessed at http://localhost:" + str(port_number))
    global _server
    _server = TelemetryWebServer(
        port=port_number)
    _server.run()

if __name__ == "__main__":
    main()
