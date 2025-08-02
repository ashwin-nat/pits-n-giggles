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
# pylint: skip-file

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

def parseArgs(logger: logging.Logger) -> argparse.Namespace:
    """Parse the command line args and perform validation

    Args:
        logger (logging.Logger): Logger

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description="Pits n' Giggles save data viewer")

    # Add command-line arguments with default values
    parser.add_argument("--launcher", action="store_true", help="Enable launcher mode. Input is expeected via stdin")
    parser.add_argument("--port", type=int, default=None, help="Port number for the server.")
    parser.add_argument("--ipc-port", type=int, default=None, help="Port number for the IPC server.")

    # Parse the command-line arguments
    parsed_args = parser.parse_args()

    if parsed_args.launcher and parsed_args.port is None:
        logger.info("Port number is required in launcher mode")
        sys.exit(1)

    return parsed_args

async def main(logger: logging.Logger, server_port: int, ipc_port: int, version: str) -> None:

    tasks: List[asyncio.Task] = []
    init_state(logger=logger, port=server_port)
    init_server_task(port=server_port, ver_str=version, logger=logger, tasks=tasks)
    init_ipc_task(logger=logger, ipc_port=ipc_port, server_port=server_port, tasks=tasks)

    await asyncio.gather(*tasks)


    # png_logger.debug(f"cwd={os.getcwd()}")
    # global g_port_number
    # args = parseArgs()
    # version = get_version()

    # tasks: List[asyncio.Task] = []


    # ipc_server = IpcChildAsync(args.ipc_port, "Save Viewer")
    # tasks.append(ipc_server.get_task(partial(handle_ipc_message, logger=png_logger)))
    # g_port_number = args.port
    # if not is_port_available(g_port_number):
    #     png_logger.error(f"Port {g_port_number} is not available")
    #     sys.exit(PNG_ERROR_CODE_PORT_IN_USE)

    # # Start Flask server after Tkinter UI is initialized
    # png_logger.info(f"Starting server. It can be accessed at http://localhost:{str(g_port_number)} "
    #                 f"PID = {os.getpid()} Version = {version}")
    # global _server
    # _server = TelemetryWebServer(
    #     port=g_port_number,
    #     ver_str=version,
    #     logger=png_logger)
    # tasks.append(asyncio.create_task(_server.run(), name="Web Server Task"))
    # try:
    #     await asyncio.gather(*tasks)
    # except asyncio.CancelledError:
    #     png_logger.debug("Main task was cancelled.")
    #     await _server.stop()
    #     for task in tasks:
    #         task.cancel()
    #     raise  # Ensure proper cancellation behavior
    # try:
    #     _server.run()
    # except OSError as e:
    #     png_logger.error(e)
    #     if e.errno == errno.EADDRINUSE:
    #         sys.exit(PNG_ERROR_CODE_PORT_IN_USE)
    #     else:
    #         sys.exit(PNG_ERROR_CODE_UNKNOWN)

def entry_point():
    report_pid_from_child()
    png_logger = get_logger()
    args = parseArgs(png_logger)
    version = get_version()
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main(logger=png_logger, server_port=args.port, ipc_port=args.ipc_port, version=version))
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except asyncio.CancelledError:
        png_logger.info("Program shutdown gracefully.")
