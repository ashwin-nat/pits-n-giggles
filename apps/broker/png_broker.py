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
    parser.add_argument("--config-file", nargs="?", default="png_config.json", help="Configuration file name (optional)")
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

    @proc_mgr.on_shutdown
    def _shutdown_handler(_args: dict) -> dict:
        logger.debug("Received IPC shutdown. Shutting down the broker...")
        broker.close()
        return {
            "status": "success",
        }

    @proc_mgr.on_heartbeat_missed
    def _heartbeat_missed_handler(count: int) -> None:
        logger.warning("Missed heartbeat %s times. This process has probably been orphaned. Terminating...", count)
        # os._exit required: child process must terminate immediately without
        # running atexit handlers or flushing stdio buffers from parent.
        os._exit(PNG_LOST_CONN_TO_PARENT)

    @proc_mgr.on("get-stats")
    def _get_stats_handler(_args: dict) -> dict:
        return {
            "status": "success",
            "stats": broker.get_stats(),
        }

    proc_mgr.serve()
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
        png_logger.exception("Terminating due to Error: %s with code %d", e, e.exit_code)
        sys.exit(e.exit_code)
    except Exception as e: # pylint: disable=broad-exception-caught
        png_logger.exception("Error in main: %s", e)
        sys.exit(1)

    png_logger.info("PitWall application exiting normally.")
