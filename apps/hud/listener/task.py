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

from lib.ipc import PngShmReader

from ..ui.infra import OverlaysMgr
from .client import HudClient

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def run_hud_update_threads(
        port: int,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        shm_read_interval_ms: int
        ) -> HudClient:
    """Creates, runs and returns the HUD update thread.

    Args:
        port: Port number of the Socket.IO server.
        logger: Logger instance.
        overlays_mgr: Overlays manager
        shm_read_interval_ms: Shared memory read interval

    Returns:
        HudClient - the incoming data receiver client obj
    """
    return _run_socketio_thread(port, logger, overlays_mgr), _run_shm_thread(logger, overlays_mgr, shm_read_interval_ms)

def _run_socketio_thread(
        port: int,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr
        ) -> None:
    """Thread target to run the Socket.IO listener for HUD updates.

    Args:
        port: Port number of the Socket.IO server.
        logger: Logger instance.
        overlays_mgr: Overlays manager
    """
    client = HudClient(port, logger, overlays_mgr)
    threading.Thread(target=client.run, daemon=True, name="Socket.IO listener").start()
    return client

def _run_shm_thread(
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        shm_read_interval_ms: int
        ) -> None:
    """Thread target to run the shared memory listener for HUD updates.

    Args:
        logger: Logger instance.
        overlays_mgr: Overlays manager
        shm_read_interval_ms: Shared memory read interval
    """
    shm = PngShmReader(logger, read_interval_ms=shm_read_interval_ms)

    @shm.on("race-table-update")
    def _handle_race_table_update(data):
        """Race table data update handler."""
        overlays_mgr.race_table_update(data)

    @shm.on("stream-overlay-update")
    def _handle_stream_overlay_update(data):
        """Stream overlay data update handler."""
        overlays_mgr.stream_overlays_update(data)

    threading.Thread(target=shm.read, daemon=True, name="SHM listener").start()
    return shm
