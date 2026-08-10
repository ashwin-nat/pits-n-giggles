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

from dataclasses import replace
from typing import TYPE_CHECKING, List

from PySide6.QtWidgets import QPushButton

from lib.error_status import PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE
from lib.ipc import IpcClientSync

from ..base_mgr import ExitReason, PngAppMgrConfig
from .settings_change import BackendSettingsChangeBase

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BackendAppMgr(BackendSettingsChangeBase):
    """Implementation of PngApp for backend services"""

    MODULE_PATH = "apps.backend"
    DISPLAY_NAME = "Core"
    SHORT_NAME = "CORE"

    def __init__(self,
                 common_cfg: PngAppMgrConfig,
                 replay_server: bool):
        """Initialize the backend manager
        :param common_cfg: Common configuration for the backend app manager
        :param replay_server: Whether to run the replay server
        """

        extra_args = []
        extra_args.append("--run-ipc-server")
        if common_cfg.debug_mode:
            extra_args.append("--debug")
        if replay_server:
            extra_args.append("--replay-server")
        final_args = [*common_cfg.args, *extra_args]

        config = replace(common_cfg,
                         args=final_args,
                         post_start_cb=self.post_start,
                         post_stop_cb=self.post_stop
        )

        super().__init__(
            config=config,
        )
        self.register_exit_reason(PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE, ExitReason(
            code=PNG_ERROR_CODE_UDP_TELEMETRY_PORT_IN_USE,
            status="UDP Port Conflict",
            title="UDP port in use",
            message="The UDP port is already in use by another process. Please close the other process and try again or change the port.",
            can_restart=False,
            settings_field='Network -> "F1 UDP Telemetry Port"'
        ))

    def get_buttons(self) -> List[QPushButton]:
        """Return a list of button objects directly
        :return: List of button objects
        """

        self.start_stop_button = self.build_button(self.get_icon("start"), self.start_stop_callback, "Start")
        self.manual_save_button = self.build_button(self.get_icon("save"), self.manual_save, "Manual Save")

        return [
            self.start_stop_button,
            self.manual_save_button,
        ]

    def post_start(self):
        """Update buttons after app start"""
        self.set_button_icon(self.start_stop_button, self.get_icon("stop"))
        self.set_button_tooltip(self.start_stop_button, "Stop")
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.manual_save_button, True)

    def post_stop(self):
        """Update buttons after app stop"""
        self.set_button_icon(self.start_stop_button, self.get_icon("start"))
        self.set_button_tooltip(self.start_stop_button, "Start")
        self.set_button_state(self.start_stop_button, True)
        self.set_button_state(self.manual_save_button, False)

    def manual_save(self):
        """Send a manual save command to the backend."""
        self.debug_log("Sending manual save command to backend...")
        ipc_client = IpcClientSync(self.ipc_port)
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
        try:
            # Call the start_stop method
            self.start_stop("Stop button pressed")
        except Exception as e: # pylint: disable=broad-exception-caught
            # Log the error or handle it as needed
            self.debug_log(f"{self.DISPLAY_NAME}:Error during start/stop: {e}")
            # If no exception, it will be handled in post_start/post_stop
            self.set_button_state(self.start_stop_button, True)
