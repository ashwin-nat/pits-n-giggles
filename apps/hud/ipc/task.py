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

from lib.child_proc_mgmt import report_ipc_port_from_child
from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.ipc import IpcServerSyncRouter, IpcSubscriberSync

from ..listener import HudClient
from ..ui.infra import OverlaysMgr
from .handlers import (handle_lock_widgets, handle_mfd_interact,
                       handle_next_page, handle_prev_page, handle_set_opacity,
                       handle_get_stats,
                       handle_set_overlays_layout,
                       handle_set_track_radar_idle_opacity,
                       handle_set_ui_scale, handle_toggle_visibility)

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
    ipc_server = IpcServerSyncRouter(
        # port=port,
        name="hud"
    )
    report_ipc_port_from_child(ipc_server.port)
    logger.debug("Started IPC server on port %d", ipc_server.port)
    _register_routes(
        ipc_server=ipc_server,
        logger=logger,
        overlays_mgr=overlays_mgr,
        socketio_client=socketio_client,
        ipc_sub=ipc_sub,
    )
    return ipc_server.serve_in_thread()

def _register_routes(
        ipc_server: IpcServerSyncRouter,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        socketio_client: HudClient,
        ipc_sub: IpcSubscriberSync,
        ) -> None:
    """Register all IPC routes using decorator-style handlers."""

    @ipc_server.on("lock-widgets")
    def _lock_widgets(args: dict) -> dict:
        return handle_lock_widgets(args, logger, overlays_mgr)

    @ipc_server.on("toggle-overlays-visibility")
    def _toggle_visibility(args: dict) -> dict:
        return handle_toggle_visibility(args, logger, overlays_mgr)

    @ipc_server.on("set-overlays-opacity")
    def _set_opacity(args: dict) -> dict:
        return handle_set_opacity(args, logger, overlays_mgr)

    @ipc_server.on("next-page")
    def _next_page(args: dict) -> dict:
        return handle_next_page(args, logger, overlays_mgr)

    @ipc_server.on("prev-page")
    def _prev_page(args: dict) -> dict:
        return handle_prev_page(args, logger, overlays_mgr)

    @ipc_server.on("mfd-interact")
    def _mfd_interact(args: dict) -> dict:
        return handle_mfd_interact(args, logger, overlays_mgr)

    @ipc_server.on("set-overlays-layout")
    def _set_overlays_layout(args: dict) -> dict:
        return handle_set_overlays_layout(args, logger, overlays_mgr)

    @ipc_server.on("set-ui-scale")
    def _set_ui_scale(args: dict) -> dict:
        return handle_set_ui_scale(args, logger, overlays_mgr)

    @ipc_server.on("set-track-radar-idle-opacity")
    def _set_track_radar_idle_opacity(args: dict) -> dict:
        return handle_set_track_radar_idle_opacity(args, logger, overlays_mgr)

    @ipc_server.on("get-stats")
    def _get_stats(args: dict) -> dict:
        return handle_get_stats(args, logger, overlays_mgr)

    @ipc_server.on_shutdown
    def _shutdown(args: dict) -> dict:
        return _shutdown_handler(
            args,
            logger=logger,
            overlays_mgr=overlays_mgr,
            socketio_client=socketio_client,
            ipc_sub=ipc_sub,
        )

    @ipc_server.on_heartbeat_missed
    def _heartbeat_missed(count: int) -> None:
        _handle_heartbeat_missed(count, logger=logger)

def _shutdown_handler(
        args: dict,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        socketio_client: HudClient,
        ipc_sub: IpcSubscriberSync
        ) -> dict:
    """Handles shutdown command.

    Args:
        args (dict): IPC message
        logger (logging.Logger): Logger
        overlays_mgr (OverlaysMgr): Overlays manager
        socketio_client (HudClient): Receiver client obj
        ipc_sub (PngShmReader): Shared memory reader
    """

    logger.debug("In shutdown handler")
    threading.Thread(target=_stop_other_tasks, args=(args, logger, overlays_mgr, socketio_client, ipc_sub,),
                     name="Shutdown tasks").start()
    return {
        "status": "success",
        "message": "Shutting down HUD manager",
    }

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

def _handle_heartbeat_missed(count: int, logger: logging.Logger) -> None:
    """Handle terminate command"""

    logger.error("Missed heartbeat %d times. This process has probably been orphaned. Terminating...", count)
    os._exit(PNG_LOST_CONN_TO_PARENT)
