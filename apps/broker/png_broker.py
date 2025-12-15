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

from lib.child_proc_mgmt import report_pid_from_child
from lib.config import PngSettings, load_config_from_json
from lib.logger import get_logger
from meta.meta import APP_NAME

from lib.ipc import IpcPubSubBroker, IpcServerSync
from .ipc import init_ipc_task

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args and perform validation

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description=f"{APP_NAME} HUD")

    # Add command-line arguments with default values
    parser.add_argument("--config-file", nargs="?", default="png_config.ini", help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument('--run-ipc-server', action='store_true', help="Run IPC server on OS assigned port") # unused
    parser.add_argument('--xpub-port', type=int, default=None, help="IPC xpub port") # unused
    parser.add_argument('--xsub-port', type=int, default=None, help="IPC xsub port") # unused

    # Parse the command-line arguments
    return parser.parse_args()

def main(logger: logging.Logger, config: PngSettings, debug_mode: bool) -> None:
    """Main function

    Args:
        logger (logging.Logger): Logger
        config (PngSettings): Configurations
        debug_mode (bool): Debug mode
    """

    init_ipc_task(logger)

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    """Entry point"""

    report_pid_from_child()
    args = parseArgs()
    png_logger = get_logger("hud", args.debug, jsonl=True)
    configs = load_config_from_json(args.config_file, png_logger)
    try:
        main(
            logger=png_logger,
            config=configs,
            debug_mode=args.debug)
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except Exception as e: # pylint: disable=broad-except
        png_logger.exception("Error in main: %s", e)
        sys.exit(1)

    png_logger.info("PitWall application exiting normally.")
