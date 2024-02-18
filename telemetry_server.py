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

try:
    from flask import Flask, render_template
except ImportError:
    print("Flask is not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip3", "install", "flask"])
    print("Flask installation complete.")
    from flask import Flask, render_template
try:
    from flask_cors import CORS
except ImportError:
    print("flask-cors is not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip3", "install", "flask-cors"])
    print("Flask installation complete.")
    from flask_cors import CORS
import telemetry_data as TelData
from telemetry_handler import dumpPktCapToFile
import logging

class TelemetryServer:
    def __init__(self, port, debug_mode=False):
        """
        Initialize TelemetryServer.

        Args:
            port (int): Port number for the server.
            debug_mode (bool, optional): Enable debug mode. Defaults to False.
        """
        self.m_app = Flask(__name__)
        self.m_app.config['PROPAGATE_EXCEPTIONS'] = True
        self.m_port = port
        self.m_debug_mode = debug_mode

        # Define your endpoint
        @self.m_app.route('/telemetry-info')
        def telemetryInfo():
            """
            Endpoint for telemetry information.

            Returns:
                str: Telemetry data in JSON format.
            """
            telemetry_data = self.getTelemetryData()
            return telemetry_data

        @self.m_app.route('/save-telemetry-capture', methods=['GET'])
        def saveTelemetryCapture():
            """
            Endpoint for saving telemetry packet capture.

            Returns:
                str: JSON response indicating success or failure.
            """
            return self.saveTelemetryData()

        # Render the HTML page
        @self.m_app.route('/')
        def index():
            """
            Endpoint for the index page.

            Returns:
                str: HTML page content.
            """
            return render_template('index.html')

    def getValueOrDefaultValue(self, value, default_value='---'):
        """
        Get value or default as string.

        Args:
            value: The value to check.
            default_value (str, optional): Default value if the input is None. Defaults to '---'.

        Returns:
            str: The value as string or default string.
        """
        return value if value is not None else default_value

    def getTelemetryData(self):
        """
        Get telemetry data in JSON format.

        Returns:
            str: Telemetry data in JSON format.
        """

        # Fetch the data from the data stores
        driver_data, fastest_lap_overall = TelData.getDriverData()
        circuit, track_temp, event_type, total_laps, curr_lap, \
            safety_car_status, weather_forecast_samples, pit_speed_limit = TelData.getGlobals()

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
            "weather-forecast-samples": []
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
                    "drs": self.getDRSValue(data_per_driver.m_drs_activated, data_per_driver.m_drs_allowed,
                                            data_per_driver.m_drs_distance),
                    "num-pitstops": self.getValueOrDefaultValue(data_per_driver.m_num_pitstops),
                    "dnf-status" : self.getValueOrDefaultValue(data_per_driver.m_dnf_status_code),
                    "index" : self.getValueOrDefaultValue(data_per_driver.m_index)
                }
            )

        return json_response

    def saveTelemetryData(self) -> str:
        """Save the raw telemetry data to a file.

        Returns:
            str: The str containing the JSON response
        """

        status_code, file_name, num_packets, num_bytes = dumpPktCapToFile(clear_db=True, reason='Received Request')
        return {
            "is-success" : (True if file_name else False),
            "status-code" : str(status_code),
            "file-name" : self.getValueOrDefaultValue(file_name, ""),
            "num-packets" : self.getValueOrDefaultValue(num_packets, default_value=0),
            "num-bytes" : self.getValueOrDefaultValue(num_bytes, default_value=0)
        }

    def getDeltaPlusPenaltiesPlusPit(self, delta, penalties, is_pitting, dnf_status_code: str):
        """
        Get delta plus penalties plus pit information.

        Args:
            delta: Delta information.
            penalties: Penalties information.
            is_pitting: Whether the driver is pitting.
            dnf_status_code: The code indicating DNF status. Empty string if driver is still racing

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

    def getDRSValue(self, drs_activated, drs_available, drs_distance):
        """
        Get DRS value.

        Args:
            drs_activated: Whether DRS is activated.
            drs_available: Whether DRS is available.
            drs_distance: DRS distance.

        Returns:
            bool: True if DRS is activated or available or has non-zero distance, False otherwise.
        """
        return True if (drs_activated or drs_available or (drs_distance > 0)) else False

    def run(self):
        """
        Run the TelemetryServer.
        """

        # Disable Werkzeug request logging
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)

        self.m_app.run(debug=self.m_debug_mode, port=self.m_port, threaded=True, use_reloader=False, host='0.0.0.0')
