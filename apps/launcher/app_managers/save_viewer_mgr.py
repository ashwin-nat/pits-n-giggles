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

from tkinter import ttk

from ..console_interface import ConsoleInterface
from .base_mgr import PngAppMgrBase

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class SaveViewerAppMgr(PngAppMgrBase):
    """Implementation of PngApp for save viewer"""
    def __init__(self, console_app: ConsoleInterface):
        """Initialize the save viewer manager
        :param console_app: Reference to a console interface for logging
        """
        super().__init__(
            name="save_viewer",
            module_path="apps.save_viewer.telemetry_post_race_viewer",
            display_name="Save Viewer",
            start_by_default=False,
            console_app=console_app
        )

    def get_buttons(self, frame: ttk.Frame) -> list[dict]:
        """Return a list of button objects directly
        :param frame: The frame to place the buttons in
        :return: List of button objects
        """

        self.start_stop_button = ttk.Button(
            frame,
            text="Start",
            command=self.start_stop,
            style="Racing.TButton"
        )
        self.open_dashboard_button = ttk.Button(
            frame,
            text="Dashboard",
            command=self.open_dashboard,
            style="Racing.TButton",
            state="disabled"  # Initially disabled until the app is running
        )

        return [self.start_stop_button, self.open_dashboard_button]

    def start(self):
        """Start the save viewer process"""
        if not self.is_running:
            self.console_app.log(f"Starting {self.display_name}...")
            # Implementation of starting the dashboard
            self.status_var.set("Running")
            self.is_running = True
            self.start_stop_button.config(text="Stop")
            self.open_dashboard_button.config(state="normal")

    def stop(self):
        """Stop the save viewer process"""
        if self.is_running:
            self.console_app.log(f"Stopping {self.display_name}...")
            # Implementation of stopping the dashboard
            self.status_var.set("Stopped")
            self.is_running = False
            self.start_stop_button.config(text="Start")
            self.open_dashboard_button.config(state="disabled")

    def open_dashboard(self):
        self.console_app.log("Opening dashboard viewer...")
        # Implementation of viewing dashboard data
