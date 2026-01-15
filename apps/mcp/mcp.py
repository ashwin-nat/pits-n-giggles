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
import asyncio
import logging
import sys
from typing import List

from lib.child_proc_mgmt import (notify_parent_init_complete,
                                 report_pid_from_child)
from lib.config import PngSettings, load_config_from_json
from lib.error_status import PngError
from lib.logger import get_logger
from lib.version import get_version
from meta.meta import APP_NAME

from .mgmt import init_ipc_task
from .subscriber import init_subscriber_task
from .mcp_server import MCPBridge

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args and perform validation

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description=f"{APP_NAME} MCP server")

    # Add command-line arguments with default values
    parser.add_argument("--config-file", nargs="?", default="png_config.json", help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Parse the command-line arguments
    return parser.parse_args()

async def main(logger: logging.Logger, settings: PngSettings, version: str) -> None:
    """Main function

    Args:
        logger (logging.Logger): Logger
        settings (PngSettings): Settings
        version (str): Version string
    """
    tasks: List[asyncio.Task] = []
    init_subscriber_task(port=settings.Network.broker_xpub_port, logger=logger, tasks=tasks)
    mcp_bridge = MCPBridge(logger, version)
    tasks.append(asyncio.create_task(mcp_bridge.run(), name="MCP Server Task"))

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.debug("Main task was cancelled.")
        for task in tasks:
            task.cancel()
        raise  # Ensure proper cancellation behavior
    except PngError as e:
        logger.error(f"Terminating due to Error: {e} with code {e.exit_code}")
        sys.exit(e.exit_code)


def entry_point():
    """Entry point"""
    args = parseArgs()
    # TODO: make rotating logging configurable
    png_logger = get_logger("mcp", args.debug, jsonl=False, file_path="mcp.log", console_output=False)
    version = get_version()
    # TODO: fail if config file is not available
    configs = load_config_from_json(args.config_file, png_logger)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main(
            logger=png_logger,
            settings=configs,
            version=version
            ))
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except asyncio.CancelledError:
        png_logger.info("Program shutdown gracefully.")
