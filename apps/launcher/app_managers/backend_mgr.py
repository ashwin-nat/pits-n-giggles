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

import os
import sys
import webbrowser
from tkinter import ttk

from ..console_interface import ConsoleInterface
from .base_mgr import PngAppMgrBase

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class BackendAppMgr(PngAppMgrBase):
    """Implementation of PngApp for backend services"""
    def __init__(self, console_app: ConsoleInterface, port_str: str, args: list[str] = None):
        """Initialize the backend manager
        :param console_app: Reference to a console interface for logging
        :param port_str: Port number to use for the backend
        :param args: Additional Command line arguments to pass to the backend
        """
        self.port_str = port_str
        super().__init__(
            name="server",
            module_path="apps.backend.pits_n_giggles",
            display_name="Server",
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
            text="Start", # Intially, app is stopped
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


    def open_dashboard(self):
        """Open the dashboard viewer in a web browser."""
        webbrowser.open(f'http://localhost:{self.port_str}', new=2)

    def on_settings_change(self, new_settings):
        """Handle changes in settings for the backend application"""

        # Update the port number
        self.port_str = new_settings.get("Network", "server_port")

    def get_launch_command(self, module_path: str, args: list[str]):
        """Get the command to launch the backend application"""
        if not getattr(sys, 'frozen', False):
            return [sys.executable, "-m", module_path, *args]
        exe_path = os.path.join(sys._MEIPASS, 'embedded_exes', 'backend.exe')
        return [exe_path, *args]
