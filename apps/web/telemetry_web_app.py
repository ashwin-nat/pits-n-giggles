# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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
from pathlib import Path
from typing import List

from lib.child_proc_mgmt import report_pid_from_child
from lib.config import PngSettings, load_config_from_json
from lib.error_status import PngError
from lib.file_path import get_app_base_dir
from lib.logger import get_logger
from lib.periodic_task import periodic_task
from lib.version import get_version
from meta.meta import APP_NAME

from .ipc_mgmt import init_ipc_task
from .tasks import initDealer, initSubscriber, raceTableEmitTask, streamOverlayEmitTask
from .web_server import WebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args and perform validation

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    parser = argparse.ArgumentParser(description=f"{APP_NAME} unified web app")
    parser.add_argument("--config-file", nargs="?", default="png_config.json", help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    return parser.parse_args()

async def main(logger: logging.Logger, settings: PngSettings, version: str, debug_mode: bool) -> None:
    """Main function

    Args:
        logger (logging.Logger): Logger
        settings (PngSettings): Settings
        version (str): Version string
        debug_mode (bool): Whether debug mode is enabled
    """
    tasks: List[asyncio.Task] = []
    shutdown_event = asyncio.Event()

    session_dir_setting = settings.Capture.session_dir_path
    session_dir = session_dir_setting if session_dir_setting.is_absolute() \
        else (get_app_base_dir() / session_dir_setting).resolve()
    viewer_dir = Path(__file__).resolve().parent.parent / "external" / "f1-save-viewer" / "dist"
    logger.debug("Session directory: %s", session_dir)
    logger.debug("Viewer directory: %s", viewer_dir)

    web_server = WebServer(settings=settings, ver_str=version, logger=logger, session_dir=session_dir,
                           viewer_dir=viewer_dir, debug_mode=debug_mode)
    tasks.append(asyncio.create_task(web_server.run(), name="Web Server Task"))

    ipc_sub = initSubscriber(settings.Network.broker_xpub_port, logger, web_server)
    tasks.append(asyncio.create_task(ipc_sub.run(), name="Broker Subscriber Task"))

    dealer = initDealer(settings.Network.broker_router_port, logger, web_server)
    tasks.append(asyncio.create_task(dealer.start(), name="Web Dealer Recv"))

    tasks.append(asyncio.create_task(
        periodic_task(
            settings.Display.refresh_interval,
            shutdown_event,
            logger,
            raceTableEmitTask,
            web_server), name="Race Table Emit Task"))
    tasks.append(asyncio.create_task(
        periodic_task(
            settings.Display.refresh_interval,
            shutdown_event,
            logger,
            streamOverlayEmitTask,
            web_server), name="Stream Overlay Emit Task"))

    init_ipc_task(logger, web_server, ipc_sub, dealer, shutdown_event, tasks)

    try:
        logger.debug("Registered %d Tasks: %s", len(tasks), [task.get_name() for task in tasks])
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.debug("Main task was cancelled.")
        await web_server.stop()
        for task in tasks:
            task.cancel()
        raise  # Ensure proper cancellation behavior
    except PngError as e:
        logger.error("Terminating due to Error: %s with code %s", e, e.exit_code)
        sys.exit(e.exit_code)

def entry_point():
    """Entry point"""
    report_pid_from_child()
    args = parseArgs()
    png_logger = get_logger("web", args.debug, jsonl=True)
    version = get_version()
    settings = load_config_from_json(args.config_file, png_logger, fail_if_missing=True)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main(
            logger=png_logger,
            settings=settings,
            version=version,
            debug_mode=args.debug))
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except asyncio.CancelledError:
        png_logger.info("Program shutdown gracefully.")
