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

import asyncio
import logging
import argparse
import sys
from typing import List

from apps.save_viewer.save_web_server import init_server_task
from apps.save_viewer.save_viewer_ipc import init_ipc_task
from apps.save_viewer.logger import get_logger
from apps.save_viewer.save_viewer_state import init_state
from lib.version import get_version

from lib.child_proc_mgmt import report_pid_from_child
from lib.config import load_config_from_ini
from meta.meta import APP_NAME

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args and perform validation

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description=f"{APP_NAME} save data viewer")

    # Add command-line arguments with default values
    parser.add_argument("--config-file", nargs="?", default="png_config.ini", help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--ipc-port", type=int, default=None, help="Port number for the IPC server.")

    # Parse the command-line arguments
    return parser.parse_args()

async def main(logger: logging.Logger, server_port: int, ipc_port: int, version: str) -> None:
    """Main function

    Args:
        logger (logging.Logger): Logger
        server_port (int): Server port
        ipc_port (int): IPC port
        version (str): Version
    """
    tasks: List[asyncio.Task] = []
    init_state(logger=logger)
    web_server = init_server_task(port=server_port, ver_str=version, logger=logger, tasks=tasks)
    init_ipc_task(logger=logger, ipc_port=ipc_port, server=web_server, tasks=tasks)

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.debug("Main task was cancelled.")
        await web_server.stop()
        for task in tasks:
            task.cancel()
        raise  # Ensure proper cancellation behavior

def entry_point():
    """Entry point"""
    report_pid_from_child()
    args = parseArgs()
    png_logger = get_logger(args.debug)
    version = get_version()
    configs = load_config_from_ini(args.config_file, png_logger)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main(
            logger=png_logger,
            server_port=configs.Network.save_viewer_port, # pylint: disable=no-member
            ipc_port=args.ipc_port,
            version=version))
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except asyncio.CancelledError:
        png_logger.info("Program shutdown gracefully.")
