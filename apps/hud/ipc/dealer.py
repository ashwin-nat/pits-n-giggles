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

"""Router/dealer routes - button-press notifications pushed by the backend."""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from lib.ipc import IpcDealerClient

from ..ui.infra import OverlaysMgr

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def register_dealer_routes(
        dealer: IpcDealerClient,
        overlays_mgr: OverlaysMgr) -> None:
    """Register the notifications the backend fires when a mapped button is pressed.

    Args:
        dealer (IpcDealerClient): Router/dealer client, built by the subsystem base
        overlays_mgr (OverlaysMgr): Overlays manager
    """

    @dealer.route("hud-toggle-notification")
    def _toggle_notification(data: dict, _sender: str) -> None:
        oid = data.get("message", {}).get("oid") if isinstance(data, dict) else None
        overlays_mgr.toggle_overlays_visibility(oid)

    @dealer.route("hud-cycle-mfd-notification")
    def _cycle_mfd_notification(_data: dict, _sender: str) -> None:
        overlays_mgr.next_page()

    @dealer.route("hud-prev-page-mfd-notification")
    def _prev_page_notification(_data: dict, _sender: str) -> None:
        overlays_mgr.prev_page()

    @dealer.route("hud-mfd-interaction-notification")
    def _mfd_interaction_notification(_data: dict, _sender: str) -> None:
        overlays_mgr.mfd_interact()

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "register_dealer_routes",
]
