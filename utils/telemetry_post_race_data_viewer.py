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


from typing import Dict
from http import HTTPStatus
import logging
import json
from threading import Lock, Thread
import sys
import os
import tkinter as tk
from tkinter import filedialog
import subprocess
import time
import webbrowser

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.f1_types import F1Utils, LapData, ResultStatus

try:
    from flask import Flask, render_template, request, jsonify
except ImportError:
    print("Flask is not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip3", "install", "flask"])
    print("Flask installation complete.")
    from flask import Flask, render_template, request, jsonify
try:
    from flask_cors import CORS
except ImportError:
    print("flask-cors is not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip3", "install", "flask-cors"])
    print("flask-cors installation complete.")
    from flask_cors import CORS

g_json_data = {}
g_json_lock = Lock()
ui_initialized = False  # Flag to track if UI has been initialized

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

    # Init the global data onto the JSON repsonse
    with g_json_lock:
        if not g_json_data:
            return {}
        json_response = {
            "circuit": g_json_data["session-info"]["track-id"],
            "track-temperature": g_json_data["session-info"]["track-temperature"],
            "event-type": g_json_data["session-info"]["session-type"],
            "total-laps": g_json_data["session-info"]["total-laps"],
            "current-lap": g_json_data["classification-data"][0]["lap-data"]["current-lap-num"],
            "safety-car-status": g_json_data["session-info"]["safety-car-status"],
            "fastest-lap-overall": g_json_data["records"]["fastest"]["lap"]["time"],
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
                delta = "---"
            else:
                delta = F1Utils.millisecondsToSecondsMilliseconds(data_per_driver["lap-data"]["delta-to-race-leader-in-ms"])
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
            avg_tyre_wear = sum(data_per_driver["car-damage"]["tyres-wear"])/len(data_per_driver["car-damage"]["tyres-wear"])

            json_response["table-entries"].append(
                {
                    "position": position,
                    "name": data_per_driver["driver-name"],
                    "team": data_per_driver["participant-data"]["team-id"],
                    "delta": getDeltaPlusPenaltiesPlusPit(delta, penalties, is_pitting, dnf_status_code),
                    "ers": F1Utils.floatToStr(ers_perc) + '%',
                    "best": data_per_driver["final-classification"]["best-lap-time-str"],
                    "last": data_per_driver["session-history"]["lap-history-data"][-1]["lap-time-str"],
                    "is-fastest": is_fastest,
                    "is-player": data_per_driver["is-player"],
                    "average-tyre-wear": F1Utils.floatToStr(avg_tyre_wear) + "%",
                    "tyre-age": data_per_driver["car-status"]["tyres-age-laps"],
                    "tyre-life-remaining" : "---",
                    "tyre-compound": data_per_driver["car-status"]["actual-tyre-compound"] + ' - ' + data_per_driver["car-status"]["visual-tyre-compound"],
                    "drs": False,
                    "num-pitstops": data_per_driver["final-classification"]["num-pit-stops"],
                    "dnf-status" : dnf_status_code,
                    "index" : index,
                    "telemetry-setting" : data_per_driver["participant-data"]["telemetry-setting"], # Already NULL checked
                    "lap-progress" : None # NULL is supported
                }
            )

        return json_response

def getDriverInfoJsonByIndex(index):

    with g_json_lock:
        final_json = {}
        global g_json_data
        if not g_json_data:
            return final_json

        # Add the primary data
        final_json["index"] = index
        driver_data = g_json_data["classification-data"][index]

        final_json["is-player"] = driver_data["is-player"]
        final_json["driver-name"] = driver_data["driver-name"]
        final_json["track-position"] = driver_data["final-classification"]["position"]
        final_json["telemetry-settings"] = driver_data["participant-data"]["telemetry-setting"]
        final_json["car-damage"] = driver_data["car-damage"]
        final_json["car-status"] = driver_data["car-status"]
        final_json["session-history"] = driver_data["session-history"]
        final_json["final-classification"] = driver_data["final-classification"]
        final_json["lap-data"] = driver_data["lap-data"]

        final_json["participant-data"] = driver_data["participant-data"]
        final_json["tyre-sets"] = driver_data["tyre-sets"]

        # Insert the tyre set history
        final_json["tyre-set-history"]= driver_data["tyre-set-history"]

        # Insert the per lap backup
        final_json["per-lap-info"] = driver_data["per-lap-info"]

        # Return this fully prepped JSON
        return final_json

class TelemetryWebServer:
    def __init__(self,
        port: int,
        packet_capture_enabled: bool,
        client_poll_interval_ms: int,
        debug_mode: bool,
        num_adjacent_cars: int):
        """
        Initialize TelemetryServer.

        Args:
            port (int): Port number for the server.
            packet_capture (bool) - True if packet capture is enabled
            client_refresh_interval_ms (int) - The interval at which the client is to poll the server for data
            debug_mode (bool): Enable debug mode.
            num_adjacent_cars (int): The number of cars adjacent to player to be included in telemetry-info response
        """
        self.m_app = Flask(__name__, template_folder='../src/templates')
        self.m_app.config['PROPAGATE_EXCEPTIONS'] = True
        self.m_app.config["EXPLAIN_TEMPLATE_LOADING"] = True
        self.m_port = port
        self.m_debug_mode = debug_mode
        self.m_packet_capture_enabled = packet_capture_enabled
        self.m_client_poll_interval_ms = client_poll_interval_ms
        self.m_num_adjacent_cars = num_adjacent_cars

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
                packet_capture_enabled=self.m_packet_capture_enabled,
                client_poll_interval_ms=self.m_client_poll_interval_ms)

        # Define your endpoint
        @self.m_app.route('/telemetry-info')
        def telemetryInfo() -> Dict:
            """
            Endpoint for telemetry information.

            Returns:
                str: Telemetry data in JSON format.
            """
            return getTelemetryInfo()

        @self.m_app.route('/driver-info', methods=['GET'])
        def driverInfo() -> Dict:
            """
            Endpoint for saving telemetry packet capture.

            Returns:
                str: JSON response indicating success or failure.
            """
            # Access parameters using request.args
            index = request.args.get('index')

            # Check if only one parameter is provided
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
                return jsonify(error_response), HTTPStatus.BAD_REQUEST

            # Process parameters and generate response
            index = int(index)
            driver_info = getDriverInfoJsonByIndex(index)
            if driver_info:
                return jsonify(driver_info), HTTPStatus.OK
            else:
                error_response = {
                    'error' : 'Invalid parameter value',
                    'message' : 'Invalid index'
                }
                return jsonify(error_response), HTTPStatus.BAD_REQUEST

    def run(self):
        """
        Run the TelemetryServer.
        """

        # Disable Werkzeug request logging
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)

        self.m_app.run(
            debug=self.m_debug_mode,
            port=self.m_port,
            threaded=False,
            use_reloader=False,
            host='0.0.0.0')

def open_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        status_label.config(text=f"Selected file: {file_path}")
        f = open(file_path)
        global g_json_lock
        global g_json_data
        with g_json_lock:
            g_json_data = json.load(f)
        f.close()
    else:
        status_label.config(text="No file selected")

def start_ui():
    global ui_initialized
    if not ui_initialized:
        ui_initialized = True  # Set flag to True
        # Create the main window
        print("UI thread")
        root = tk.Tk()
        root.title("F1 2023 Post race analyzer")

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
        root.mainloop()

def openWebPage() -> None:
    """Open the webpage on a new browser tab.

    """
    time.sleep(1)
    webbrowser.open('http://localhost:5000', new=2)

def main():
    # Start Tkinter UI
    ui_thread = Thread(target=start_ui)
    ui_thread.start()

    # Open the webpage
    webpage_thread = Thread(target=openWebPage)
    webpage_thread.start()

    # Start Flask server after Tkinter UI is initialized
    server = TelemetryWebServer(
        port=5000,
        packet_capture_enabled=False,
        client_poll_interval_ms=200,
        debug_mode=True,
        num_adjacent_cars=20)
    server.run()



if __name__ == "__main__":
    main()
