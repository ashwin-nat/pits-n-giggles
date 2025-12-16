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
from typing import Tuple

from lib.ipc import IpcSubscriberSync

from ..ui.infra import OverlaysMgr
from .client import HudClient

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def run_hud_update_threads(
        port: int,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        low_freq_update_interval_ms: int,
        xpub_port: int
        ) -> Tuple[HudClient, IpcSubscriberSync]:
    """Creates, runs and returns the HUD update thread.

    Args:
        port: Port number of the Socket.IO server.
        logger: Logger instance.
        overlays_mgr: Overlays manager
        low_freq_update_interval_ms: Low frequency update interval
        xpub_port: IPC xpub port

    Returns:
        A tuple of the Socket.IO client and the IPC subscriber instances.
    """
    return _run_socketio_thread(port, logger, overlays_mgr), \
            _run_ipc_sub_thread(logger, overlays_mgr, low_freq_update_interval_ms, xpub_port)

def _run_socketio_thread(
        port: int,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr
        ) -> HudClient:
    """Thread target to run the Socket.IO listener for HUD updates.

    Args:
        port: Port number of the Socket.IO server.
        logger: Logger instance.
        overlays_mgr: Overlays manager

    Returns:
        The Socket.IO client instance.
    """
    client = HudClient(port, logger, overlays_mgr)
    threading.Thread(target=client.run, daemon=True, name="Socket.IO listener").start()
    return client

def _run_ipc_sub_thread(
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        low_freq_update_interval_ms: int,
        xpub_port: int
        ) -> IpcSubscriberSync:
    """Thread target to run the shared memory listener for HUD updates.

    Args:
        logger: Logger instance.
        overlays_mgr: Overlays manager
        low_freq_update_interval_ms: Low frequency update interval
        xpub_port: IPC xpub port

    Returns:
        The IPC subscriber instance.
    """

    ipc_sub = IpcSubscriberSync(port=xpub_port, logger=logger)

    @ipc_sub.route("race-table-update")
    def _handle_race_table_update(data):
        """Race table data update handler."""
        overlays_mgr.race_table_update(data)

    @ipc_sub.route("stream-overlay-update")
    def _handle_stream_overlay_update(data):
        """Stream overlay data update handler."""
        overlays_mgr.stream_overlays_update(data)

    threading.Thread(target=ipc_sub.start, daemon=True, name="IPC Subscriber").start()
    return ipc_sub
