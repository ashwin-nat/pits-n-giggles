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

from typing import Dict, Any
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

from src.telemetry_handler import dumpPktCapToFile, getOvertakeJSON, GetOvertakesStatus, getCustomMarkersJSON
from lib.race_analyzer import getFastestTimesJson, getTyreStintRecordsDict
from lib.f1_types import F1Utils
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
            return self.getRaceTelemetryInfo()

        @self.m_app.route('/player-telemetry-info')
        def playerTelemetryInfo() -> Dict:
            """
            Endpoint for telemetry information.

            Returns:
                str: Telemetry data in JSON format.
            """
            return self.getPlayerTelemetryInfo()

        # Define your endpoint
        @self.m_app.route('/race-info')
        def overtakeInfo() -> Dict:
            """
            Endpoint for overtake information.

            Returns:
                str: Overtake data in JSON format.
            """
            rsp = TelData.getRaceInfo()
            self._checkUpdateRecords(rsp)
            return rsp

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
                client_poll_interval_ms=self.m_client_poll_interval_ms,
                player_only_telemetry=False,
                hide_delta_column=True)

        # Render the HTML page
        @self.m_app.route('/obs-overlay')
        def obsOverlay():
            """
            Endpoint for the index page.

            Returns:
                str: HTML page content.
            """

            return render_template('index.html',
                packet_capture_enabled=self.m_packet_capture_enabled,
                client_poll_interval_ms=self.m_client_poll_interval_ms,
                player_only_telemetry=True)

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
        for data_per_driver in driver_data:
            json_response["table-entries"].append(
                {
                    "position": self.getValueOrDefaultValue(data_per_driver.m_position),
                    "name": self.getValueOrDefaultValue(data_per_driver.m_name),
                    "team": self.getValueOrDefaultValue(data_per_driver.m_team),
                    "delta": self.getDeltaPlusPenaltiesPlusPit(data_per_driver.m_delta_to_car_in_front,
                                                               data_per_driver.m_penalties,
                                                               data_per_driver.m_is_pitting,
                                                               data_per_driver.m_dnf_status_code),
                    "delta-to-leader": self.getDeltaPlusPenaltiesPlusPit(
                                F1Utils.millisecondsToSecondsMilliseconds(data_per_driver.m_delta_to_leader),
                                                               data_per_driver.m_penalties,
                                                               data_per_driver.m_is_pitting,
                                                               data_per_driver.m_dnf_status_code),
                    "ers": self.getValueOrDefaultValue(data_per_driver.m_ers_perc),
                    "best": self.getValueOrDefaultValue(data_per_driver.m_best_lap_str),
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
                    "lap-progress" : data_per_driver.m_lap_progress, # NULL is supported
                    "corner-cutting-warnings" : self.getValueOrDefaultValue(data_per_driver.m_corner_cutting_warnings),
                    "time-penalties" : self.getValueOrDefaultValue(data_per_driver.m_time_penalties),
                    "num-dt" : self.getValueOrDefaultValue(data_per_driver.m_num_dt),
                    "num-sg" : self.getValueOrDefaultValue(data_per_driver.m_num_sg)
                }
            )

        return json_response

    def getPlayerTelemetryInfo(self) -> Dict:
        """
        Get player telemetry data in JSON format.

        Returns:
            Dict: Player Telemetry data in JSON format.
        """

        # Fetch the data from the data stores
        player_driver_data, fastest_lap_overall = TelData.getPlayerDriverData()
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
        if player_driver_data:
            driver_data = [player_driver_data]
        else:
            driver_data = []
        for data_per_driver in driver_data:
            # if data_per_driver.m_is_fastest:
            #     fastest_lap_overall = data_per_driver.m_best_lap
            json_response["table-entries"].append(
                {
                    "position": self.getValueOrDefaultValue(data_per_driver.m_position),
                    "name": self.getValueOrDefaultValue(data_per_driver.m_name),
                    "team": self.getValueOrDefaultValue(data_per_driver.m_team),
                    "delta": self.getDeltaPlusPenaltiesPlusPit(data_per_driver.m_delta_to_car_in_front,
                                                               data_per_driver.m_penalties,
                                                               data_per_driver.m_is_pitting,
                                                               data_per_driver.m_dnf_status_code),
                    "ers": self.getValueOrDefaultValue(data_per_driver.m_ers_perc),
                    "best": self.getValueOrDefaultValue(data_per_driver.m_best_lap_str),
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
                    "lap-progress" : data_per_driver.m_lap_progress, # NULL is supported
                    "corner-cutting-warnings" : self.getValueOrDefaultValue(data_per_driver.m_corner_cutting_warnings),
                    "time-penalties" : self.getValueOrDefaultValue(data_per_driver.m_time_penalties),
                    "num-dt" : self.getValueOrDefaultValue(data_per_driver.m_num_dt),
                    "num-sg" : self.getValueOrDefaultValue(data_per_driver.m_num_sg),
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

    def _checkUpdateRecords(self, json_data: Dict[str, Any]):
        """
        Checks the given JSON data for the presence of certain keys and updates the data if necessary.

        Args:
            json_data (Dict[str, Any]): The JSON data to be checked and updated.
        """

        if "records" not in json_data:
            json_data["records"] = {}

        if "fastest" not in json_data["records"]:
            try:
                json_data["records"]["fastest"] = getFastestTimesJson(json_data)
            except ValueError:
                logging.debug('Failed to get fastest times JSON')
                json_data["records"]["fastest"] = None

        if "tyre-stats" not in json_data["records"]:
            try:
                json_data["records"]["tyre-stats"] = getTyreStintRecordsDict(json_data)
            except:
                logging.debug('Failed to get tyre stats JSON')
                json_data["records"]["tyre-stats"] = None

        should_recompute_overtakes = False
        if "overtakes" not in json_data:
            json_data["overtakes"] = {
                "records" : []
            }
            should_recompute_overtakes = True

        expected_keys = [
            "number-of-overtakes",
            "number-of-times-overtaken",
            "most-heated-rivalries"
        ]
        for key in expected_keys:
            if key not in json_data["overtakes"]:
                should_recompute_overtakes = True

        if should_recompute_overtakes:
            _, overtake_records = getOvertakeJSON()
            json_data["overtakes"] = json_data["overtakes"] | overtake_records

        json_data["custom-markers"] = getCustomMarkersJSON()

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