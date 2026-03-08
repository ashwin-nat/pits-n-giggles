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
from typing import Dict

from ..ui.infra import OverlaysMgr

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def handle_lock_widgets(args: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'lock-widgets' IPC command to lock or unlock HUD widgets.

    Args:
        args (dict): IPC command message args
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.debug("Received lock-widgets command")
    return overlays_mgr.on_locked_state_change(args)

def handle_toggle_visibility(args: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'toggle-visibility' IPC command to show or hide HUD widgets.

    Args:
        args (dict): IPC command message args
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.debug("Received toggle-visibility command. args: %s", args)
    overlays_mgr.toggle_overlays_visibility()
    return {"status": "success", "message": "toggle-visibility handler executed."}

def handle_set_opacity(args: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'set-opacity' IPC command to set HUD widgets opacity.

    Args:
        args (dict): IPC command message args
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.debug("Received set-opacity command. args: %s", args)

    if opacity := args.get("opacity"):
        overlays_mgr.set_overlays_opacity(opacity)
        return {"status": "success", "message": "set-opacity handler executed."}

    return {"status": "error", "message": "Missing opacity value in set-opacity command."}

def handle_next_page(args: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'next-page' IPC command to show next page of HUD widgets.

    Args:
        args (dict): IPC command message args
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.info("Received next-page command. args: %s", args)

    overlays_mgr.next_page()
    return {"status": "success", "message": "next-page handler executed."}

def handle_prev_page(args: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'prev-page' IPC command to show previous page of HUD widgets.

    Args:
        args (dict): IPC command message args
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.info("Received prev-page command. args: %s", args)

    overlays_mgr.prev_page()
    return {"status": "success", "message": "prev-page handler executed."}

def handle_mfd_interact(args: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'mfd-interact' IPC command to show next page of HUD widgets.

    Args:
        args (dict): IPC command message args
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.info("Received mfd-interact command. args: %s", args)

    overlays_mgr.mfd_interact()
    return {"status": "success", "message": "mfd-interact handler executed."}

def handle_set_overlays_layout(args: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'reset-overlays' IPC command to reset HUD widgets.

    Args:
        args (dict): IPC command message args
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.debug("Received reset-overlays command. args: %s", args)
    if not args:
        return {"status": "error", "message": "Missing args in set-overlays-layout command."}

    layout: Dict[str, Dict[str, int]] = args.get("layout")
    if not layout:
        return {"status": "error", "message": "Missing layout in set-overlays-layout command."}

    return overlays_mgr.set_overlays_layout(layout)

def handle_set_ui_scale(args: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'set-ui-scale' IPC command to set HUD widgets UI scale.

    Args:
        args (dict): IPC command msg args
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.debug("Received set-ui-scale command. args: %s", args)

    oid = args.get('oid')
    if not oid:
        return {"status": "error", "message": "Missing overlay id in set-ui-scale command."}

    scale_factor = args.get('scale_factor')
    if not scale_factor:
        return {"status": "error", "message": "Missing scale_factor in set-ui-scale command."}

    try:
        overlays_mgr.set_scale_factor(oid, scale_factor)
        return {"status": "success", "message": "set-ui-scale handler executed."}
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.exception(f"Error handling set-ui-scale command: {e}")
        return {"status": "error", "message": f"Exception during set-ui-scale handling: {str(e)}"}

def handle_set_track_radar_idle_opacity(args: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'set-track-radar-idle-opacity' IPC command to set HUD widgets opacity.

    Args:
        args (dict): IPC command message args
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.debug("Received set-track-radar-idle-opacity command. args: %s", args)

    opacity = args.get("opacity")
    if opacity is not None:
        overlays_mgr.set_track_radar_idle_opacity(opacity)
        return {"status": "success", "message": "set-track-radar-idle-opacity handler executed."}
    return {"status": "error", "message": "Missing opacity value in set-track-radar-idle-opacity command."}

def handle_get_stats(_args: dict, _logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'get-stats' IPC command."""
    return {
        "status": "success",
        "stats": overlays_mgr.get_stats(),
    }
