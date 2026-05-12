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
from typing import List

from PySide6.QtWidgets import QPushButton

from lib.config import PngSettings
from lib.error_status import PNG_ERROR_CODE_HTTP_PORT_IN_USE

from .base_mgr import ExitReason, PngAppMgrBase, PngAppMgrConfig

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class HttpServerAppMgr(PngAppMgrBase):
    """Launcher subsystem manager for the HTTP/Socket.IO server process."""

    MODULE_PATH = "apps.http_server"
    DISPLAY_NAME = "HTTP Server"
    SHORT_NAME = "HTTP"

    SHOULD_DISPLAY = False

    def __init__(self, common_cfg: PngAppMgrConfig):
        extra_args = ["--run-ipc-server"]
        if common_cfg.debug_mode:
            extra_args.append("--debug")

        config = replace(
            common_cfg,
            args=common_cfg.args + extra_args,
            post_start_cb=self.post_start,
            post_stop_cb=self.post_stop,
        )
        super().__init__(config=config)

        self.register_exit_reason(PNG_ERROR_CODE_HTTP_PORT_IN_USE, ExitReason(
            code=PNG_ERROR_CODE_HTTP_PORT_IN_USE,
            status="HTTP Port Conflict",
            title="HTTP port in use",
            message="The HTTP port is already in use by another process. Please close the other process and try again or change the port.",
            can_restart=False,
            settings_field='Network -> "Pits n\' Giggles HTTP Server Port"'
        ))

    def get_buttons(self) -> List[QPushButton]:
        return []

    def post_start(self):
        pass

    def post_stop(self):
        pass

    def on_settings_change(self, new_settings: PngSettings) -> bool:
        diff = self.curr_settings.diff(new_settings, {
            "Network": [
                "server_port",
                "bind_address",
                "broker_xsub_port",
                "broker_router_port",
            ],
            "HTTPS": [],
            "Display": [],
        })
        self.debug_log(f"{self.DISPLAY_NAME} Settings changed: {diff}")
        return bool(diff)
