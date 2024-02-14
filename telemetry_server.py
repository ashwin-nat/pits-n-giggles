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
    from flask import Flask, jsonify, render_template
except ImportError:
    print("Flask is not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "flask"])
    print("Flask installation complete.")
import telemetry_data as TelData


class TelemetryServer:
    def __init__(self, port, debug_mode=False):
        self.m_app = Flask(__name__)
        self.m_app.config['PROPAGATE_EXCEPTIONS'] = True
        self.m_port = port
        self.m_debug_mode = debug_mode

        # Define your endpoint
        @self.m_app.route('/telemetry-info')
        def telemetry_info():
            telemetry_data = self.get_telemetry_data()
            return telemetry_data

        # Render the HTML page
        @self.m_app.route('/')
        def index():
            return render_template('index.html')

    def get_value_or_default_str(self, value, default_value='---'):
        return value if value is not None else default_value

    def get_telemetry_data(self):
        driver_data = TelData.get_driver_data()
        circuit, track_temp, event_type, total_laps, curr_lap, \
            safety_car_status, weather_forecast_samples = TelData.get_globals()

        json_response = {
            "circuit": self.get_value_or_default_str(circuit),
            "track-temperature": self.get_value_or_default_str(track_temp),
            "event-type": self.get_value_or_default_str(event_type),
            "total-laps": self.get_value_or_default_str(total_laps),
            "current-lap": self.get_value_or_default_str(curr_lap),
            "safety-car-status": str(self.get_value_or_default_str(safety_car_status, default_value="")),
            "weather-forecast-samples" : [
            ]
        }
        for sample in weather_forecast_samples:
            json_response["weather-forecast-samples"].append(
                {
                    "time-offset" : str(sample.m_timeOffset),
                    "weather" : str(sample.m_weather),
                    "rain-probability" : str(sample.m_rainPercentage)
                }
            )

        json_response["table-entries"] = []
        fastest_lap_overall = "---"
        for data_per_driver in driver_data:
            if data_per_driver.m_is_fastest:
                fastest_lap_overall = data_per_driver.m_best_lap
            json_response["table-entries"].append(
                {
                    "position": self.get_value_or_default_str(data_per_driver.m_position),
                    "name": self.get_value_or_default_str(data_per_driver.m_name),
                    "team": self.get_value_or_default_str(data_per_driver.m_team),
                    "delta": self.get_delta_plus_penalties_plus_pit(data_per_driver.m_delta,
                                                        data_per_driver.m_penalties, data_per_driver.m_is_pitting),
                    "ers": self.get_value_or_default_str(data_per_driver.m_ers_perc),
                    "best": self.get_value_or_default_str(data_per_driver.m_best_lap),
                    "last": self.get_value_or_default_str(data_per_driver.m_last_lap),
                    "is-fastest": self.get_value_or_default_str(data_per_driver.m_is_fastest),
                    "is-player": self.get_value_or_default_str(data_per_driver.m_is_player),
                    "average-tyre-wear": self.get_value_or_default_str(data_per_driver.m_tyre_wear),
                    "tyre-age" : self.get_value_or_default_str(data_per_driver.m_tyre_age),
                    "tyre-compound" : self.get_value_or_default_str(data_per_driver.m_tyre_compound_type),
                    "drs" : self.get_drs_value(data_per_driver.m_drs_activated, data_per_driver.m_drs_allowed,
                                                data_per_driver.m_drs_distance),
                    "num-pitstops" : self.get_value_or_default_str(data_per_driver.m_num_pitstops)
                }
            )
        json_response["fastest-lap-overall"] = fastest_lap_overall

        return jsonify(json_response)

    def get_delta_plus_penalties_plus_pit(self, delta, penalties, is_pitting):

        if is_pitting:
            return "PIT " + penalties
        elif delta is not None:
            return delta + " " + penalties
        else:
            return "---"

    def get_drs_value(self, drs_activated, drs_available, drs_distance):
        return True if (drs_activated or drs_available or (drs_distance > 0)) else False

    def run(self):
        self.m_app.run(debug=self.m_debug_mode, port=self.m_port, threaded=True, use_reloader=False)
