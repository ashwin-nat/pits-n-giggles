# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

import webbrowser
from dataclasses import replace
from typing import TYPE_CHECKING, List

from PySide6.QtWidgets import QPushButton

from lib.config import PngSettings
from lib.error_status import PNG_ERROR_CODE_HTTP_PORT_IN_USE

from .base_mgr import ExitReason, PngAppMgrBase, PngAppMgrConfig

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WebAppMgr(PngAppMgrBase):
    """Implementation of PngApp for the unified web subsystem (live dashboard + save viewer)"""

    MODULE_PATH = "apps.web"
    DISPLAY_NAME = "Web"
    SHORT_NAME = "WEB"

    def __init__(self,
                 common_cfg: PngAppMgrConfig):
        """Initialize the web manager
        :param common_cfg: Common configuration for the web app manager
        """

        extra_args = []
        if common_cfg.debug_mode:
            extra_args.append("--debug")
        temp_args = common_cfg.args + extra_args
        self.port = common_cfg.settings.Network.server_port
        self.proto = common_cfg.settings.HTTPS.proto

        config = replace(common_cfg,
                         args=temp_args,
                         post_start_cb=self.post_start,
                         post_stop_cb=self.post_stop
        )

        super().__init__(
            config=config,
        )
        self.register_exit_reason(PNG_ERROR_CODE_HTTP_PORT_IN_USE, ExitReason(
            code=PNG_ERROR_CODE_HTTP_PORT_IN_USE,
            status="HTTP Port Conflict",
            title="HTTP port in use",
            message="The HTTP port is already in use by another process. Please close the other process and try again or change the port.",
            can_restart=False,
            settings_field='Network -> "Pits n\' Giggles HTTP Server Port"'
        ))

    def get_buttons(self) -> List[QPushButton]:
        """Return a list of button objects directly
        :return: List of button objects
        """

        self.start_stop_button = self.build_button(self.get_icon("start"), self.start_stop_callback, "Start")
        self.open_dashboard_button = self.build_button(self.get_icon("dashboard"), self.open_dashboard,
                                                       "Open Dashboard")
        self.open_obs_overlay_button = self.build_button(self.get_icon("twitch"), self.open_obs_overlay,
                                                         "Open Stream Overlay")

        return [
            self.start_stop_button,
            self.open_dashboard_button,
            self.open_obs_overlay_button,
        ]

    def open_dashboard(self):
        """Open the dashboard viewer in a web browser."""
        # TODO(Phase 3): point at "/" once the shared sidebar + home/hub page lands.
        webbrowser.open(f'{self.proto}://localhost:{self.port}/live', new=2)

    def open_obs_overlay(self):
        """Open the OBS overlay page in a web browser."""
        webbrowser.open(f'{self.proto}://localhost:{self.port}/player-stream-overlay', new=2)

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the web application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """

        diff = self.curr_settings.diff(new_settings, {
            "Network": [
                "server_port",
                "bind_address",
                "broker_xpub_port",
                "broker_router_port",
            ],
            "Display": [
                "refresh_interval",
            ],
            "HTTPS": [],
        })
        self.debug_log(f"{self.DISPLAY_NAME} Settings changed: {diff}")
        # Update the port number
        self.port = new_settings.Network.server_port
        self.proto = new_settings.HTTPS.proto
        return bool(diff)

    def post_start(self):
        """Update buttons after app start"""
        self.set_button_icon(self.start_stop_button, self.get_icon("stop"))
        self.set_button_tooltip(self.start_stop_button, "Stop")
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.open_dashboard_button, True)
        self.set_button_state(self.open_obs_overlay_button, True)

    def post_stop(self):
        """Update buttons after app stop"""
        self.set_button_icon(self.start_stop_button, self.get_icon("start"))
        self.set_button_tooltip(self.start_stop_button, "Start")
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.open_dashboard_button, False)
        self.set_button_state(self.open_obs_overlay_button, False)

    def start_stop_callback(self):
        """Start or stop the web application."""
        # disable the button. enable in post_start/post_stop
        self.set_button_state(self.start_stop_button, False)
        self.set_button_state(self.open_dashboard_button, False)
        self.set_button_state(self.open_obs_overlay_button, False)
        try:
            # Call the start_stop method
            self.start_stop("Button pressed")
        except Exception as e: # pylint: disable=broad-exception-caught
            # Log the error or handle it as needed
            self.debug_log(f"{self.DISPLAY_NAME}:Error during start/stop: {e}")
            # If no exception, it will be handled in post_start/post_stop
            self.set_button_state(self.start_stop_button, True)
