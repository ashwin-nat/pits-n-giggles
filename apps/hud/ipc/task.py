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
import os
import threading
from functools import partial
from typing import Callable, Dict

from lib.child_proc_mgmt import report_ipc_port_from_child
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.ipc import IpcServerSync, IpcSubscriberSync

from ..listener import HudClient
from ..ui.infra import OverlaysMgr
from .handlers import (handle_lock_widgets, handle_mfd_interact,
                       handle_next_page, handle_prev_page, handle_set_opacity,
                       handle_set_overlays_layout,
                       handle_set_track_radar_idle_opacity,
                       handle_set_ui_scale, handle_toggle_visibility)

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Define a type for handler functions
CommandHandler = Callable[[dict, logging.Logger, OverlaysMgr], dict]

# Registry of command handlers
COMMAND_HANDLERS: Dict[str, CommandHandler] = {
    "lock-widgets": handle_lock_widgets,
    "toggle-overlays-visibility": handle_toggle_visibility,
    "set-overlays-opacity": handle_set_opacity,
    "next-page": handle_next_page,
    "prev-page": handle_prev_page,
    "mfd-interact": handle_mfd_interact,
    "set-overlays-layout": handle_set_overlays_layout,
    "set-ui-scale": handle_set_ui_scale,
    "set-track-radar-idle-opacity": handle_set_track_radar_idle_opacity,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def run_ipc_task(
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        socketio_client: HudClient,
        ipc_sub: IpcSubscriberSync
        ) -> threading.Thread:
    """Runs the IPC task.

    Args:
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager
        socketio_client (HudClient): Receiver client
        ipc_sub (IpcSubscriberSync): IPC subscriber

    Returns:
        threading.Thread: IPC thread handle
    """
    logger.debug("Starting IPC server")
    ipc_server = IpcServerSync(
        # port=port,
        name="hud"
    )
    report_ipc_port_from_child(ipc_server.port)
    logger.debug("Started IPC server on port %d", ipc_server.port)
    ipc_server.register_shutdown_callback(partial(
        _shutdown_handler, logger=logger, overlays_mgr=overlays_mgr, socketio_client=socketio_client,
        shm_reader=ipc_sub))
    ipc_server.register_heartbeat_missed_callback(partial(_handle_heartbeat_missed, logger=logger))
    return ipc_server.serve_in_thread(partial(_ipc_handler, logger=logger, overlays_mgr=overlays_mgr))

def _ipc_handler(msg: dict, logger: logging.Logger, overlays_mgr: OverlaysMgr) -> dict:
    """Handles incoming IPC messages and dispatches commands.

    Args:
        msg (dict): IPC message
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager

    Returns:
        dict: IPC response
    """
    logger.debug(f"Received IPC message: {msg}")

    if not (cmd := msg.get("cmd")):
        return {"status": "error", "message": "Missing command name"}

    if (handler := COMMAND_HANDLERS.get(cmd)):
        return handler(msg, logger, overlays_mgr)

    return {"status": "error", "message": f"Unknown command: {cmd}"}

def _shutdown_handler(
        args: dict, logger:
        logging.Logger,
        overlays_mgr: OverlaysMgr,
        socketio_client: HudClient,
        ipc_sub: IpcSubscriberSync
        ) -> None:
    """Handles shutdown command.

    Args:
        args (dict): IPC message
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager
        socketio_client (HudClient): Receiver client obj
        ipc_sub (PngShmReader): Shared memory reader
    """

    threading.Thread(target=_stop_other_tasks, args=(args, logger, overlays_mgr, socketio_client, ipc_sub,),
                     name="Shutdown tasks").start()
    return {"status": "success", "message": "Shutting down HUD manager"}

def _stop_other_tasks(
        args: dict,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        socketio_client: HudClient,
        ipc_sub: IpcSubscriberSync
        ) -> None:
    """Stop all other tasks when IPC shutdown is received.
    Args:
        args (dict): IPC message
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager
        socketio_client (HudClient): Receiver client
        ipc_sub (IpcSubscriberSync): IPC subscriber
    """
    reason = args.get("reason", "N/A")
    logger.info(f"Shutdown command received via IPC. Reason: {reason}. Stopping all tasks...")

    socketio_client.stop()
    ipc_sub.close()
    overlays_mgr.stop()

    logger.info("Exiting HUD subsystem")

def _handle_heartbeat_missed(count: int, logger: logging.Logger) -> dict:
    """Handle terminate command"""

    logger.error("Missed heartbeat %d times. This process has probably been orphaned. Terminating...", count)
    os._exit(PNG_LOST_CONN_TO_PARENT)
