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

import argparse
import logging
import os
import sys
from functools import partial

from lib.child_proc_mgmt import (notify_parent_init_complete,
                                 report_ipc_port_from_child,
                                 report_pid_from_child)
from lib.config import PngSettings, load_config_from_json
from lib.error_status import PNG_LOST_CONN_TO_PARENT, PngError
from lib.ipc import IpcPubSubBroker, IpcServerSync
from lib.logger import get_logger
from meta.meta import APP_NAME

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args and perform validation

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description=f"{APP_NAME} Pit Wall")

    # Add command-line arguments with default values
    parser.add_argument("--config-file", nargs="?", default="png_config.ini", help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Parse the command-line arguments
    return parser.parse_args()

def main(logger: logging.Logger, config: PngSettings) -> None:
    """Main function

    Args:
        logger (logging.Logger): Logger
        config (PngSettings): Configurations
    """

    broker = IpcPubSubBroker(
        xsub_port=config.Network.broker_xsub_port,
        xpub_port=config.Network.broker_xpub_port,
        logger=logger)
    broker_thread = broker.run_in_thread()

    proc_mgr = IpcServerSync(
        name="pitwall_ipc",
        max_missed_heartbeats=3,
        heartbeat_timeout=5.0,
    )
    report_ipc_port_from_child(proc_mgr.port)
    notify_parent_init_complete()

    proc_mgr.register_shutdown_callback(partial(_proc_mgr_shutdown_callback, logger=logger, broker=broker))
    proc_mgr.register_heartbeat_missed_callback(partial(_handle_heartbeat_missed, logger=logger))
    proc_mgr.serve(handler_fn=_proc_mgmt_cmd_handler, timeout=0.25)

    broker_thread.join(timeout=3.0)
    proc_mgr.close()

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    """Entry point"""

    report_pid_from_child()
    args = parseArgs()
    png_logger = get_logger("pit_wall", args.debug, jsonl=True)
    configs = load_config_from_json(args.config_file, png_logger)
    try:
        main(
            logger=png_logger,
            config=configs)
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except PngError as e:
        png_logger.error(f"Terminating due to Error: {e} with code {e.exit_code}")
        sys.exit(e.exit_code)
    except Exception as e: # pylint: disable=broad-except
        png_logger.exception("Error in main: %s", e)
        sys.exit(1)

    png_logger.info("PitWall application exiting normally.")

# -------------------------------------- CALLBACKS ---------------------------------------------------------------------

def _proc_mgr_shutdown_callback(_args: dict, logger: logging.Logger, broker: IpcPubSubBroker) -> dict:
    """Shutdown callback"""
    logger.debug("Received IPC shutdown. Shutting down the broker...")
    broker.close()
    return {"status": "success"}

def _handle_heartbeat_missed(count: int, logger: logging.Logger) -> dict:
    """Handle terminate command"""
    logger.warning(f"Missed heartbeat {count} times. This process has probably been orphaned. Terminating...")
    os._exit(PNG_LOST_CONN_TO_PARENT)

def _proc_mgmt_cmd_handler(request: dict) -> dict:
    """Handles incoming IPC messages and dispatches commands."""
    return {
        "status": "error",
        "message": f"Pit Wall does not support IPC requests. Unknown command {request['cmd']}",
    }
