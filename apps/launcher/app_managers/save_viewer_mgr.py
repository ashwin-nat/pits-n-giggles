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
from tkinter import filedialog, messagebox, ttk

from lib.config import PngSettings
from lib.ipc import IpcParent

from ..console_interface import ConsoleInterface
from .base_mgr import PngAppMgrBase

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class SaveViewerAppMgr(PngAppMgrBase):
    """Implementation of PngApp for save viewer"""
    def __init__(self, console_app: ConsoleInterface, port_str: str, extra_args: list[str] = None):
        """Initialize the save viewer manager
        :param console_app: Reference to a console interface for logging
        :param port_str: Port number to use for the save viewer
        :param extra_args: Additional Command line arguments to pass to the save
        """
        self.port_str = port_str
        args = ["--launcher", "--port", port_str]
        self.extra_args = extra_args or []
        super().__init__(
            port_conflict_settings_field='Network -> "Pits n\' Giggles Save Data Viewer Port"',
            module_path="apps.save_viewer",
            exe_name_without_ext="save_viewer",
            display_name="Save Viewer",
            start_by_default=True,
            console_app=console_app,
            args=args + self.extra_args
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
            text="Start",
            command=self.start_stop_callback,
            style="Racing.TButton",
            state="disabled"  # Initially disabled until the app is running
        )
        self.open_file_button = ttk.Button(
            frame,
            text="Open File",
            command=self.open_file,
            style="Racing.TButton",
            state="disabled"  # Initially disabled until the app is running
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

    def open_dashboard(self):
        """Open the dashboard viewer in a web browser."""
        webbrowser.open(f'http://localhost:{self.port_str}', new=2)

    def open_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.console_app.log(f"Selected file: {file_path}")
            if self.process:
                self.process.stdin.write(file_path + '\n')
                self.process.stdin.flush()

                ipc_client = IpcParent(self.ipc_port)
                rsp = ipc_client.request("open-file", {"file-path": file_path})
                if rsp["status"] != "error":
                    self.console_app.log("File path sent successfully.")
                else:
                    self.console_app.log(f"Error sending file path: {rsp['message']}")
                    messagebox.showerror("File open error", "\n".join([rsp["message"]]))
            else:
                self.console_app.log("No process running to send the file path to.")

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the sub-application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """
        # Implementation of handling settings changes
        self.console_app.log(f"Settings changed for {self.display_name}")
        should_restart = self.port_str != str(new_settings.Network.save_viewer_port)

        # Update the args with the new port
        self.port_str = str(new_settings.Network.save_viewer_port)
        self.args = ["--launcher", "--port", self.port_str] + self.extra_args
        self.console_app.log(f"Updated args: {self.args}")

        return should_restart

    def post_start(self):
        """Update buttons after app start"""
        self.start_stop_button.config(text="Stop")
        self.start_stop_button.config(state="normal")
        self.open_file_button.config(state="normal")
        self.open_dashboard_button.config(state="normal")

    def post_stop(self):
        """Update buttons after app stop"""
        self.start_stop_button.config(text="Start")
        self.start_stop_button.config(state="normal")
        self.open_file_button.config(state="disabled")
        self.open_dashboard_button.config(state="disabled")

    def start_stop_callback(self):
        """Start or stop the backend application."""
        # disable the button. enable in post_start/post_stop
        self.start_stop_button.config(state="disabled")
        try:
            # Call the start_stop method
            self.start_stop()
        except Exception as e: # pylint: disable=broad-exception-caught
            # Log the error or handle it as needed
            self.console_app.log(f"{self.display_name}:Error during start/stop: {e}")
        finally:
            # Re-enable the button regardless of whether an error occurred
            self.start_stop_button.config(state="normal")
