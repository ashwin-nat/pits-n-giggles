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

"""Management routes - the launcher's overlay control commands.

Shutdown, get-stats and heartbeat-missed are not here: those are owned by lib/subsystem, and
MgmtIpcHandle deliberately does not expose them.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import logging

from lib.subsystem import MgmtIpcHandle

from ..ui.infra import OverlaysMgr

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def register_mgmt_routes(
        mgmt: MgmtIpcHandle,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr) -> None:
    """Register the overlay control commands the launcher sends.

    Args:
        mgmt (MgmtIpcHandle): The subsystem's management IPC handle
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager
    """

    @mgmt.on("lock-widgets")
    def _lock_widgets(args: dict) -> dict:
        logger.debug("Received lock-widgets command")
        return overlays_mgr.on_locked_state_change(args)

    @mgmt.on("toggle-overlays-visibility")
    def _toggle_visibility(args: dict) -> dict:
        logger.debug("Received toggle-visibility command. args: %s", args)
        overlays_mgr.toggle_overlays_visibility()
        return {"status": "success", "message": "toggle-visibility handler executed."}

    @mgmt.on("set-overlays-opacity")
    def _set_opacity(args: dict) -> dict:
        logger.debug("Received set-opacity command. args: %s", args)

        if opacity := args.get("opacity"):
            overlays_mgr.set_overlays_opacity(opacity)
            return {"status": "success", "message": "set-opacity handler executed."}

        return {"status": "error", "message": "Missing opacity value in set-opacity command."}

    @mgmt.on("next-page")
    def _next_page(args: dict) -> dict:
        logger.info("Received next-page command. args: %s", args)

        overlays_mgr.next_page()
        return {"status": "success", "message": "next-page handler executed."}

    @mgmt.on("prev-page")
    def _prev_page(args: dict) -> dict:
        logger.info("Received prev-page command. args: %s", args)

        overlays_mgr.prev_page()
        return {"status": "success", "message": "prev-page handler executed."}

    @mgmt.on("mfd-interact")
    def _mfd_interact(args: dict) -> dict:
        logger.info("Received mfd-interact command. args: %s", args)

        overlays_mgr.mfd_interact()
        return {"status": "success", "message": "mfd-interact handler executed."}

    @mgmt.on("set-overlays-layout")
    def _set_overlays_layout(args: dict) -> dict:
        logger.debug("Received reset-overlays command. args: %s", args)
        if not args:
            return {"status": "error", "message": "Missing args in set-overlays-layout command."}

        layout: dict = args.get("layout")
        if not layout:
            return {"status": "error", "message": "Missing layout in set-overlays-layout command."}

        return overlays_mgr.set_overlays_layout(layout)

    @mgmt.on("set-track-radar-idle-opacity")
    def _set_track_radar_idle_opacity(args: dict) -> dict:
        logger.debug("Received set-track-radar-idle-opacity command. args: %s", args)

        opacity = args.get("opacity")
        if opacity is not None:
            overlays_mgr.set_track_radar_idle_opacity(opacity)
            return {"status": "success", "message": "set-track-radar-idle-opacity handler executed."}
        return {"status": "error", "message": "Missing opacity value in set-track-radar-idle-opacity command."}

    @mgmt.on("set-track-radar-range")
    def _set_track_radar_range(args: dict) -> dict:
        logger.debug("Received set-track-radar-range command. args: %s", args)

        range_m = args.get("range_m")
        if range_m is not None:
            overlays_mgr.set_track_radar_range(range_m)
            return {"status": "success", "message": "set-track-radar-range handler executed."}
        return {"status": "error", "message": "Missing range_m value in set-track-radar-range command."}

    @mgmt.on("set-circuit-info-length")
    def _set_circuit_info_length(args: dict) -> dict:
        logger.debug("Received set-circuit-info-length command. args: %s", args)

        length = args.get("length")
        if length is not None:
            overlays_mgr.set_circuit_info_length(length)
            return {"status": "success", "message": "set-circuit-info-length handler executed."}
        return {"status": "error", "message": "Missing length value in set-circuit-info-length command."}

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "register_mgmt_routes",
]
