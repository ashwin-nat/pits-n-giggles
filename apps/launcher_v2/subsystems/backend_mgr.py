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

from lib.config import PngSettings
from lib.ipc import IpcParent

from .base_mgr import PngAppMgrBase
from PySide6.QtWidgets import QPushButton
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from apps.launcher_v2.gui import PngLauncherWindow

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
            display_name="Server",
            settings=settings,
            start_by_default=True,
            args=temp_args,
            debug_mode=debug_mode,
            coverage_enabled=coverage_enabled,
            http_port_conflict_settings_field='Network -> "Pits n\' Giggles HTTP Server Port"',
            udp_port_conflict_settings_field='Network -> "F1 UDP Telemetry Port"',
        )

        self.register_post_start(self.post_start)
        self.register_post_stop(self.post_stop)

    def get_buttons(self) -> List[QPushButton]:
        """Return a list of button objects directly
        :param frame: The frame to place the buttons in
        :return: List of button objects
        """

        self.start_stop_button = self.build_button("Start", self.start_stop_callback)
        self.open_dashboard_button = self.build_button("Dashboard", self.open_dashboard)
        self.open_obs_overlay_button = self.build_button("Stream overlay", self.open_obs_overlay)
        self.manual_save_button = self.build_button("Manual Save", self.manual_save)

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

        diff = self.curr_settings.diff(new_settings, {
            "Network": [
                "telemetry_port",
                "server_port",
                "udp_tyre_delta_action_code",
                "udp_custom_action_code",
                "wdt_interval_sec",
            ],
            "Capture" : [],
            "Display" : [],
            "Logging" : [],
            "Privacy" : [],
            "Forwarding" : [],
            "StreamOverlay" : [],
            "HUD": [
                "toggle_overlays_udp_action_code",
            ]
        })
        self.debug_log(f"{self.display_name} Settings changed: {json.dumps(diff, indent=2)}")

        # Restart if diff is not empty
        return bool(diff)

    def post_start(self):
        """Update buttons after app start"""
        self.set_button_text_state(self.start_stop_button, "Stop", True)
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.open_dashboard_button, True)
        self.set_button_state(self.open_obs_overlay_button, True)
        self.set_button_state(self.manual_save_button, True)

    def post_stop(self):
        """Update buttons after app stop"""
        self.set_button_text_state(self.start_stop_button, "Start", True)
        self.set_button_state(self.open_dashboard_button, False)
        self.set_button_state(self.open_obs_overlay_button, False)
        self.set_button_state(self.manual_save_button, False)

    def manual_save(self):
        """Send a manual save command to the backend."""
        self.debug_log("Sending manual save command to backend...")
        ipc_client = IpcParent(self.ipc_port)
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
