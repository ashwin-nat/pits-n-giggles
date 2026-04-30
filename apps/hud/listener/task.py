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

from lib.ipc import IpcDealerClient, IpcSubscriberSync, PngAppId

from ..ui.infra import OverlaysMgr

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def run_hud_update_threads(
        router_port: int,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        xpub_port: int
        ) -> Tuple[IpcDealerClient, IpcSubscriberSync]:
    """Creates, runs and returns the HUD update thread.

    Args:
        router_port: Port number of the ZeroMQ ROUTER socket on the broker.
        logger: Logger instance.
        overlays_mgr: Overlays manager
        xpub_port: IPC xpub port

    Returns:
        A tuple of the IPC dealer client and the IPC subscriber instances.
    """
    return _run_dealer_thread(router_port, logger, overlays_mgr), \
            _run_ipc_sub_thread(logger, overlays_mgr, xpub_port)

def _run_dealer_thread(
        router_port: int,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr
        ) -> IpcDealerClient:
    """Start the ZeroMQ DEALER client thread for HUD button-press commands.

    Args:
        router_port: Port of the broker ROUTER socket.
        logger: Logger instance.
        overlays_mgr: Overlays manager

    Returns:
        The IpcDealerClient instance.
    """
    dealer_client = IpcDealerClient(
        host="127.0.0.1",
        port=router_port,
        identity=str(PngAppId.HUD),
        logger=logger,
    )

    @dealer_client.route("hud-toggle-notification")
    def _(data):
        oid = data.get("message", {}).get("oid") if isinstance(data, dict) else None
        overlays_mgr.toggle_overlays_visibility(oid)

    @dealer_client.route("hud-cycle-mfd-notification")
    def _(_data):
        overlays_mgr.next_page()

    @dealer_client.route("hud-prev-page-mfd-notification")
    def _(_data):
        overlays_mgr.prev_page()

    @dealer_client.route("hud-mfd-interaction-notification")
    def _(_data):
        overlays_mgr.mfd_interact()

    threading.Thread(target=dealer_client.start, daemon=True, name="HUD Dealer").start()
    return dealer_client

def _run_ipc_sub_thread(
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        xpub_port: int
        ) -> IpcSubscriberSync:
    """Thread target to run the shared memory listener for HUD updates.

    Args:
        logger: Logger instance.
        overlays_mgr: Overlays manager
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
