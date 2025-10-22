# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

import logging
import threading

from lib.ipc import IpcSubscriber
from ..ui.infra import WindowManager

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class HudClient(IpcSubscriber):
    """Socket.IO client to receive HUD data updates."""
    def __init__(self, port: int, logger: logging.Logger, window_manager: WindowManager, stop_event: threading.Event):
        """Args:
            port: Port number of the Socket.IO server.
            logger: Logger instance.
            stop_event: Event to signal stopping.
        """
        url = f"http://localhost:{port}"
        super().__init__(url, logger, stop_event, msg_packed=True)
        self.m_window_manager = window_manager

        # optional connect/disconnect hooks
        @self.on_connect
        def connected():
            """Post connection callback."""
            self._log(logging.INFO, "[RaceTableClient] Connected")
            self._sio.emit('register-client', {
                'type': 'race-table',
                'id': 'race-table-client',
            })

        @self.on_disconnect
        def disconnected():
            """Post disconnection callback."""
            self._log(logging.INFO, "[RaceTableClient] Disconnected")

        # custom event handler
        @self.on('race-table-update')
        def handle_race_table(data):
            """Race table data update handler."""
            self._log(logging.INFO, "[RaceTableClient] Received race-table-update")
            self.m_window_manager.race_table_update(data)
