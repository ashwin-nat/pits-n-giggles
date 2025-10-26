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
from functools import partial
from typing import Callable, Dict

from lib.ipc import IpcChildSync

from ..ui.infra import WindowManager
from .handlers import handle_lock_widgets

from ..listener import HudClient

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Define a type for handler functions
CommandHandler = Callable[[dict, logging.Logger, WindowManager], dict]

# Registry of command handlers
COMMAND_HANDLERS: Dict[str, CommandHandler] = {
    "lock-widgets": handle_lock_widgets,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def run_ipc_task(
        port: int, logger:
        logging.Logger,
        window_manager: WindowManager,
        receiver_client: HudClient
        ) -> threading.Thread:
    """Runs the IPC task.

    Args:
        port (int): IPC port
        logger (logging.Logger): Logger
        window_manager (WindowManager): WindowManager
        receiver_client (HudClient): Receiver client

    Returns:
        threading.Thread: IPC thread handle
    """
    ipc_server = IpcChildSync(
        port=port,
        name="hud"
    )
    ipc_server.register_shutdown_callback(partial(
        _shutdown_handler, logger=logger, window_manager=window_manager, receiver_client=receiver_client))
    return ipc_server.serve_in_thread(partial(_ipc_handler, logger=logger, window_manager=window_manager))

def _ipc_handler(msg: dict, logger: logging.Logger, window_manager: WindowManager) -> dict:
    """Handles incoming IPC messages and dispatches commands.

    Args:
        msg (dict): IPC message
        logger (logging.Logger): Logger
        window_manager (WindowManager): WindowManager

    Returns:
        dict: IPC response
    """
    logger.info(f"Received IPC message: {msg}")

    if not (cmd := msg.get("cmd")):
        return {"status": "error", "message": "Missing command name"}

    if (handler := COMMAND_HANDLERS.get(cmd)):
        return handler(msg, logger, window_manager)

    return {"status": "error", "message": f"Unknown command: {cmd}"}

def _shutdown_handler(args: dict, logger: logging.Logger, window_manager: WindowManager, receiver_client: HudClient) -> None:
    """Handles shutdown command.

    Args:
        args (dict): IPC message
        logger (logging.Logger): Logger
        window_manager (WindowManager): WindowManager
        receiver_client (HudClient): Receiver client obj
    """

    threading.Thread(target=_stop_other_tasks, args=(args, logger, window_manager, receiver_client,), name="Shutdown tasks").start()
    return {"status": "success", "message": "Shutting down HUD manager"}

def _stop_other_tasks(args: dict, logger: logging.Logger, window_manager: WindowManager, receiver_client: HudClient) -> None:
    """Stop all other tasks when IPC shutdown is received.

    Args:
        args (dict): IPC message
        logger (logging.Logger): Logger
        window_manager (WindowManager): WindowManager
        receiver_client (HudClient): Receiver client
    """
    reason = args.get("reason", "N/A")
    logger.info(f"Shutdown command received via IPC. Reason: {reason}. Stopping all tasks...")
    receiver_client.stop()
    window_manager.stop()
