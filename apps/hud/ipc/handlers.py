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

from pydantic import TypeAdapter, ValidationError, conint

from ..ui.infra import OverlaysMgr

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def handle_lock_widgets(msg: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'lock-widgets' IPC command to lock or unlock HUD widgets.

    Args:
        msg (dict): IPC command message
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.info("Received lock-widgets command. args: %s", msg)

    args = msg.get("args", {})
    if args:
        overlays_mgr.on_locked_state_change(args)
        return {"status": "success", "message": "lock-widgets handler executed."}
    return {"status": "error", "message": "Missing args in lock-widgets command."}

def handle_toggle_visibility(msg: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'toggle-visibility' IPC command to show or hide HUD widgets.

    Args:
        msg (dict): IPC command message
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.info("Received toggle-visibility command. args: %s", msg)

    overlays_mgr.toggle_overlays_visibility()
    return {"status": "success", "message": "toggle-visibility handler executed."}

def handle_set_opacity(msg: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'set-opacity' IPC command to set HUD widgets opacity.

    Args:
        msg (dict): IPC command message
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.info("Received set-opacity command. args: %s", msg)

    args = msg.get("args", {})
    if opacity := args.get("opacity"):
        overlays_mgr.set_overlays_opacity(opacity)
        return {"status": "success", "message": "set-opacity handler executed."}
    return {"status": "error", "message": "Missing opacity value in set-opacity command."}

def handle_next_page(msg: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'next-page' IPC command to show next page of HUD widgets.

    Args:
        msg (dict): IPC command message
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.info("Received next-page command. args: %s", msg)

    overlays_mgr.next_page()
    return {"status": "success", "message": "next-page handler executed."}

def handle_reset_overlays(msg: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'reset-overlays' IPC command to reset HUD widgets.

    Args:
        msg (dict): IPC command message
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.info("Received reset-overlays command. args: %s", msg)
    overlays_mgr.reset_overlays()
    return {"status": "success", "message": "reset-overlays handler executed."}

def handle_set_ui_scale(msg: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handle the 'set-ui-scale' IPC command to set HUD widgets UI scale.

    Args:
        args (dict): IPC command msg
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """

    logger.info("Received set-ui-scale command. args: %s", msg)
    args = msg.get("args", {})

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
