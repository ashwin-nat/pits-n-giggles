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

from lib.ipc import IpcSubscriber
from ..ui.infra import OverlaysMgr

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class HudClient(IpcSubscriber):
    """Socket.IO client to receive HUD data updates."""
    def __init__(self, port: int, logger: logging.Logger, overlays_mgr: OverlaysMgr):
        """Args:
            port: Port number of the Socket.IO server.
            logger: Logger instance.
        """
        url = f"http://localhost:{port}"
        super().__init__(url, logger, msg_packed=True)
        self.m_overlays_mgr = overlays_mgr

        # optional connect/disconnect hooks
        @self.on_connect
        def connected():
            """Post connection callback."""
            self._log(logging.INFO, "[HudClient] Connected")
            self._sio.emit('register-client', {
                'type': 'hud',
                'id': 'hud-mgr',
            })

        @self.on_disconnect
        def disconnected():
            """Post disconnection callback."""
            self._log(logging.INFO, "[HudClient] Disconnected")

        # custom event handler
        @self.on('race-table-update')
        def handle_race_table(data):
            """Race table data update handler."""
            self.m_overlays_mgr.race_table_update(data)

        @self.on('hud-toggle-notification')
        def handle_hud_toggle_notification(_data):
            """HUD toggle notification handler."""
            self.logger.debug(f"[HudClient] Received HUD toggle notification: {_data}")
            self.m_overlays_mgr.toggle_overlays_visibility()

        @self.on('hud-cycle-mfd-notification')
        def handle_hud_cycle_mfd_notification(_data):
            """Cycle MFD notification handler."""
            self.logger.debug(f"[HudClient] Received Cycle MFD notification: {_data}")
            self.m_overlays_mgr.next_page()

        @self.on('stream-overlay-update')
        def handle_stream_overlay_update(data):
            """Stream overlay data update handler."""
            self.m_overlays_mgr.stream_overlays_update(data)
