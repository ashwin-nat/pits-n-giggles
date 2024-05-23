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

from typing import Dict, Any, Optional
from http import HTTPStatus
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from src.telemetry_handler import dumpPktCapToFile, getOvertakeJSON, GetOvertakesStatus, getCustomMarkersJSON
from lib.race_analyzer import getFastestTimesJson, getTyreStintRecordsDict
from lib.f1_types import F1Utils
import src.telemetry_data as TelData
import src.telemetry_web_api as TelWebAPI

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

            return TelWebAPI.RaceInfoRsp().toJSON(), HTTPStatus.OK

        # Define your endpoint
        @self.m_app.route('/race-info')
        def overtakeInfo() -> Dict:
            """
            Endpoint for overtake information.

            Returns:
                str: Overtake data in JSON format.
            """

            return TelWebAPI.OverallRaceStatsRsp().toJSON(), HTTPStatus.OK

        @self.m_app.route('/save-telemetry-capture')
        def saveTelemetryCapture() -> Dict:
            """
            Endpoint for saving telemetry packet capture.

            Returns:
                str: JSON response indicating success or failure.
            """
            return TelWebAPI.SavePacketCaptureRsp().toJSON()

        @self.m_app.route('/driver-info', methods=['GET'])
        def driverInfo() -> Dict:
            """
            Endpoint for saving telemetry packet capture.

            Returns:
                str: JSON response indicating success or failure.
            """

            # Access parameters using request.args
            index = request.args.get('index')

            # Validate the input
            error_response = self.validateIntGetRequestParam(index, 'index')
            if error_response:
                return error_response, HTTPStatus.BAD_REQUEST

            # Check if the given index is valid
            index = int(index)
            if not TelData.isDriverIndexValid(index):
                error_response = {
                    'error' : 'Invalid parameter value',
                    'message' : 'Invalid index'
                }
                return jsonify(error_response), HTTPStatus.BAD_REQUEST

            # Process parameters and generate response
            return TelWebAPI.DriverInfoRsp(index).toJSON(), HTTPStatus.OK

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
                num_adjacent_cars=self.m_num_adjacent_cars,
                live_data_mode=True)

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
                num_adjacent_cars=1,
                live_data_mode=True)

        # Render the HTML page
        @self.m_app.route('/full')
        def fullTelemetryView():
            """
            Endpoint for the index page.

            Returns:
                str: HTML page content.
            """

            return render_template('index.html',
                packet_capture_enabled=self.m_packet_capture_enabled,
                client_poll_interval_ms=self.m_client_poll_interval_ms,
                num_adjacent_cars=22,
                live_data_mode=True)

    def validateIntGetRequestParam(self, param: Any, param_name: str) -> Optional[Dict[str, Any]]:
        """
        Validate integer get request parameter.

        Args:
            param (Any): The parameter to check.
            param_name (str) : The name of the parameter (used in response)

        Returns:
            Optional[Dict[str, Any]]: Error response if the parameter is invalid, else None
        """

        # Check if only one parameter is provided
        if not param:
            return {
                'error': 'Invalid parameters',
                'message': f'Provide "{param_name}" parameter'
            }

        # Check if the provided value for index is numeric
        if not param.isdigit():
            return {
                'error': 'Invalid parameter value',
                'message': f'"{param_name}" parameter must be numeric'
            }

        return None

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
