# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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
from lib.ipc import IpcServerSync
from lib.error_status import PNG_LOST_CONN_TO_PARENT
import os
from functools import partial
from lib.child_proc_mgmt import notify_parent_init_complete, report_ipc_port_from_child

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_ipc_task(logger: logging.Logger) -> None:
    """Initialize the IPC task.

    Args:
        logger (logging.Logger): Logger
    """
    proc_mgr = IpcServerSync(
        name="pitwall_ipc",
        max_missed_heartbeats=3,
        heartbeat_timeout=5.0,
    )
    report_ipc_port_from_child(proc_mgr.port)
    notify_parent_init_complete()

    proc_mgr.register_shutdown_callback(_proc_mgr_shutdown_callback)
    proc_mgr.register_heartbeat_missed_callback(partial(_handle_heartbeat_missed, logger=logger))
    proc_mgr.serve(handler_fn=_proc_mgmt_cmd_handler, timeout=0.25)

def _proc_mgr_shutdown_callback(_args: dict) -> dict:
    """Shutdown callback"""
    return {"status": "success"}

def _handle_heartbeat_missed(count: int, logger: logging.Logger) -> dict:
    """Handle terminate command"""

    logger.warning(f"[HUD] Missed heartbeat {count} times. This process has probably been orphaned. Terminating...")
    os._exit(PNG_LOST_CONN_TO_PARENT)

def _proc_mgmt_cmd_handler(request: dict) -> dict:
    """Handles incoming IPC messages and dispatches commands."""
    return {
        "status": "error",
        "message": f"Pit Wall does not support IPC requests. Unknown command {request['cmd']}",
    }
