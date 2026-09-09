# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

"""Pub/sub routes - the broker telemetry the overlays render."""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from lib.ipc import IpcSubscriberSync

from ..ui.infra import OverlaysMgr

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def register_subscriber_routes(
        subscriber: IpcSubscriberSync,
        overlays_mgr: OverlaysMgr) -> None:
    """Register the broker topics the overlays render.

    Args:
        subscriber (IpcSubscriberSync): Broker subscriber, built by the subsystem base
        overlays_mgr (OverlaysMgr): Overlays manager
    """

    @subscriber.route("race-table-update")
    def _race_table_update(data: dict) -> None:
        overlays_mgr.race_table_update(data)

    @subscriber.route("stream-overlay-update")
    def _stream_overlay_update(data: dict) -> None:
        overlays_mgr.stream_overlays_update(data)
