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
import sys
from tkinter import ttk

from lib.button_debouncer import ButtonDebouncer
from lib.config import PngSettings
from lib.ipc import IpcParent

from ..console_interface import ConsoleInterface
from .base_mgr import PngAppMgrBase

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class HudAppMgr(PngAppMgrBase):
    """Implementation of PngApp for save viewer"""
    def __init__(self, console_app: ConsoleInterface, settings: PngSettings, args: list[str], debug_mode: bool):
        """Initialize the save viewer manager
        :param console_app: Reference to a console interface for logging
        :param settings: Settings object
        :param args: Command line arguments to pass to the save viewer subsystem
        :param debug_mode: Whether to run the save viewer in debug mode
        """
        self.port = settings.Network.save_viewer_port
        self.supported = (sys.platform == "win32") # Only supported on Windows
        self.enabled = settings.HUD.enabled
        self.args = args + ["--debug"] if debug_mode else (args or [])
        self.locked = True # HUD starts locked by default
        self.debouncer = ButtonDebouncer(debounce_time=1.5)
        super().__init__(
            port_conflict_settings_field='Network -> "Pits n\' Giggles HUD Manager"',
            module_path="apps.hud",
            display_name="HUD",
            start_by_default=(self.supported and self.enabled),
            console_app=console_app,
            settings=settings,
            args=self.args,
            debug_mode=debug_mode
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
        self.ping_button = ttk.Button(
            frame,
            text="Hide/Show",
            command=self.hide_show_callback,
            style="Racing.TButton",
            state="disabled"  # Initially disabled until the app is running
        )
        self.lock_button = ttk.Button(
            frame,
            text="Unlock",
            command=self.lock_callback,
            style="Racing.TButton",
            state="disabled"  # Initially disabled until the app is running
        )

        return [
            self.start_stop_button,
            self.ping_button,
            self.lock_button,
        ]

    def hide_show_callback(self):
        """Open the dashboard viewer in a web browser."""
        self.console_app.info_log("Sending hide/show command to HUD...")
        rsp = IpcParent(self.ipc_port).request(
            command="toggle-overlays-visibility", args={}
        )
        self.console_app.info_log(str(rsp))

    def lock_callback(self):
        """Lock or unlock the HUD from receiving data."""
        if not self.debouncer.onButtonPress("lock_button"):
            self.console_app.debug_log("Lock button press debounced.")
            return

        self.console_app.debug_log("Toggling HUD lock state...")
        self.lock_button.config(state="disabled")
        rsp = IpcParent(self.ipc_port).request(command="lock-widgets", args={
            "old-value": self.locked,
            "new-value": not self.locked,
        })
        self.locked = not self.locked
        self.console_app.info_log(str(rsp))

        self.lock_button.config(state="normal")
        status = rsp.get("status", None)
        if status is not None:
            self.set_lock_button_text()
        else:
            self.console_app.error_log("Failed to toggle lock state.")

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the backend application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """

        diff = self.curr_settings.diff(new_settings, {
            "HUD": [
                "enabled",
                "show_lap_timer",
                "show_timing_tower",
            ],
        })
        self.console_app.debug_log(f"{self.display_name} Settings changed: {json.dumps(diff, indent=2)}")
        has_changed = bool(diff)
        if has_changed:
            self.enabled = new_settings.HUD.enabled
        return has_changed

    def start(self):
        """Check for enabled flag before starting"""
        if not self.enabled:
            self.console_app.debug_log(f"{self.display_name} is not enabled.")
            self.status_var.set("Disabled")
            return

        # Run the standard start
        super().start()

    def post_start(self):
        """Update buttons after app start"""
        self.ping_button.config(state="normal")
        self.start_stop_button.config(text="Stop")
        self.start_stop_button.config(state="normal")
        self.lock_button.config(state="normal")

    def post_stop(self):
        """Update buttons after app stop"""
        self.ping_button.config(state="disabled")
        self.start_stop_button.config(text="Start")
        self.start_stop_button.config(state="normal")
        self.lock_button.config(state="disabled")

    def start_stop_callback(self):
        """Start or stop the backend application."""
        # disable the button. enable in post_start/post_stop
        self.ping_button.config(state="disabled")
        self.start_stop_button.config(state="disabled")
        self.lock_button.config(state="disabled")
        try:
            # Call the start_stop method
            self.start_stop()
        except Exception as e: # pylint: disable=broad-exception-caught
            # Log the error or handle it as needed
            self.console_app.debug_log(f"{self.display_name}:Error during start/stop: {e}")
            # If no exception, it will be handled in post_start/post_stop
            self.ping_button.config(state="normal")
            self.start_stop_button.config(state="normal")
            self.lock_button.config(state="normal")

    def set_lock_button_text(self):
        if self.locked:
            self.lock_button.config(text="Unlock")
        else:
            self.lock_button.config(text="Lock")

    def process_enabled_change(self):
        """
        Process the enabled state change and update the GUI accordingly.

        If the application is enabled, start the backend application,
        enable the start/stop button, update the lock button text and
        enable the ping button. If the application is disabled, stop
        the backend application, disable the start/stop button and
        disable the ping and lock buttons.
        """

        if self.enabled:
            self.start()
            self.start_stop_button.config(state="normal")
            self.set_lock_button_text()
            self.ping_button.config(state="normal")
        else:
            self.stop()
            self.start_stop_button.config(state="disabled")
            self.ping_button.config(state="disabled")
            self.lock_button.config(state="disabled")
