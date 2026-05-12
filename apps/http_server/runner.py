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
from typing import List

from wsproto.connection import LocalProtocolError

from lib.child_proc_mgmt import notify_parent_init_complete, report_pid_from_child
from lib.config import load_config_from_json
from lib.error_status import PngError
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.ipc import IpcDealerAsync, IpcSubscriberAsync, PngAppId
from lib.logger import get_logger
from lib.version import get_version
from meta.meta import APP_NAME

from .ipc import registerIpcTask
from .telemetry_web_server import TelemetryWebServer
from .ui_tasks import initSubscriberTasks

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class HttpServerRunner:
    """Pits n' Giggles HTTP/Socket.IO Server Runner"""

    def __init__(self,
                 logger: logging.Logger,
                 config_file: str,
                 debug_mode: bool,
                 run_ipc_server: bool = False) -> None:
        self.m_logger: logging.Logger = logger
        self.m_config = load_config_from_json(config_file, logger)
        self.m_tasks: List[asyncio.Task] = []
        self.m_version: str = get_version()
        self.m_shutdown_event: asyncio.Event = asyncio.Event()

        self.m_dealer = IpcDealerAsync(
            host="127.0.0.1",
            port=self.m_config.Network.broker_router_port,
            identity=str(PngAppId.HTTP_SERVER),
            logger=logger,
        )
        self.m_tasks.append(asyncio.create_task(self.m_dealer.start(), name="Backend Dealer Recv"))

        self.m_web_server = TelemetryWebServer(
            settings=self.m_config,
            ver_str=self.m_version,
            logger=self.m_logger,
            dealer=self.m_dealer,
            debug_mode=debug_mode,
        )
        self.m_tasks.append(asyncio.create_task(self.m_web_server.run(), name="Web Server Task"))

        self.m_subscriber = initSubscriberTasks(
            settings=self.m_config,
            logger=self.m_logger,
            server=self.m_web_server,
            tasks=self.m_tasks,
        )

        registerIpcTask(
            run_ipc_server=run_ipc_server,
            logger=self.m_logger,
            web_server=self.m_web_server,
            subscriber=self.m_subscriber,
            dealer=self.m_dealer,
            tasks=self.m_tasks,
        )

        self.m_tasks.append(asyncio.create_task(self._shutdown_task(), name="Shutdown Task"))
        self.m_logger.debug("Registered %d Tasks: %s", len(self.m_tasks), [t.get_name() for t in self.m_tasks])

    async def run(self) -> None:
        """Main entry point to run the application."""
        notify_parent_init_complete()
        try:
            await asyncio.gather(*self.m_tasks)
        except asyncio.CancelledError:
            self.m_logger.debug("Main task was cancelled.")
            await AsyncInterTaskCommunicator().send('shutdown', {"reason": "Main task was cancelled."})
            raise

    async def _shutdown_task(self) -> None:
        """Wait for shutdown signal, then stop all components cleanly."""
        self.m_logger.debug("Starting shutdown task. Awaiting shutdown command...")
        await AsyncInterTaskCommunicator().receive("shutdown")
        self.m_logger.debug("Received shutdown command. Stopping tasks...")

        self.m_shutdown_event.set()
        await AsyncInterTaskCommunicator().unblock_receivers()

        await self.m_web_server.stop()
        self.m_subscriber.close()
        await self.m_dealer.close()
        await asyncio.sleep(1)

        self.m_logger.debug("Tasks stopped. Exiting...")

# -------------------------------------- FUNCTION DEFINITIONS ----------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} HTTP/Socket.IO Server")
    parser.add_argument("--config-file", nargs="?", default="png_config.json",
                        help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log-file-name", type=str, default=None, help="Log file name")
    parser.add_argument("--run-ipc-server", action="store_true",
                        help="Run IPC server on OS assigned port")
    return parser.parse_args()

async def main(logger: logging.Logger, args: argparse.Namespace) -> None:
    try:
        app = HttpServerRunner(
            logger=logger,
            config_file=args.config_file,
            debug_mode=args.debug,
            run_ipc_server=args.run_ipc_server,
        )
    except PngError as e:
        logger.error("Terminating due to Error: %s with code %s", e, e.exit_code)
        sys.exit(e.exit_code)
    try:
        await app.run()
    except PngError as e:
        logger.error("Terminating due to Error: %s with code %s", e, e.exit_code)
        sys.exit(e.exit_code)

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    report_pid_from_child()
    args_obj = parseArgs()
    png_logger = get_logger(
        name="http_server",
        debug_mode=args_obj.debug,
        file_path=args_obj.log_file_name,
        jsonl=not bool(args_obj.log_file_name),
    )
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main(png_logger, args_obj))
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except asyncio.CancelledError:
        png_logger.info("Program shutdown gracefully.")
    except LocalProtocolError:
        png_logger.info("Program shutdown gracefully.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        png_logger.exception("Error in main: %s", e)
        sys.exit(1)
