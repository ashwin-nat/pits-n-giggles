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
import sys
import threading
from functools import partial

from lib.child_proc_mgmt import (notify_parent_init_complete,
                                 report_pid_from_child)
from lib.config import PngSettings, load_config_from_ini
from lib.ipc import IpcChildSync
from lib.logger import get_logger
from lib.version import get_version

from .listener.task import run_hud_update_thread
from .ipc import run_ipc_task

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args and perform validation

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description="Pits n' Giggles save data viewer")

    # Add command-line arguments with default values
    parser.add_argument("--config-file", nargs="?", default="png_config.ini", help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--ipc-port", type=int, default=None, help="Port number for the IPC server.")

    # Parse the command-line arguments
    return parser.parse_args()

def main(logger: logging.Logger, config: PngSettings, ipc_port: int, version: str) -> None:
    """Main function

    Args:
        logger (logging.Logger): Logger
        config (PngSettings): Configurations
        ipc_port (int): IPC port
        version (str): Version
    """

    notify_parent_init_complete() # TODO: re-evaluate placement
    stop_event = threading.Event()
    updater_thread = run_hud_update_thread(
        logger=logger,
        stop_event=stop_event,
        port=config.Network.server_port)

    run_ipc_task(
        port=ipc_port,
        logger=logger,
        stop_event=stop_event)
    logger.info("IPC server stopped.")

    updater_thread.join()
    logger.info("Data update listener thread stopped.")

def entry_point():
    """Entry point"""
    report_pid_from_child()
    args = parseArgs()
    png_logger = get_logger("hud", args.debug)
    version = get_version()
    configs = load_config_from_ini(args.config_file, png_logger)
    try:
        main(
            logger=png_logger,
            config=configs, # pylint: disable=no-member
            ipc_port=args.ipc_port,
            version=version)
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except Exception as e: # pylint: disable=broad-except
        png_logger.exception("Error in main: %s", e)
        sys.exit(1)
