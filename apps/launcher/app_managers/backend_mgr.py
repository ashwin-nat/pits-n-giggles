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
from tkinter import ttk, messagebox

from lib.config import PngSettings
from lib.ipc import IpcParent

from ..console_interface import ConsoleInterface
from .base_mgr import PngAppMgrBase

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class BackendAppMgr(PngAppMgrBase):
    """Implementation of PngApp for backend services"""
    def __init__(self, console_app: ConsoleInterface, port_str: str, args: list[str], proto: str):
        """Initialize the backend manager
        :param console_app: Reference to a console interface for logging
        :param port_str: Port number to use for the backend
        :param args: Additional Command line arguments to pass to the backend
        :param proto: Protocol to use to open webpage
        """
        self.port_str = port_str
        self.proto = proto
        super().__init__(
            port_conflict_settings_field='Network -> "Pits n\' Giggles HTTP Server Port"',
            module_path="apps.backend",
            exe_name_without_ext="backend",
            display_name="Server",
            start_by_default=True,
            console_app=console_app,
            args=args
        )
        self.register_post_start(self.post_start)
        self.register_post_stop(self.post_stop)

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
        self.open_obs_overlay_button = ttk.Button(
            frame,
            text="Stream overlay",
            command=self.open_obs_overlay,
            style="Racing.TButton",
            state="disabled"  # Initially disabled until the app is running
        )
        self.manual_save_button = ttk.Button(
            frame,
            text="Manual Save",
            command=self.manual_save,
            style="Racing.TButton",
            state="disabled"  # Initially disabled until the app is running
        )
        return [
            self.start_stop_button,
            self.open_dashboard_button,
            self.open_obs_overlay_button,
            self.manual_save_button,
        ]

    def open_dashboard(self):
        """Open the dashboard viewer in a web browser."""
        webbrowser.open(f'{self.proto}://localhost:{self.port_str}', new=2)

    def open_obs_overlay(self):
        """Open the OBS overlay page in a web browser."""
        webbrowser.open(f'{self.proto}://localhost:{self.port_str}/player-stream-overlay', new=2)

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the backend application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """

        # Update the port number
        self.port_str = str(new_settings.Network.server_port)
        self.proto = new_settings.HTTPS.proto

        # Always restart the backend, since there are so many settings, it's easier to just restart it
        return True

    def post_start(self):
        """Update buttons after app start"""
        self.start_stop_button.config(text="Stop")
        self.open_dashboard_button.config(state="normal")
        self.open_obs_overlay_button.config(state="normal")
        self.manual_save_button.config(state="normal")

    def post_stop(self):
        """Update buttons after app stop"""
        self.start_stop_button.config(text="Start")
        self.open_dashboard_button.config(state="disabled")
        self.open_obs_overlay_button.config(state="disabled")
        self.manual_save_button.config(state="disabled")

    def manual_save(self):
        """Send a manual save command to the backend."""
        self.console_app.log("Sending manual save command to backend...")
        ipc_client = IpcParent(self.ipc_port)
        rsp = ipc_client.request("manual-save", {})
        status = rsp["status"]
        message = rsp.get("message")
        if status == "success":
            self.console_app.log("File path sent successfully.")
            messagebox.showinfo("Manual save success", f"The session has been saved successfully at {message}")
        else:
            error = rsp.get("error", "Unknown error")
            message = rsp.get("message", "")
            self.console_app.log(f"Error in manual save: error={error} message={message}")
            error_details = "\n".join(filter(None, [error, message]))
            messagebox.showerror("Manual save error", error_details)