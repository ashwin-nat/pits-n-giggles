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

from typing import TYPE_CHECKING, List

from PySide6.QtWidgets import QPushButton

from lib.config import PngSettings

from .base_mgr import PngAppMgrBase

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BrokerAppMgr(PngAppMgrBase):
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
        super().__init__(
            window=window,
            module_path="apps.broker",
            display_name="Pit Wall",
            short_name="WALL",
            settings=settings,
            start_by_default=True,
            should_display=False,
            args=temp_args,
            debug_mode=debug_mode,
            coverage_enabled=coverage_enabled,
            post_start_cb=self.post_start,
            post_stop_cb=self.post_stop
        )

    def get_buttons(self) -> List[QPushButton]:
        """Return a list of button objects directly
        :return: List of button objects
        """

        # Button for trouble shooting only
        self.start_stop_button = self.build_button(self.get_icon("start"), self.start_stop_callback, "Start")
        return [
            self.start_stop_button
        ]

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        """Handle changes in settings for the backend application

        :param new_settings: New settings

        :return: True if the app needs to be restarted
        """

        diff = self.curr_settings.diff(new_settings, {
            "Network": [
                "broker_xpub_port",
                "broker_xsub_port",
            ],
        })
        self.debug_log(f"{self.display_name} Settings changed: {diff}")
        # Update the port number
        should_restart = bool(diff)
        return should_restart

    def post_start(self):
        """Update buttons after app start"""
        if not self.should_display:
            return

        self.set_button_icon(self.start_stop_button, self.get_icon("stop"))
        self.set_button_tooltip(self.start_stop_button, "Stop")
        self.set_button_state(self.start_stop_button, True)

    def post_stop(self):
        """Update buttons after app stop"""
        if not self.should_display:
            return

        self.set_button_icon(self.start_stop_button, self.get_icon("start"))
        self.set_button_tooltip(self.start_stop_button, "Start")
        self.set_button_state(self.start_stop_button, True)

    def start_stop_callback(self):
        """Start or stop the backend application."""
        if not self.should_display:
            return

        # disable the button. enable in post_start/post_stop
        self.set_button_state(self.start_stop_button, False)
        try:
            # Call the start_stop method
            self.start_stop("Button pressed")
        except Exception as e: # pylint: disable=broad-exception-caught
            # Log the error or handle it as needed
            self.debug_log(f"{self.display_name}:Error during start/stop: {e}")
            # If no exception, it will be handled in post_start/post_stop
            self.set_button_state(self.start_stop_button, True)
