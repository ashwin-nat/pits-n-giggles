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
import webbrowser
from typing import TYPE_CHECKING, List

from PySide6.QtWidgets import QPushButton

from lib.config import PngSettings
from lib.ipc import IpcClientSync

from .base_mgr import PngAppMgrBase

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BackendAppMgr(PngAppMgrBase):
    """Implementation of PngApp for backend services"""
    def __init__(self,
                 window: "PngLauncherWindow",
                 settings: PngSettings,
                 args: list[str],
                 debug_mode: bool,
                 replay_server: bool,
                 coverage_enabled: bool):
        """Initialize the backend manager
        :param window: Reference to the GUI window object
        :param settings: Settings object
        :param args: Additional Command line arguments to pass to the backend
        :param debug_mode: Whether to run the backend in debug mode
        :param replay_server: Whether to run the replay server
        :param coverage_enabled: Whether to enable coverage
        """

        extra_args = []
        extra_args.append("--run-ipc-server")
        if debug_mode:
            extra_args.append("--debug")
        if replay_server:
            extra_args.append("--replay-server")
        temp_args = args + extra_args
        self.port = settings.Network.server_port
        self.proto = settings.HTTPS.proto
        super().__init__(
            window=window,
            module_path="apps.backend",
            display_name="Core",
            short_name="CORE",
            settings=settings,
            start_by_default=True,
            should_display=True,
            args=temp_args,
            debug_mode=debug_mode,
            coverage_enabled=coverage_enabled,
            http_port_conflict_settings_field='Network -> "Pits n\' Giggles HTTP Server Port"',
            udp_port_conflict_settings_field='Network -> "F1 UDP Telemetry Port"',
            post_start_cb=self.post_start,
            post_stop_cb=self.post_stop
        )

    def get_buttons(self) -> List[QPushButton]:
        """Return a list of button objects directly
        :return: List of button objects
        """

        self.start_stop_button = self.build_button(self.get_icon("start"), self.start_stop_callback, "Start")
        self.open_dashboard_button = self.build_button(self.get_icon("dashboard"), self.open_dashboard,
                                                       "Open Dashboard")
        self.open_obs_overlay_button = self.build_button(self.get_icon("twitch"), self.open_obs_overlay,
                                                         "Open Stream Overlay")
        self.manual_save_button = self.build_button(self.get_icon("save"), self.manual_save, "Manual Save")

        return [
            self.start_stop_button,
            self.open_dashboard_button,
            self.open_obs_overlay_button,
            self.manual_save_button,
        ]

    def open_dashboard(self):
        """Open the dashboard viewer in a web browser."""
        webbrowser.open(f'{self.proto}://localhost:{self.port}', new=2)

    def open_obs_overlay(self):
        """Open the OBS overlay page in a web browser."""
        webbrowser.open(f'{self.proto}://localhost:{self.port}/player-stream-overlay', new=2)

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the backend application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """

        # Update the port number
        self.port = new_settings.Network.server_port
        self.proto = new_settings.HTTPS.proto

        # Update UDP action codes if required
        if udp_action_codes_diff := self.curr_settings.diff(new_settings, {
            "Network": [
                "udp_tyre_delta_action_code",
                "udp_custom_action_code",
                "broker_xsub_port",
            ],
            "HUD": [
                "toggle_overlays_udp_action_code",
                "lap_timer_toggle_udp_action_code",
                "timing_tower_toggle_udp_action_code",
                "mfd_toggle_udp_action_code",
                "cycle_mfd_udp_action_code",
            ],
        }):
            for fields_in_category in udp_action_codes_diff.values():
                for field, diff in fields_in_category.items():
                    new_value = diff["new_value"]
                    self.send_udp_action_code_change(field, new_value)
        else:
            self.debug_log(f"{self.display_name} UDP action codes NO CHANGE")

        if restart_required_fields_diff := self.curr_settings.diff(new_settings, {
            "Network": [
                "telemetry_port",
                "server_port",
                "wdt_interval_sec",
            ],
            "Capture" : [],
            "Display" : [
                "refresh_interval",
            ],
            "Logging" : [],
            "Privacy" : [],
            "Forwarding" : [],
            "StreamOverlay" : [],
            "TimeLossInPitsF1": [],
            "TimeLossInPitsF2": [],
        }):
            self.debug_log(f"{self.display_name} Restart required fields change: "
                           f"{json.dumps(restart_required_fields_diff, indent=2)}")
        else:
            self.debug_log(f"{self.display_name} Restart required fields NO CHANGE")

        # Restart if diff is not empty
        return bool(restart_required_fields_diff)

    def post_start(self):
        """Update buttons after app start"""
        self.set_button_icon(self.start_stop_button, self.get_icon("stop"))
        self.set_button_tooltip(self.start_stop_button, "Stop")
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.open_dashboard_button, True)
        self.set_button_state(self.open_obs_overlay_button, True)
        self.set_button_state(self.manual_save_button, True)

    def post_stop(self):
        """Update buttons after app stop"""
        self.set_button_icon(self.start_stop_button, self.get_icon("start"))
        self.set_button_tooltip(self.start_stop_button, "Start")
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.open_dashboard_button, False)
        self.set_button_state(self.open_obs_overlay_button, False)
        self.set_button_state(self.manual_save_button, False)

    def manual_save(self):
        """Send a manual save command to the backend."""
        self.debug_log("Sending manual save command to backend...")
        ipc_client = IpcClientSync(self.ipc_port)
        rsp = ipc_client.request("manual-save", {})

        status = rsp["status"]
        message = rsp.get("message")

        if status == "success":
            self.info_log(f"Manual save success. Path {message}")
            self.show_success("Manual Save Success", f"The session has been saved successfully at:\n{message}")

        else:
            error = rsp.get("error", "Unknown error")
            message = rsp.get("message", "")
            self.info_log(f"Error in manual save: error={error} message={message}")

            error_details = "\n".join(filter(None, [error, message]))
            self.show_error("Manual Save Error", error_details)

    def send_udp_action_code_change(self, action_code_field: str, value: int):
        """Send a UDP action code change command to the backend."""
        self.debug_log(f"Sending UDP action code change for {action_code_field} to backend...")
        ipc_client = IpcClientSync(self.ipc_port)
        rsp = ipc_client.request("udp-action-code-change", {"action_code_field": action_code_field, "value": value})
        if not rsp or rsp.get("status") != "success":
            self.error_log(f"Failed to change UDP action code: {rsp}")
        else:
            self.debug_log(f"Change UDP action code response: {rsp}")

    def start_stop_callback(self):
        """Start or stop the backend application."""
        # disable the button. enable in post_start/post_stop
        self.set_button_state(self.start_stop_button, False)
        self.set_button_state(self.manual_save_button, False)
        self.set_button_state(self.open_dashboard_button, False)
        self.set_button_state(self.open_obs_overlay_button, False)
        try:
            # Call the start_stop method
            self.start_stop("Stop button pressed")
        except Exception as e: # pylint: disable=broad-exception-caught
            # Log the error or handle it as needed
            self.debug_log(f"{self.display_name}:Error during start/stop: {e}")
            # If no exception, it will be handled in post_start/post_stop
            self.set_button_state(self.start_stop_button, True)
