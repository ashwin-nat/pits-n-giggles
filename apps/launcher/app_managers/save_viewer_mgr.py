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

from tkinter import ttk, filedialog
import subprocess
import threading
import sys

from ..console_interface import ConsoleInterface
from .base_mgr import PngAppMgrBase

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class SaveViewerAppMgr(PngAppMgrBase):
    """Implementation of PngApp for save viewer"""
    def __init__(self, console_app: ConsoleInterface, args: list[str] = None):
        """Initialize the save viewer manager
        :param console_app: Reference to a console interface for logging
        :param args: Command line arguments to pass to the save
        """
        super().__init__(
            name="save_viewer",
            module_path="apps.save_viewer.telemetry_post_race_data_viewer",
            display_name="Save Viewer",
            start_by_default=True,
            console_app=console_app,
            args=args
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
        self.open_file_button = ttk.Button(
            frame,
            text="Open File",
            command=self.open_file,
            style="Racing.TButton"
        )
        self.open_dashboard_button = ttk.Button(
            frame,
            text="Dashboard",
            command=self.open_dashboard,
            style="Racing.TButton",
            state="disabled"  # Initially disabled until the app is running
        )

        return [
            self.start_stop_button,
            self.open_file_button,
            self.open_dashboard_button,
        ]

    def start(self):
        """Start the sub-application process"""
        if self.is_running:
            self.console_app.log(f"{self.display_name} is already running.")
            return

        try:
            self.console_app.log(f"Starting {self.display_name}...")

            self.process = subprocess.Popen(
                [sys.executable, '-m', self.module_path, *self.args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.is_running = True
            self.status_var.set("Running")
            threading.Thread(target=self._capture_output, daemon=True).start()

            self.console_app.log(f"{self.display_name} started successfully.")
            self.start_stop_button.config(text="Stop")
            self.open_dashboard_button.config(state="normal")
        except Exception as e:
            self.console_app.log(f"Error starting {self.display_name}: {e}")
            self.status_var.set("Error")

        self.console_app.log(f"Starting {self.display_name}...")
        # Implementation of starting the dashboard
        self.status_var.set("Running")
        self.is_running = True
        self.start_stop_button.config(text="Stop")
        self.open_dashboard_button.config(state="normal")
        self.open_file_button.config(state="normal")

    def stop(self):
        """Stop the save viewer process"""
        if self.is_running:
            self.console_app.log(f"Stopping {self.display_name}...")
            # Implementation of stopping the dashboard
            self.status_var.set("Stopped")
            self.is_running = False
            self.start_stop_button.config(text="Start")
            self.open_dashboard_button.config(state="disabled")
            self.open_file_button.config(state="disabled")

    def open_dashboard(self):
        self.console_app.log("Opening dashboard viewer...")
        # Implementation of viewing dashboard data

    def open_file(self):
        file_path = filedialog.askopenfilename()
        self.console_app.log(f"Selected file: {file_path}")
        if file_path:
            if self.process:
                self.process.stdin.write(file_path + '\n')
                self.process.stdin.flush()
            else:
                self.console_app.log("No process running to send the file path to.")
