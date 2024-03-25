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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Dict
from http import HTTPStatus
import logging

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

from src.telemetry_handler import dumpPktCapToFile, getOvertakeJSON, GetOvertakesStatus
import src.telemetry_data as TelData

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

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
        self.m_app = Flask(__name__, template_folder='templates')
        self.m_app.config['PROPAGATE_EXCEPTIONS'] = True
        self.m_port = port
        self.m_debug_mode = debug_mode
        self.m_packet_capture_enabled = packet_capture_enabled
        self.m_client_poll_interval_ms = client_poll_interval_ms
        self.m_num_adjacent_cars = num_adjacent_cars

        # Define your endpoint
        @self.m_app.route('/telemetry-info')
        def telemetryInfo() -> Dict:
            """
            Endpoint for telemetry information.

            Returns:
                str: Telemetry data in JSON format.
            """
            # return self.sampleTelemetryInfoRsp() # TODO - remove
            return self.getRaceTelemetryInfo()

        # Define your endpoint
        @self.m_app.route('/overtake-info')
        def overtakeInfo() -> Dict:
            """
            Endpoint for overtake information.

            Returns:
                str: Overtake data in JSON format.
            """
            overtake_info = self.getOvertakeInfo()
            return overtake_info

        @self.m_app.route('/save-telemetry-capture')
        def saveTelemetryCapture() -> Dict:
            """
            Endpoint for saving telemetry packet capture.

            Returns:
                str: JSON response indicating success or failure.
            """
            return self.saveTelemetryData()

        @self.m_app.route('/driver-info', methods=['GET'])
        def driverInfo() -> Dict:
            """
            Endpoint for saving telemetry packet capture.

            Returns:
                str: JSON response indicating success or failure.
            """
            # Access parameters using request.args
            index = request.args.get('index')

            # TODO - remove
            # return self.sampleDriverInfoRsp()

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
            driver_info = TelData.getDriverInfoJsonByIndex(index)
            if driver_info:
                # return jsonify(driver_info), HTTPStatus.OK
                status, overtakes_info = getOvertakeJSON(driver_info["driver-name"])
                driver_info["overtakes-status-code"] = str(status)
                driver_info['overtakes'] = overtakes_info
                if status != GetOvertakesStatus.INVALID_INDEX:
                    return jsonify(driver_info), HTTPStatus.OK
                else:
                    return jsonify(driver_info), HTTPStatus.BAD_REQUEST
            else:
                error_response = {
                    'error' : 'Invalid parameter value',
                    'message' : 'Invalid index'
                }
                return jsonify(error_response), HTTPStatus.BAD_REQUEST

        # Render the HTML page
        @self.m_app.route('/')
        def index():
            """
            Endpoint for the index page.

            Returns:
                str: HTML page content.
            """

            return render_template('index.html',
                packet_capture_enabled=self.m_packet_capture_enabled,
                client_poll_interval_ms=self.m_client_poll_interval_ms)

    def getValueOrDefaultValue(self,
            value: str,
            default_value: str ='---') -> str:
        """
        Get value or default as string.

        Args:
            value: The value to check.
            default_value (str, optional): Default value if the input is None. Defaults to '---'.

        Returns:
            str: The value as string or default string.
        """
        return value if value is not None else default_value

    def getRaceTelemetryInfo(self) -> Dict:
        """
        Get telemetry data in JSON format.

        Returns:
            Dict: Telemetry data in JSON format.
        """

        # Fetch the data from the data stores
        driver_data, fastest_lap_overall = TelData.getDriverData(self.m_num_adjacent_cars)
        circuit, track_temp, event_type, total_laps, curr_lap, \
            safety_car_status, weather_forecast_samples, pit_speed_limit, \
                    final_classification_received = TelData.getGlobals()

        # Init the global data onto the JSON repsonse
        json_response = {
            "circuit": self.getValueOrDefaultValue(circuit),
            "track-temperature": self.getValueOrDefaultValue(track_temp),
            "event-type": self.getValueOrDefaultValue(event_type),
            "total-laps": self.getValueOrDefaultValue(total_laps),
            "current-lap": self.getValueOrDefaultValue(curr_lap),
            "safety-car-status": str(self.getValueOrDefaultValue(safety_car_status, default_value="")),
            "fastest-lap-overall": fastest_lap_overall,
            "pit-speed-limit" : self.getValueOrDefaultValue(pit_speed_limit),
            "weather-forecast-samples": [],
            "race-ended" : self.getValueOrDefaultValue(final_classification_received, False)
        }
        for sample in weather_forecast_samples:
            json_response["weather-forecast-samples"].append(
                {
                    "time-offset": str(sample.m_timeOffset),
                    "weather": str(sample.m_weather),
                    "rain-probability": str(sample.m_rainPercentage)
                }
            )

        # Fill in the per driver data
        json_response["table-entries"] = []
        fastest_lap_overall = "---"
        for data_per_driver in driver_data:
            if data_per_driver.m_is_fastest:
                fastest_lap_overall = data_per_driver.m_best_lap
            json_response["table-entries"].append(
                {
                    "position": self.getValueOrDefaultValue(data_per_driver.m_position),
                    "name": self.getValueOrDefaultValue(data_per_driver.m_name),
                    "team": self.getValueOrDefaultValue(data_per_driver.m_team),
                    "delta": self.getDeltaPlusPenaltiesPlusPit(data_per_driver.m_delta,
                                                               data_per_driver.m_penalties,
                                                               data_per_driver.m_is_pitting,
                                                               data_per_driver.m_dnf_status_code),
                    "ers": self.getValueOrDefaultValue(data_per_driver.m_ers_perc),
                    "best": self.getValueOrDefaultValue(data_per_driver.m_best_lap),
                    "last": self.getValueOrDefaultValue(data_per_driver.m_last_lap),
                    "is-fastest": self.getValueOrDefaultValue(data_per_driver.m_is_fastest),
                    "is-player": self.getValueOrDefaultValue(data_per_driver.m_is_player),
                    "average-tyre-wear": self.getValueOrDefaultValue(data_per_driver.m_tyre_wear),
                    "tyre-age": self.getValueOrDefaultValue(data_per_driver.m_tyre_age),
                    "tyre-life-remaining" : self.getValueOrDefaultValue(data_per_driver.m_tyre_life_remaining_laps),
                    "tyre-compound": self.getValueOrDefaultValue(data_per_driver.m_tyre_compound_type),
                    "drs": self.getDRSValue(data_per_driver.m_drs_activated, data_per_driver.m_drs_allowed),
                    "num-pitstops": self.getValueOrDefaultValue(data_per_driver.m_num_pitstops),
                    "dnf-status" : self.getValueOrDefaultValue(data_per_driver.m_dnf_status_code),
                    "index" : self.getValueOrDefaultValue(data_per_driver.m_index),
                    "telemetry-setting" : data_per_driver.m_telemetry_restrictions, # Already NULL checked
                    "lap-progress" : data_per_driver.m_lap_progress # NULL is supported
                }
            )

        return json_response

    def saveTelemetryData(self) -> Dict:
        """Save the raw telemetry data to a file.

        Returns:
            Dict: The Dict containing the JSON response
        """

        status_code, file_name, num_packets, num_bytes = dumpPktCapToFile(clear_db=True, reason='Received Request')
        return {
            "is-success" : (True if file_name else False),
            "status-code" : str(status_code),
            "file-name" : self.getValueOrDefaultValue(file_name, ""),
            "num-packets" : self.getValueOrDefaultValue(num_packets, default_value=0),
            "num-bytes" : self.getValueOrDefaultValue(num_bytes, default_value=0)
        }

    def getOvertakeInfo(self) -> Dict:
        """Get the overtake information

        Returns:
            Dict: Dict containing overtake Info in JSON format
        """

        status, overtake_info = getOvertakeJSON()
        overtake_info["status-code"] = str(status)
        return overtake_info

    def getDeltaPlusPenaltiesPlusPit(self,
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

    def getDRSValue(self,
            drs_activated: bool,
            drs_available: bool) -> bool:
        """
        Get DRS value.

        Args:
            drs_activated (bool): Whether DRS is activated.
            drs_available (bool): Whether DRS is available.

        Returns:
            bool: True if DRS is activated or available or has non-zero distance, False otherwise.
        """
        # return True if (drs_activated or drs_available or (drs_distance > 0)) else False
        return True if (drs_activated or drs_available) else False

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
            threaded=True,
            use_reloader=self.m_debug_mode,
            host='0.0.0.0')

    # TODO: remove
    def sampleTelemetryInfoRsp(self):

        return {
            "circuit": "Shanghai",
            "current-lap": 5,
            "event-type": "Race",
            "fastest-lap-overall": "01:34.809",
            "pit-speed-limit": 80,
            "race-ended": True,
            "safety-car-status": "",
            "table-entries": [
                {
                    "average-tyre-wear": "11.58%",
                    "best": "01:35.242",
                    "delta": "-2.678 ",
                    "dnf-status": "",
                    "drs": False,
                    "ers": "8.24%",
                    "index": 5,
                    "is-fastest": False,
                    "is-player": False,
                    "lap-progress": 3.505215034001103,
                    "last": "01:35.520",
                    "name": "RUSSELL",
                    "num-pitstops": 0,
                    "position": 1,
                    "team": "Mercedes",
                    "telemetry-setting": "Public",
                    "tyre-age": 5,
                    "tyre-compound": "C4 - Soft",
                    "tyre-life-remaining": 22
                },
                {
                    "average-tyre-wear": "11.56%",
                    "best": "01:35.124",
                    "delta": "-1.932 ",
                    "dnf-status": "",
                    "drs": True,
                    "ers": "8.37%",
                    "index": 17,
                    "is-fastest": False,
                    "is-player": False,
                    "lap-progress": 2.6308855793971695,
                    "last": "01:35.722",
                    "name": "PIASTRI",
                    "num-pitstops": 0,
                    "position": 2,
                    "team": "McLaren",
                    "telemetry-setting": "Public",
                    "tyre-age": 5,
                    "tyre-compound": "C4 - Soft",
                    "tyre-life-remaining": 22
                },
                {
                    "average-tyre-wear": "11.65%",
                    "best": "01:35.257",
                    "delta": "-1.540 ",
                    "dnf-status": "",
                    "drs": True,
                    "ers": "7.94%",
                    "index": 3,
                    "is-fastest": False,
                    "is-player": False,
                    "lap-progress": 2.1194331809410034,
                    "last": "01:35.260",
                    "name": "P\u00c9REZ",
                    "num-pitstops": 0,
                    "position": 3,
                    "team": "Red Bull Racing",
                    "telemetry-setting": "Public",
                    "tyre-age": 5,
                    "tyre-compound": "C4 - Soft",
                    "tyre-life-remaining": 22
                },
                {
                    "average-tyre-wear": "11.69%",
                    "best": "01:35.087",
                    "delta": "-1.099 ",
                    "dnf-status": "",
                    "drs": True,
                    "ers": "8.11%",
                    "index": 8,
                    "is-fastest": False,
                    "is-player": False,
                    "lap-progress": 1.5196396572321265,
                    "last": "01:35.087",
                    "name": "HAMILTON",
                    "num-pitstops": 0,
                    "position": 4,
                    "team": "Mercedes",
                    "telemetry-setting": "Public",
                    "tyre-age": 5,
                    "tyre-compound": "C4 - Soft",
                    "tyre-life-remaining": 21
                },
                {
                    "average-tyre-wear": "12.89%",
                    "best": "01:34.809",
                    "delta": "--- ",
                    "dnf-status": "",
                    "drs": True,
                    "ers": "5.68%",
                    "index": 19,
                    "is-fastest": True,
                    "is-player": True,
                    "lap-progress": 0.005815222385590884,
                    "last": "01:35.200",
#                     "name": "VERSTAPPEN",
#                     "num-pitstops": 0,
#                     "position": 5,
#                     "team": "Red Bull Racing",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 21
#                 },
#                 {
#                     "average-tyre-wear": "12.08%",
#                     "best": "01:35.161",
#                     "delta": "+1.850 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "9.20%",
#                     "index": 7,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 97.64350676575997,
#                     "last": "01:35.433",
#                     "name": "LECLERC",
#                     "num-pitstops": 0,
#                     "position": 6,
#                     "team": "Ferrari",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 21
#                 },
#                 {
#                     "average-tyre-wear": "11.42%",
#                     "best": "01:35.715",
#                     "delta": "+2.850 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "8.79%",
#                     "index": 13,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 96.53269160080868,
#                     "last": "01:36.506",
#                     "name": "STROLL",
#                     "num-pitstops": 0,
#                     "position": 7,
#                     "team": "Aston Martin",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "11.64%",
#                     "best": "01:35.375",
#                     "delta": "+3.167 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "10.15%",
#                     "index": 12,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 96.17616821356368,
#                     "last": "01:35.557",
#                     "name": "NORRIS",
#                     "num-pitstops": 0,
#                     "position": 8,
#                     "team": "McLaren",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "11.60%",
#                     "best": "01:35.232",
#                     "delta": "+3.483 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "9.85%",
#                     "index": 4,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 95.87880215034002,
#                     "last": "01:35.298",
#                     "name": "ALONSO",
#                     "num-pitstops": 0,
#                     "position": 9,
#                     "team": "Aston Martin",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "11.60%",
#                     "best": "01:35.323",
#                     "delta": "+3.966 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "10.44%",
#                     "index": 9,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 95.4556190842676,
#                     "last": "01:35.352",
#                     "name": "SAINZ",
#                     "num-pitstops": 0,
#                     "position": 10,
#                     "team": "Ferrari",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "11.19%",
#                     "best": "01:35.517",
#                     "delta": "+4.883 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "10.27%",
#                     "index": 10,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 94.60591458371623,
#                     "last": "01:35.605",
#                     "name": "MAGNUSSEN",
#                     "num-pitstops": 0,
#                     "position": 11,
#                     "team": "Haas",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "11.08%",
#                     "best": "01:35.432",
#                     "delta": "+5.600 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "9.18%",
#                     "index": 11,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 93.8843962506892,
#                     "last": "01:35.432",
#                     "name": "HULKENBERG",
#                     "num-pitstops": 0,
#                     "position": 12,
#                     "team": "Haas",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "10.97%",
#                     "best": "01:35.455",
#                     "delta": "+6.117 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "9.18%",
#                     "index": 18,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 93.22314803115236,
#                     "last": "01:35.558",
#                     "name": "OCON",
#                     "num-pitstops": 0,
#                     "position": 13,
#                     "team": "Alpine",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "11.26%",
#                     "best": "01:35.489",
#                     "delta": "+6.667 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "9.69%",
#                     "index": 16,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 92.54377211220364,
#                     "last": "01:35.596",
#                     "name": "ALBON",
#                     "num-pitstops": 0,
#                     "position": 14,
#                     "team": "Williams",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "10.97%",
#                     "best": "01:35.682",
#                     "delta": "+8.034 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "11.87%",
#                     "index": 2,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 90.98299514105864,
#                     "last": "01:35.682",
#                     "name": "BOTTAS",
#                     "num-pitstops": 0,
#                     "position": 15,
#                     "team": "Alfa Romeo",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "11.05%",
#                     "best": "01:35.230",
#                     "delta": "+8.501 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "13.11%",
#                     "index": 15,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 90.53353588494763,
#                     "last": "01:35.983",
#                     "name": "ZHOU",
#                     "num-pitstops": 0,
#                     "position": 16,
#                     "team": "Alfa Romeo",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "10.91%",
#                     "best": "01:35.893",
#                     "delta": "+9.201 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "14.10%",
#                     "index": 14,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 89.90811230702077,
#                     "last": "01:35.893",
#                     "name": "SARGEANT",
#                     "num-pitstops": 0,
#                     "position": 17,
#                     "team": "Williams",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "10.99%",
#                     "best": "01:35.770",
#                     "delta": "+9.618 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "13.60%",
#                     "index": 0,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 89.63788394826318,
#                     "last": "01:36.003",
#                     "name": "RICCIARDO",
#                     "num-pitstops": 0,
#                     "position": 18,
#                     "team": "Alpha Tauri",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "11.10%",
#                     "best": "01:35.670",
#                     "delta": "+10.101 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "14.43%",
#                     "index": 1,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 89.32985664399926,
#                     "last": "01:36.116",
#                     "name": "GASLY",
#                     "num-pitstops": 0,
#                     "position": 19,
#                     "team": "Alpine",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 },
#                 {
#                     "average-tyre-wear": "10.90%",
#                     "best": "01:35.653",
#                     "delta": "+10.634 ",
#                     "dnf-status": "",
#                     "drs": False,
#                     "ers": "14.43%",
#                     "index": 6,
#                     "is-fastest": False,
#                     "is-player": False,
#                     "lap-progress": 89.03022910540341,
#                     "last": "01:36.151",
#                     "name": "TSUNODA",
#                     "num-pitstops": 0,
#                     "position": 20,
#                     "team": "Alpha Tauri",
#                     "telemetry-setting": "Public",
#                     "tyre-age": 4,
#                     "tyre-compound": "C4 - Soft",
#                     "tyre-life-remaining": 22
#                 }
#             ],
#             "total-laps": 5,
#             "track-temperature": 28,
#             "weather-forecast-samples": [
#                 {
#                     "rain-probability": "24",
#                     "time-offset": "0",
#                     "weather": "Overcast"
#                 },
#                 {
#                     "rain-probability": "24",
#                     "time-offset": "5",
#                     "weather": "Overcast"
#                 },
#                 {
#                     "rain-probability": "24",
#                     "time-offset": "10",
#                     "weather": "Overcast"
#                 }
#             ]
#         }

#     # TODO: remove
#     def sampleDriverInfoRsp(self):

#         return {
#             "car-damage": {
#             "brakes-damage": [
#                 0,
#                 0,
#                 0,
#                 0
#             ],
#             "diffuser-damage": 0,
#             "drs-fault": False,
#             "engine-blown": False,
#             "engine-ce-wear": 1,
#             "engine-damage": 4,
#             "engine-es-wear": 1,
#             "engine-ice-wear": 4,
#             "engine-mguh-wear": 3,
#             "engine-mguk-wear": 1,
#             "engine-seized": False,
#             "engine-tc-wear": 2,
#             "ers-fault": False,
#             "floor-damage": 0,
#             "front-left-wing-damage": 0,
#             "front-right-wing-damage": 0,
#             "gear-box-damage": 4,
#             "rear-wing-damage": 0,
#             "sidepod-damage": 0,
#             "tyres-damage": [
#                 13,
#                 12,
#                 13,
#                 12
#             ],
#             "tyres-wear": [
#                 13.403026580810547,
#                 12.56920051574707,
#                 13.130508422851562,
#                 12.452241897583008
#             ]
#             },
#             "car-status": {
#             "actual-tyre-compound": "C4",
#             "anti-lock-brakes": 0,
#             "drs-activation-distance": 0,
#             "drs-allowed": 0,
#             "engine-power-ice": 598267.5625,
#             "engine-power-mguk": 51289.734375,
#             "ers-deploy-mode": "Overtake",
#             "ers-deployed-this-lap": 1937890.5,
#             "ers-harvested-this-lap-mguh": 934289,
#             "ers-harvested-this-lap-mguk": 407664.9375,
#             "ers-max-capacity": 4000000,
#             "ers-store-energy": 227027.15625,
#             "front-brake-bias": 58,
#             "fuel-capacity": 110,
#             "fuel-in-tank": 2.25842022895813,
#             "fuel-mix": 1,
#             "fuel-remaining-laps": 1.2396146059036255,
#             "idle-rpm": 3499,
#             "max-gears": 9,
#             "max-rpm": 13000,
#             "network-paused": 0,
#             "pit-limiter-status": 0,
#             "traction-control": 0,
#             "tyres-age-laps": 4,
#             "vehicle-fia-flags": "None",
#             "visual-tyre-compound": "Soft"
#             },
#             "driver-name": "VERSTAPPEN",
#             "final-classification": {
#             "best-lap-time-ms": 94809,
#             "best-lap-time-str": "01:34.809",
#             "grid-position": 6,
#             "num-laps": 5,
#             "num-penalties": 0,
#             "num-pit-stops": 0,
#             "num-tyre-stints": 1,
#             "penalties-time": 0,
#             "points": 11,
#             "position": 5,
#             "result-status": "FINISHED",
#             "total-race-time": 481.0958251953125,
#             "total-race-time-str": "08:01.095",
#             "tyre-stints-actual": [
#                 17
#             ],
#             "tyre-stints-end-laps": [
#                 255
#             ],
#             "tyre-stints-visual": [
#                 16
#             ]
#             },
#             "index": 19,
#             "is-player": True,
#             "lap-data": {
#             "car-position": 5,
#             "corner-cutting-warnings": 0,
#             "current-lap-invalid": False,
#             "current-lap-num": 5,
#             "current-lap-time-in-ms": 16,
#             "current-lap-time-str": "00:00.016",
#             "delta-to-car-in-front-in-ms": 1099,
#             "delta-to-race-leader-in-ms": 2678,
#             "driver-status": "ON_TRACK",
#             "grid-position": 6,
#             "lap-distance": 0.31640625,
#             "last-lap-time-in-ms": 95200,
#             "last-lap-time-str": "01:35.200",
#             "num-pit-stops": 0,
#             "num-unserved-drive-through-pens": 0,
#             "num-unserved-stop-go-pens": 0,
#             "penalties": 0,
#             "pit-lane-time-in-lane-in-ms": 0,
#             "pit-lane-timer-active": False,
#             "pit-status": "0",
#             "pit-stop-should-serve-pen": 0,
#             "pit-stop-timer-in-ms": 0,
#             "result-status": "FINISHED",
#             "safety-car-delta": 0,
#             "sector": "0",
#             "sector-1-time-in-ms": 0,
#             "sector-1-time-minutes": 0,
#             "sector-1-time-str": "00.000",
#             "sector-2-time-in-ms": 0,
#             "sector-2-time-minutes": 0,
#             "sector-2-time-str": "00.000",
#             "total-distance": 27208.671875,
#             "total-warnings": 0
#             },
#             "overtakes": {
#             "number-of-overtakes": 3,
#             "number-of-times-overtaken": 3,
#             "player-most-heated-rivalries": [
#                 {
#                 "driver1": "HAMILTON",
#                 "driver2": "VERSTAPPEN",
#                 "overtakes": [
#                     {
#                     "overtaken-driver-lap": 1,
#                     "overtaken-driver-name": "VERSTAPPEN",
#                     "overtaking-driver-lap": 1,
#                     "overtaking-driver-name": "HAMILTON"
#                     },
#                     {
#                     "overtaken-driver-lap": 1,
#                     "overtaken-driver-name": "HAMILTON",
#                     "overtaking-driver-lap": 1,
#                     "overtaking-driver-name": "VERSTAPPEN"
#                     },
#                     {
#                     "overtaken-driver-lap": 1,
#                     "overtaken-driver-name": "VERSTAPPEN",
#                     "overtaking-driver-lap": 1,
#                     "overtaking-driver-name": "HAMILTON"
#                     }
#                 ]
#                 }
#             ],
#             "player-name": "VERSTAPPEN"
#             },
#             "overtakes-status-code": "RACE_COMPLETED",
#             "participant-data": {
#             "ai-controlled": False,
#             "driver-id": 9,
#             "my-team": False,
#             "name": "VERSTAPPEN",
#             "nationality": "Dutch",
#             "network-id": 255,
#             "platform": "Steam",
#             "race-number": 33,
#             "show-online-names": True,
#             "team-id": "Red Bull Racing",
#             "telemetry-setting": "Public"
#             },
#             "per-lap-info": [
#             {
#                 "car-damage-data": {
#                 "brakes-damage": [
#                     0,
#                     0,
#                     0,
#                     0
#                 ],
#                 "diffuser-damage": 0,
#                 "drs-fault": False,
#                 "engine-blown": False,
#                 "engine-ce-wear": 0,
#                 "engine-damage": 0,
#                 "engine-es-wear": 0,
#                 "engine-ice-wear": 0,
#                 "engine-mguh-wear": 0,
#                 "engine-mguk-wear": 0,
#                 "engine-seized": False,
#                 "engine-tc-wear": 0,
#                 "ers-fault": False,
#                 "floor-damage": 0,
#                 "front-left-wing-damage": 0,
#                 "front-right-wing-damage": 0,
#                 "gear-box-damage": 0,
#                 "rear-wing-damage": 0,
#                 "sidepod-damage": 0,
#                 "tyres-damage": [
#                     0,
#                     0,
#                     0,
#                     0
#                 ],
#                 "tyres-wear": [
#                     0,
#                     0,
#                     0,
#                     0
#                 ]
#                 },
#                 "car-status-data": {
#                 "actual-tyre-compound": "C4",
#                 "anti-lock-brakes": 0,
#                 "drs-activation-distance": 0,
#                 "drs-allowed": 0,
#                 "engine-power-ice": 93480.734375,
#                 "engine-power-mguk": 0,
#                 "ers-deploy-mode": "Medium",
#                 "ers-deployed-this-lap": 0,
#                 "ers-harvested-this-lap-mguh": 0,
#                 "ers-harvested-this-lap-mguk": 0,
#                 "ers-max-capacity": 4000000,
#                 "ers-store-energy": 4000000,
#                 "front-brake-bias": 58,
#                 "fuel-capacity": 110,
#                 "fuel-in-tank": 11.399999618530273,
#                 "fuel-mix": 1,
#                 "fuel-remaining-laps": 1.519197940826416,
#                 "idle-rpm": 3499,
#                 "max-gears": 9,
#                 "max-rpm": 13000,
#                 "network-paused": 0,
#                 "pit-limiter-status": 0,
#                 "traction-control": 0,
#                 "tyres-age-laps": 0,
#                 "vehicle-fia-flags": "None",
#                 "visual-tyre-compound": "Soft"
#                 },
#                 "lap-number": 0
#             },
#             {
#                 "car-damage-data": {
#                 "brakes-damage": [
#                     0,
#                     0,
#                     0,
#                     0
#                 ],
#                 "diffuser-damage": 0,
#                 "drs-fault": False,
#                 "engine-blown": False,
#                 "engine-ce-wear": 0,
#                 "engine-damage": 0,
#                 "engine-es-wear": 0,
#                 "engine-ice-wear": 1,
#                 "engine-mguh-wear": 1,
#                 "engine-mguk-wear": 0,
#                 "engine-seized": False,
#                 "engine-tc-wear": 0,
#                 "ers-fault": False,
#                 "floor-damage": 0,
#                 "front-left-wing-damage": 0,
#                 "front-right-wing-damage": 0,
#                 "gear-box-damage": 0,
#                 "rear-wing-damage": 0,
#                 "sidepod-damage": 0,
#                 "tyres-damage": [
#                     3,
#                     2,
#                     2,
#                     2
#                 ],
#                 "tyres-wear": [
#                     3.420997142791748,
#                     2.82375431060791,
#                     2.401949167251587,
#                     2.276975154876709
#                 ]
#                 },
#                 "car-status-data": {
#                 "actual-tyre-compound": "C4",
#                 "anti-lock-brakes": 0,
#                 "drs-activation-distance": 0,
#                 "drs-allowed": 0,
#                 "engine-power-ice": 594975.0625,
#                 "engine-power-mguk": 125984.2578125,
#                 "ers-deploy-mode": "Overtake",
#                 "ers-deployed-this-lap": 2852094.25,
#                 "ers-harvested-this-lap-mguh": 899012.5625,
#                 "ers-harvested-this-lap-mguk": 442197,
#                 "ers-max-capacity": 4000000,
#                 "ers-store-energy": 2468493,
#                 "front-brake-bias": 58,
#                 "fuel-capacity": 110,
#                 "fuel-in-tank": 9.507476806640625,
#                 "fuel-mix": 1,
#                 "fuel-remaining-laps": 1.4057269096374512,
#                 "idle-rpm": 3499,
#                 "max-gears": 9,
#                 "max-rpm": 13000,
#                 "network-paused": 0,
#                 "pit-limiter-status": 0,
#                 "traction-control": 0,
#                 "tyres-age-laps": 0,
#                 "vehicle-fia-flags": "None",
#                 "visual-tyre-compound": "Soft"
#                 },
#                 "lap-number": 1
#             },
#             {
#                 "car-damage-data": {
#                 "brakes-damage": [
#                     0,
#                     0,
#                     0,
#                     0
#                 ],
#                 "diffuser-damage": 0,
#                 "drs-fault": False,
#                 "engine-blown": False,
#                 "engine-ce-wear": 0,
#                 "engine-damage": 1,
#                 "engine-es-wear": 1,
#                 "engine-ice-wear": 2,
#                 "engine-mguh-wear": 1,
#                 "engine-mguk-wear": 1,
#                 "engine-seized": False,
#                 "engine-tc-wear": 1,
#                 "ers-fault": False,
#                 "floor-damage": 0,
#                 "front-left-wing-damage": 0,
#                 "front-right-wing-damage": 0,
#                 "gear-box-damage": 1,
#                 "rear-wing-damage": 0,
#                 "sidepod-damage": 0,
#                 "tyres-damage": [
#                     5,
#                     5,
#                     5,
#                     4
#                 ],
#                 "tyres-wear": [
#                     5.891158580780029,
#                     5.243369102478027,
#                     5.029486656188965,
#                     4.771495819091797
#                 ]
#                 },
#                 "car-status-data": {
#                 "actual-tyre-compound": "C4",
#                 "anti-lock-brakes": 0,
#                 "drs-activation-distance": 0,
#                 "drs-allowed": 0,
#                 "engine-power-ice": 602306.8125,
#                 "engine-power-mguk": 18897.63671875,
#                 "ers-deploy-mode": "Medium",
#                 "ers-deployed-this-lap": 2042874.75,
#                 "ers-harvested-this-lap-mguh": 926144.1875,
#                 "ers-harvested-this-lap-mguk": 409947.1875,
#                 "ers-max-capacity": 4000000,
#                 "ers-store-energy": 1753259.875,
#                 "front-brake-bias": 58,
#                 "fuel-capacity": 110,
#                 "fuel-in-tank": 7.686369895935059,
#                 "fuel-mix": 1,
#                 "fuel-remaining-laps": 1.359694004058838,
#                 "idle-rpm": 3499,
#                 "max-gears": 9,
#                 "max-rpm": 13000,
#                 "network-paused": 0,
#                 "pit-limiter-status": 0,
#                 "traction-control": 0,
#                 "tyres-age-laps": 1,
#                 "vehicle-fia-flags": "None",
#                 "visual-tyre-compound": "Soft"
#                 },
#                 "lap-number": 2
#             },
#             {
#                 "car-damage-data": {
#                 "brakes-damage": [
#                     0,
#                     0,
#                     0,
#                     0
#                 ],
#                 "diffuser-damage": 0,
#                 "drs-fault": False,
#                 "engine-blown": False,
#                 "engine-ce-wear": 1,
#                 "engine-damage": 2,
#                 "engine-es-wear": 1,
#                 "engine-ice-wear": 2,
#                 "engine-mguh-wear": 2,
#                 "engine-mguk-wear": 1,
#                 "engine-seized": False,
#                 "engine-tc-wear": 1,
#                 "ers-fault": False,
#                 "floor-damage": 0,
#                 "front-left-wing-damage": 0,
#                 "front-right-wing-damage": 0,
#                 "gear-box-damage": 2,
#                 "rear-wing-damage": 0,
#                 "sidepod-damage": 0,
#                 "tyres-damage": [
#                     8,
#                     7,
#                     7,
#                     7
#                 ],
#                 "tyres-wear": [
#                     8.327430725097656,
#                     7.614562034606934,
#                     7.701445579528809,
#                     7.31258487701416
#                 ]
#                 },
#                 "car-status-data": {
#                 "actual-tyre-compound": "C4",
#                 "anti-lock-brakes": 0,
#                 "drs-activation-distance": 0,
#                 "drs-allowed": 0,
#                 "engine-power-ice": 602771,
#                 "engine-power-mguk": 18897.63671875,
#                 "ers-deploy-mode": "Medium",
#                 "ers-deployed-this-lap": 1875934.5,
#                 "ers-harvested-this-lap-mguh": 878170.75,
#                 "ers-harvested-this-lap-mguk": 424749.625,
#                 "ers-max-capacity": 4000000,
#                 "ers-store-energy": 1179881.375,
#                 "front-brake-bias": 58,
#                 "fuel-capacity": 110,
#                 "fuel-in-tank": 5.888923645019531,
#                 "fuel-mix": 1,
#                 "fuel-remaining-laps": 1.326936960220337,
#                 "idle-rpm": 3499,
#                 "max-gears": 9,
#                 "max-rpm": 13000,
#                 "network-paused": 0,
#                 "pit-limiter-status": 0,
#                 "traction-control": 0,
#                 "tyres-age-laps": 2,
#                 "vehicle-fia-flags": "None",
#                 "visual-tyre-compound": "Soft"
#                 },
#                 "lap-number": 3
#             },
#             {
#                 "car-damage-data": {
#                 "brakes-damage": [
#                     0,
#                     0,
#                     0,
#                     0
#                 ],
#                 "diffuser-damage": 0,
#                 "drs-fault": False,
#                 "engine-blown": False,
#                 "engine-ce-wear": 1,
#                 "engine-damage": 3,
#                 "engine-es-wear": 1,
#                 "engine-ice-wear": 3,
#                 "engine-mguh-wear": 2,
#                 "engine-mguk-wear": 1,
#                 "engine-seized": False,
#                 "engine-tc-wear": 2,
#                 "ers-fault": False,
#                 "floor-damage": 0,
#                 "front-left-wing-damage": 0,
#                 "front-right-wing-damage": 0,
#                 "gear-box-damage": 3,
#                 "rear-wing-damage": 0,
#                 "sidepod-damage": 0,
#                 "tyres-damage": [
#                     10,
#                     9,
#                     10,
#                     9
#                 ],
#                 "tyres-wear": [
#                     10.76635456085205,
#                     9.974536895751953,
#                     10.348953247070312,
#                     9.826332092285156
#                 ]
#                 },
#                 "car-status-data": {
#                 "actual-tyre-compound": "C4",
#                 "anti-lock-brakes": 0,
#                 "drs-activation-distance": 0,
#                 "drs-allowed": 0,
#                 "engine-power-ice": 590741.625,
#                 "engine-power-mguk": 18897.63671875,
#                 "ers-deploy-mode": "Medium",
#                 "ers-deployed-this-lap": 1665619,
#           "ers-harvested-this-lap-mguh": 841525.5,
#           "ers-harvested-this-lap-mguk": 468384.53125,
#           "ers-max-capacity": 4000000,
#           "ers-store-energy": 823858.8125,
#           "front-brake-bias": 58,
#           "fuel-capacity": 110,
#           "fuel-in-tank": 4.062103271484375,
#           "fuel-mix": 1,
#           "fuel-remaining-laps": 1.2764604091644287,
#           "idle-rpm": 3499,
#           "max-gears": 9,
#           "max-rpm": 13000,
#           "network-paused": 0,
#           "pit-limiter-status": 0,
#           "traction-control": 0,
#           "tyres-age-laps": 3,
#           "vehicle-fia-flags": "None",
#           "visual-tyre-compound": "Soft"
#         },
#         "lap-number": 4
#       },
#       {
#         "car-damage-data": {
#           "brakes-damage": [
#             0,
#             0,
#             0,
#             0
#           ],
#           "diffuser-damage": 0,
#           "drs-fault": False,
#           "engine-blown": False,
#           "engine-ce-wear": 1,
#           "engine-damage": 4,
#           "engine-es-wear": 1,
#           "engine-ice-wear": 4,
#           "engine-mguh-wear": 3,
#           "engine-mguk-wear": 1,
#           "engine-seized": False,
#           "engine-tc-wear": 2,
#           "ers-fault": False,
#           "floor-damage": 0,
#           "front-left-wing-damage": 0,
#           "front-right-wing-damage": 0,
#           "gear-box-damage": 4,
#           "rear-wing-damage": 0,
#           "sidepod-damage": 0,
#           "tyres-damage": [
#             13,
#             12,
#             13,
#             12
#           ],
#           "tyres-wear": [
#             13.403026580810547,
#             12.56920051574707,
#             13.130508422851562,
#             12.452241897583008
#           ]
#         },
#         "car-status-data": {
#           "actual-tyre-compound": "C4",
#           "anti-lock-brakes": 0,
#           "drs-activation-distance": 0,
#           "drs-allowed": 0,
#           "engine-power-ice": 598267.5625,
#           "engine-power-mguk": 51289.734375,
#           "ers-deploy-mode": "Overtake",
#           "ers-deployed-this-lap": 1937890.5,
#           "ers-harvested-this-lap-mguh": 934289,
#           "ers-harvested-this-lap-mguk": 407664.9375,
#           "ers-max-capacity": 4000000,
#           "ers-store-energy": 227027.15625,
#           "front-brake-bias": 58,
#           "fuel-capacity": 110,
#           "fuel-in-tank": 2.25842022895813,
#           "fuel-mix": 1,
#           "fuel-remaining-laps": 1.2396146059036255,
#           "idle-rpm": 3499,
#           "max-gears": 9,
#           "max-rpm": 13000,
#           "network-paused": 0,
#           "pit-limiter-status": 0,
#           "traction-control": 0,
#           "tyres-age-laps": 4,
#           "vehicle-fia-flags": "None",
#           "visual-tyre-compound": "Soft"
#         },
#         "lap-number": 5
#       }
#     ],
#     "session-history": {
#       "best-lap-time-lap-num": 4,
#       "best-sector-1-lap-num": 2,
#       "best-sector-2-lap-num": 4,
#       "best-sector-3-lap-num": 3,
#       "car-index": 19,
#       "lap-history-data": [
#         {
#           "lap-time-in-ms": 100514,
#           "lap-time-str": "01:40.514",
#           "lap-valid-bit-flags": 15,
#           "sector-1-time-in-ms": 28803,
#           "sector-1-time-minutes": 0,
#           "sector-1-time-str": "28.803",
#           "sector-2-time-in-ms": 29952,
#           "sector-2-time-minutes": 0,
#           "sector-2-time-str": "29.952",
#           "sector-3-time-in-ms": 41757,
#           "sector-3-time-minutes": 0,
#           "sector-3-time-str": "41.757"
#         },
#         {
#           "lap-time-in-ms": 95640,
#           "lap-time-str": "01:35.640",
#           "lap-valid-bit-flags": 15,
#           "sector-1-time-in-ms": 24654,
#           "sector-1-time-minutes": 0,
#           "sector-1-time-str": "24.654",
#           "sector-2-time-in-ms": 29043,
#           "sector-2-time-minutes": 0,
#           "sector-2-time-str": "29.043",
#           "sector-3-time-in-ms": 41942,
#           "sector-3-time-minutes": 0,
#           "sector-3-time-str": "41.942"
#         },
#         {
#           "lap-time-in-ms": 94931,
#           "lap-time-str": "01:34.931",
#           "lap-valid-bit-flags": 15,
#           "sector-1-time-in-ms": 24725,
#           "sector-1-time-minutes": 0,
#           "sector-1-time-str": "24.725",
#           "sector-2-time-in-ms": 28797,
#           "sector-2-time-minutes": 0,
#           "sector-2-time-str": "28.797",
#           "sector-3-time-in-ms": 41408,
#           "sector-3-time-minutes": 0,
#           "sector-3-time-str": "41.408"
#         },
#         {
#           "lap-time-in-ms": 94809,
#           "lap-time-str": "01:34.809",
#           "lap-valid-bit-flags": 15,
#           "sector-1-time-in-ms": 24833,
#           "sector-1-time-minutes": 0,
#           "sector-1-time-str": "24.833",
#           "sector-2-time-in-ms": 28319,
#           "sector-2-time-minutes": 0,
#           "sector-2-time-str": "28.319",
#           "sector-3-time-in-ms": 41657,
#           "sector-3-time-minutes": 0,
#           "sector-3-time-str": "41.657"
#         },
#         {
#           "lap-time-in-ms": 95200,
#           "lap-time-str": "01:35.200",
#           "lap-valid-bit-flags": 15,
#           "sector-1-time-in-ms": 24726,
#           "sector-1-time-minutes": 0,
#           "sector-1-time-str": "24.726",
#           "sector-2-time-in-ms": 28693,
#           "sector-2-time-minutes": 0,
#           "sector-2-time-str": "28.693",
#           "sector-3-time-in-ms": 41780,
#           "sector-3-time-minutes": 0,
#           "sector-3-time-str": "41.780"
#         }
#       ],
#       "num-laps": 5,
#       "num-tyre-stints": 1,
#       "tyre-stints-history-data": [
#         {
#           "end-lap": 255,
#           "tyre-actual-compound": "C4",
#           "tyre-visual-compound": "Soft"
#         }
#       ]
#     },
#     "telemetry-settings": "Public",
#     "track-position": 5,
#     "tyre-set-history": [
#       {
#         "end-lap": 5,
#         "fitted-index": 6,
#         "start-lap": 1,
#         "stint-length": 5,
#         "tyre-set-data": {
#           "actual-tyre-compound": "C4",
#           "available": True,
#           "fitted": True,
#           "lap-delta-time": 0,
#           "life-span": 21,
#           "recommended-session": 5,
#           "usable-life": 26,
#           "visual-tyre-compound": "Soft",
#           "wear": 12
#         }
#       }
#     ],
#     "tyre-sets": {
#       "car-index": 19,
#       "fitted-index": 6,
#       "tyre-set-data": [
#         {
#           "actual-tyre-compound": "C4",
#           "available": False,
#           "fitted": False,
#           "lap-delta-time": -989,
#           "life-span": 26,
#           "recommended-session": 1,
#           "usable-life": 26,
#           "visual-tyre-compound": "Soft",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C2",
#           "available": False,
#           "fitted": False,
#           "lap-delta-time": 100,
#           "life-span": 40,
#           "recommended-session": 1,
#           "usable-life": 40,
#           "visual-tyre-compound": "Hard",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C4",
#           "available": False,
#           "fitted": False,
#           "lap-delta-time": -989,
#           "life-span": 26,
#           "recommended-session": 2,
#           "usable-life": 26,
#           "visual-tyre-compound": "Soft",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C3",
#           "available": False,
#           "fitted": False,
#           "lap-delta-time": -444,
#           "life-span": 35,
#           "recommended-session": 2,
#           "usable-life": 35,
#           "visual-tyre-compound": "Medium",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C4",
#           "available": False,
#           "fitted": False,
#           "lap-delta-time": -989,
#           "life-span": 26,
#           "recommended-session": 3,
#           "usable-life": 26,
#           "visual-tyre-compound": "Soft",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C4",
#           "available": False,
#           "fitted": False,
#           "lap-delta-time": -989,
#           "life-span": 26,
#           "recommended-session": 3,
#           "usable-life": 26,
#           "visual-tyre-compound": "Soft",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C4",
#           "available": True,
#           "fitted": True,
#           "lap-delta-time": 0,
#           "life-span": 21,
#           "recommended-session": 5,
#           "usable-life": 26,
#           "visual-tyre-compound": "Soft",
#           "wear": 12
#         },
#         {
#           "actual-tyre-compound": "C4",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": -989,
#           "life-span": 26,
#           "recommended-session": 5,
#           "usable-life": 26,
#           "visual-tyre-compound": "Soft",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C4",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": -989,
#           "life-span": 26,
#           "recommended-session": 6,
#           "usable-life": 26,
#           "visual-tyre-compound": "Soft",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C3",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": -444,
#           "life-span": 35,
#           "recommended-session": 6,
#           "usable-life": 35,
#           "visual-tyre-compound": "Medium",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C4",
#           "available": False,
#           "fitted": False,
#           "lap-delta-time": -989,
#           "life-span": 26,
#           "recommended-session": 7,
#           "usable-life": 26,
#           "visual-tyre-compound": "Soft",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C3",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": -444,
#           "life-span": 35,
#           "recommended-session": 10,
#           "usable-life": 35,
#           "visual-tyre-compound": "Medium",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "C2",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": 100,
#           "life-span": 40,
#           "recommended-session": 10,
#           "usable-life": 40,
#           "visual-tyre-compound": "Hard",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "Inters",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": 5062,
#           "life-span": 40,
#           "recommended-session": 0,
#           "usable-life": 40,
#           "visual-tyre-compound": "Inters",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "Inters",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": 5062,
#           "life-span": 40,
#           "recommended-session": 0,
#           "usable-life": 40,
#           "visual-tyre-compound": "Inters",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "Inters",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": 5062,
#           "life-span": 40,
#           "recommended-session": 0,
#           "usable-life": 40,
#           "visual-tyre-compound": "Inters",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "Wet",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": 6915,
#           "life-span": 38,
#           "recommended-session": 0,
#           "usable-life": 38,
#           "visual-tyre-compound": "Wet",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "Wet",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": 6915,
#           "life-span": 38,
#           "recommended-session": 0,
#           "usable-life": 38,
#           "visual-tyre-compound": "Wet",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "Inters",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": 5062,
#           "life-span": 40,
#           "recommended-session": 10,
#           "usable-life": 40,
#           "visual-tyre-compound": "Inters",
#           "wear": 0
#         },
#         {
#           "actual-tyre-compound": "Wet",
#           "available": True,
#           "fitted": False,
#           "lap-delta-time": 6915,
#           "life-span": 38,
#           "recommended-session": 10,
#           "usable-life": 38,
#           "visual-tyre-compound": "Wet",
#           "wear": 0
#         }
#       ]
#     }
#   }