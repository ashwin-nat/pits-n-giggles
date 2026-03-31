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
from lib.ipc import IpcServerSync, IpcSubscriberSync

from ..listener import HudClient
from ..ui.infra import OverlaysMgr

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
    _register_routes(
        ipc_server=ipc_server,
        logger=logger,
        overlays_mgr=overlays_mgr,
        socketio_client=socketio_client,
        ipc_sub=ipc_sub,
    )
    return ipc_server.serve_in_thread()

def _register_routes(
        ipc_server: IpcServerSync,
        logger: logging.Logger,
        overlays_mgr: OverlaysMgr,
        socketio_client: HudClient,
        ipc_sub: IpcSubscriberSync,
        ) -> None:
    """Register all IPC routes using decorator-style handlers."""

    @ipc_server.on("lock-widgets")
    def _lock_widgets(args: dict) -> dict:
        logger.debug("Received lock-widgets command")
        return overlays_mgr.on_locked_state_change(args)

    @ipc_server.on("toggle-overlays-visibility")
    def _toggle_visibility(args: dict) -> dict:
        logger.debug("Received toggle-visibility command. args: %s", args)
        overlays_mgr.toggle_overlays_visibility()
        return {"status": "success", "message": "toggle-visibility handler executed."}

    @ipc_server.on("set-overlays-opacity")
    def _set_opacity(args: dict) -> dict:
        logger.debug("Received set-opacity command. args: %s", args)

        if opacity := args.get("opacity"):
            overlays_mgr.set_overlays_opacity(opacity)
            return {"status": "success", "message": "set-opacity handler executed."}

        return {"status": "error", "message": "Missing opacity value in set-opacity command."}

    @ipc_server.on("next-page")
    def _next_page(args: dict) -> dict:
        logger.info("Received next-page command. args: %s", args)

        overlays_mgr.next_page()
        return {"status": "success", "message": "next-page handler executed."}

    @ipc_server.on("prev-page")
    def _prev_page(args: dict) -> dict:
        logger.info("Received prev-page command. args: %s", args)

        overlays_mgr.prev_page()
        return {"status": "success", "message": "prev-page handler executed."}

    @ipc_server.on("mfd-interact")
    def _mfd_interact(args: dict) -> dict:
        logger.info("Received mfd-interact command. args: %s", args)

        overlays_mgr.mfd_interact()
        return {"status": "success", "message": "mfd-interact handler executed."}

    @ipc_server.on("set-overlays-layout")
    def _set_overlays_layout(args: dict) -> dict:
        logger.debug("Received reset-overlays command. args: %s", args)
        if not args:
            return {"status": "error", "message": "Missing args in set-overlays-layout command."}

        layout: dict = args.get("layout")
        if not layout:
            return {"status": "error", "message": "Missing layout in set-overlays-layout command."}

        return overlays_mgr.set_overlays_layout(layout)

    @ipc_server.on("set-ui-scale")
    def _set_ui_scale(args: dict) -> dict:
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

    @ipc_server.on("set-track-radar-idle-opacity")
    def _set_track_radar_idle_opacity(args: dict) -> dict:
        logger.debug("Received set-track-radar-idle-opacity command. args: %s", args)

        opacity = args.get("opacity")
        if opacity is not None:
            overlays_mgr.set_track_radar_idle_opacity(opacity)
            return {"status": "success", "message": "set-track-radar-idle-opacity handler executed."}
        return {"status": "error", "message": "Missing opacity value in set-track-radar-idle-opacity command."}

    @ipc_server.on("set-circuit-info-length")
    def _set_circuit_info_length(args: dict) -> dict:
        logger.debug("Received set-circuit-info-length command. args: %s", args)

        length = args.get("length")
        if length is not None:
            overlays_mgr.set_circuit_info_length(length)
            return {"status": "success", "message": "set-circuit-info-length handler executed."}
        return {"status": "error", "message": "Missing length value in set-circuit-info-length command."}

    @ipc_server.on("get-stats")
    def _get_stats(_args: dict) -> dict:
        return {
            "status": "success",
            "stats": {
                "overlays": overlays_mgr.get_stats(),
                "ingress" : {
                    "socketio": socketio_client.get_stats(),
                    "subscriber": ipc_sub.get_stats(),
                }
            }
        }

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
