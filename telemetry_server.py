from flask import Flask, jsonify, render_template
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

    def get_value_or_default_str(self, value):
        return value if value is not None else "---"

    def get_telemetry_data(self):
        driver_data = TelData.get_driver_data()
        circuit, track_temp, event_type, total_laps, curr_lap = TelData.get_globals()

        json_response = {
            "circuit": self.get_value_or_default_str(circuit),
            "track-temperature": self.get_value_or_default_str(track_temp),
            "event-type": self.get_value_or_default_str(event_type),
            "total-laps": self.get_value_or_default_str(total_laps),
            "current-lap": self.get_value_or_default_str(curr_lap),
        }

        json_response["table-entries"] = []
        for data_per_driver in driver_data:
            penalties_str = ""
            json_response["table-entries"].append(
                {
                    "position": self.get_value_or_default_str(data_per_driver.m_position),
                    "name": self.get_value_or_default_str(data_per_driver.m_name),
                    "team": self.get_value_or_default_str(data_per_driver.m_team),
                    "delta": self.get_delta_plus_penalties(data_per_driver.m_delta, data_per_driver.m_penalties),
                    "ers": self.get_value_or_default_str(data_per_driver.m_ers_perc),
                    "best": self.get_value_or_default_str(data_per_driver.m_best_lap),
                    "last": self.get_value_or_default_str(data_per_driver.m_last_lap),
                    "is-fastest": self.get_value_or_default_str(data_per_driver.m_is_fastest),
                    "is-player": self.get_value_or_default_str(data_per_driver.m_is_player),
                    "average-tyre-wear": self.get_value_or_default_str(data_per_driver.m_tyre_wear),
                    "tyre-age" : self.get_value_or_default_str(data_per_driver.m_tyre_age),
                    "tyre-compound" : self.get_value_or_default_str(data_per_driver.m_tyre_compound_type)
                }
            )

        return jsonify(json_response)

    def get_delta_plus_penalties(self, delta, penalties):

        if delta is not None:
            return delta + " " + penalties
        else:
            return "---"

    def run(self):
        self.m_app.run(debug=self.m_debug_mode, port=self.m_port, threaded=True, use_reloader=False)
