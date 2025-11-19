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

import webbrowser
from typing import TYPE_CHECKING, List

from PySide6.QtWidgets import QPushButton

from lib.config import PngSettings
from lib.ipc import IpcParent

from .base_mgr import PngAppMgrBase

if TYPE_CHECKING:
    from apps.launcher_v2.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SaveViewerAppMgr(PngAppMgrBase):
    """Implementation of PngApp for save viewer"""
    def __init__(self,
                 window: "PngLauncherWindow",
                 settings: PngSettings,
                 args: list[str],
                 debug_mode: bool,
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
        temp_args = args + extra_args
        self.port = settings.Network.save_viewer_port
        self.proto = settings.HTTPS.proto
        super().__init__(
            window=window,
            module_path="apps.save_viewer",
            display_name="Save Viewer",
            short_name="SAVE",
            settings=settings,
            start_by_default=True,
            args=temp_args,
            debug_mode=debug_mode,
            coverage_enabled=coverage_enabled,
            http_port_conflict_settings_field='Network -> "Pits n\' Giggles Save Data Viewer Port"',
            udp_port_conflict_settings_field="N/A",
        )

        self.register_post_start(self.post_start)
        self.register_post_stop(self.post_stop)

    def get_buttons(self) -> List[QPushButton]:
        """Return a list of button objects directly
        :return: List of button objects
        """

        self.start_stop_button = self.build_button(self.get_icon("start"), self.start_stop_callback)
        self.open_file_button = self.build_button(self.get_icon("open-file"), self.open_file)
        self.open_dashboard_button = self.build_button(self.get_icon("dashboard"), self.open_dashboard)

        return [
            self.start_stop_button,
            self.open_file_button,
            self.open_dashboard_button,
        ]

    def open_dashboard(self):
        """Open the dashboard viewer in a web browser."""
        webbrowser.open(f'http://localhost:{self.port}', new=2)

    def open_file(self):
        """Open a file dialog and send the selected file path to the backend process."""
        file_path = self.select_file(title="Select File", file_filter="JSON files (*.json);;All Files (*.*)")

        if file_path:
            self.debug_log(f"Selected file: {file_path}")

            if self.process:
                ipc_client = IpcParent(self.ipc_port)
                rsp = ipc_client.request("open-file", {"file-path": file_path})

                if rsp["status"] != "error":
                    self.info_log("File path sent successfully.")
                else:
                    self.info_log(f"Error sending file path: {rsp['message']}")
                    self.show_error("File open error", "\n".join([rsp["message"]]))
            else:
                self.info_log("No process running to send the file path to.")

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the backend application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """

        diff = self.curr_settings.diff(new_settings, {
            "Network": ["save_viewer_port"],
        })
        self.debug_log(f"{self.display_name} Settings changed: {diff}")
        # Update the port number
        should_restart = (self.port != new_settings.Network.save_viewer_port)
        self.port = new_settings.Network.save_viewer_port
        return should_restart

    def post_start(self):
        """Update buttons after app start"""
        self.set_button_icon(self.start_stop_button, self.get_icon("stop"))
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.open_file_button, True)
        self.set_button_state(self.open_dashboard_button, True)

    def post_stop(self):
        """Update buttons after app stop"""
        self.set_button_icon(self.start_stop_button, self.get_icon("start"))
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.open_file_button, False)
        self.set_button_state(self.open_dashboard_button, False)

    def start_stop_callback(self):
        """Start or stop the backend application."""
        # disable the button. enable in post_start/post_stop
        self.set_button_state(self.start_stop_button, False)
        self.set_button_state(self.open_file_button, False)
        self.set_button_state(self.open_dashboard_button, False)
        try:
            # Call the start_stop method
            self.start_stop("Button pressed")
        except Exception as e: # pylint: disable=broad-exception-caught
            # Log the error or handle it as needed
            self.debug_log(f"{self.display_name}:Error during start/stop: {e}")
            # If no exception, it will be handled in post_start/post_stop
            self.set_button_state(self.start_stop_button, True)
