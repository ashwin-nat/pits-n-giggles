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
import os
import socket
import sys
from typing import List, Optional, Set

import psutil

from apps.backend.common.png_logger import initLogger
from apps.backend.state_mgmt_layer import initStateManagementLayer, SessionState
from apps.backend.telemetry_layer import initTelemetryLayer
from apps.backend.ui_intf_layer import TelemetryWebServer, initUiIntfLayer
from lib.child_proc_mgmt import report_pid_from_child
from lib.config import load_config_from_ini
from lib.error_status import PngError
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.version import get_version

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class PngRunner:
    """Pits n' Giggles Backend Runner"""
    def __init__(self,
                 logger: logging.Logger,
                 config_file: str,
                 replay_server: bool,
                 debug_mode: bool,
                 ipc_port: Optional[int] = None):
        """Init the runner. Register necessary tasks

        Args:
            logger (logging.Logger): Logger object
            config_file (str): Path to the config file
            replay_server (bool): If true, runs in TCP debug mode, else UDP live mode
            debug_mode (bool): If true, runs in debug mode
            ipc_port (Optional[int], optional): IPC port. Defaults to None.
        """
        self.m_logger: logging.Logger = logger
        self.m_config = load_config_from_ini(config_file, logger)
        self.m_tasks: List[asyncio.Task] = []
        self.m_version: str = get_version()

        self.m_logger.debug(self.m_config)
        self.m_shutdown_event: asyncio.Event = asyncio.Event()

        self.m_session_state: SessionState = initStateManagementLayer(
            logger=self.m_logger,
            settings=self.m_config,
            ver_str=self.m_version,
            tasks=self.m_tasks,
            shutdown_event=self.m_shutdown_event
        )

        self.m_telemetry_handler = initTelemetryLayer(
            settings=self.m_config,
            replay_server=replay_server,
            logger=self.m_logger,
            ver_str=self.m_version,
            shutdown_event=self.m_shutdown_event,
            session_state=self.m_session_state,
            tasks=self.m_tasks
        )
        self.m_web_server = self._setupUiIntfLayer(
            ipc_port=ipc_port,
            debug_mode=debug_mode
        )
        self.m_tasks.append(asyncio.create_task(self._shutdown_tasks(), name="Shutdown Task"))

        # Run all tasks concurrently
        self.m_logger.debug("Registered %d Tasks: %s", len(self.m_tasks), [task.get_name() for task in self.m_tasks])

    async def run(self) -> None:
        """Main entry point to run the application."""
        try:
            await asyncio.gather(*self.m_tasks)
        except asyncio.CancelledError:
            self.m_logger.debug("Main task was cancelled.")
            await AsyncInterTaskCommunicator().send('shutdown', {"reason" : "Main task was cancelled."})
            raise  # Ensure proper cancellation behavior

    def _setupUiIntfLayer(self,
        ipc_port: Optional[int] = None,
        debug_mode: Optional[bool] = False) -> TelemetryWebServer:
        """Entry point to start the HTTP server.

        Args:
            ipc_port (Optional[int], optional): IPC port. Defaults to None.
            debug_mode (bool, optional): Debug mode. Defaults to False.

        Returns:
            TelemetryWebServer: The initialized web server object
        """

        log_str = "Starting F1 telemetry server. Open one of the below addresses in your browser\n"
        ip_addresses = self._getLocalIpAddresses()
        for ip_addr in ip_addresses:
            # pylint: disable=no-member
            log_str += f"    {self.m_config.HTTPS.proto}://{ip_addr}:{self.m_config.Network.server_port}\n"
        log_str += "NOTE: The tables will be empty until the red lights appear on the screen before the race start\n"
        log_str += "That is when the game starts sending telemetry data"
        self.m_logger.info(log_str)

        return initUiIntfLayer(
            settings=self.m_config,
            logger=self.m_logger,
            session_state=self.m_session_state,
            debug_mode=debug_mode,
            tasks=self.m_tasks,
            ver_str=self.m_version,
            ipc_port=ipc_port,
            shutdown_event=self.m_shutdown_event,
        )

    def _getLocalIpAddresses(self) -> Set[str]:
        """Get local IP addresses including '127.0.0.1' and 'localhost'.

        Returns:
            Set[str]: Set of local IP addresses.
        """
        ip_addresses = {'127.0.0.1', 'localhost'}
        for _, snics in psutil.net_if_addrs().items():
            for snic in snics:
                if snic.family == socket.AF_INET:
                    ip = snic.address
                    # Filter out loopback and CGNAT (100.64.0.0/10)
                    if ip.startswith('127.') or ip.startswith('169.254.') or ip.startswith('100.'):
                        continue
                    ip_addresses.add(ip)
        return ip_addresses

    def _getVersion(self) -> str:
        """Get the version string from env variable

        Returns:
            str: Version string
        """

        return os.environ.get('PNG_VERSION', 'dev')

    async def _shutdown_tasks(self) -> None:
        """Shutdown all the tasks and finish so that the event loop can terminate naturally
        """

        self.m_logger.debug("Starting shutdown task. Awaiting shutdown command...")
        await AsyncInterTaskCommunicator().receive("shutdown")
        self.m_logger.debug("Received shutdown command. Stopping tasks...")

        # Periodic UI update tasks and packet forwarder are listening to shutdown event
        self.m_shutdown_event.set()
        await AsyncInterTaskCommunicator().unblock_receivers()

        # Explicitly stop the
        await self.m_web_server.stop()
        await self.m_telemetry_handler.stop()
        await asyncio.sleep(1)

        self.m_logger.debug("Tasks stopped. Exiting...")

# -------------------------------------- FUNCTION DEFINITIONS ----------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description="Pits n' Giggles Realtime Telemetry Server")

    # Add command-line arguments with default values
    parser.add_argument("--config-file", nargs="?", default="png_config.ini", help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument('--replay-server', action='store_true', help="Enable the TCP replay debug server")
    parser.add_argument('--log-file-name', type=str, default=None, help="Log file name")
    parser.add_argument("--ipc-port", type=int, default=None, help="Port number for the IPC server.")

    # Parse the command-line arguments
    return parser.parse_args()

async def main(logger: logging.Logger, args: argparse.Namespace) -> None:
    """Entry point for the application.

    Args:
        logger (logging.Logger): Logger object
        args (argparse.Namespace): Parsed command-line arguments.
    """

    app = PngRunner(
        logger=logger,
        config_file=args.config_file,
        replay_server=args.replay_server,
        debug_mode=args.debug,
        ipc_port=args.ipc_port
    )
    try:
        await app.run()
    except PngError as e:
        logger.error(f"Terminating due to Error: {e} with code {e.exit_code}")
        sys.exit(e.exit_code)

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    report_pid_from_child()
    args_obj = parseArgs()
    png_logger = initLogger(
        file_name=args_obj.log_file_name,
        max_size=100000,
        debug_mode=args_obj.debug
    )
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main(png_logger, args_obj))
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except asyncio.CancelledError:
        png_logger.info("Program shutdown gracefully.")
    except Exception as e: # pylint: disable=broad-exception-caught
        png_logger.exception("Error in main: %s", e)
        sys.exit(1)

# ---------------------------------------- PROFILER MODE ---------------------------------------------------------------

# import yappi
# import pstats

# def save_pstats_report(html_filename, txt_filename):
#     stats = pstats.Stats("yappi_profile.prof")

#     # Don't strip directories, so full paths are included
#     # If you want the paths to be fully visible, just skip strip_dirs()
#     stats.sort_stats("cumulative")

#     # Save as HTML
#     with open(html_filename, "w") as f:
#         f.write("<html><head><title>Yappi Profile</title></head><body><pre>")
#         stats.stream = f
#         stats.print_stats()
#         f.write("</pre></body></html>")

#     # Save as TXT
#     with open(txt_filename, "w") as f:
#         stats.stream = f
#         stats.print_stats()

# def entry_point():
#     yappi.set_clock_type("wall")  # Use "cpu" for CPU-bound tasks
#     yappi.start()

#     report_pid_from_child()
#     args_obj = parseArgs()
#     png_logger = initLogger(
#         file_name=args_obj.log_file_name,
#         max_size=100000,
#         debug_mode=args_obj.debug
#     )
#     if sys.platform == 'win32':
#         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#     try:
#         asyncio.run(main(png_logger, args_obj))
#     except KeyboardInterrupt:
#         png_logger.info("Program interrupted by user.")
#     except asyncio.CancelledError:
#         png_logger.info("Program shutdown gracefully.")
#     except Exception as e:
#         png_logger.exception("Error in main: %s", e)
#         sys.exit(1)
#     finally:
#         yappi.stop()

#         # Save function-level stats for SnakeViz
#         yappi.get_func_stats().save("yappi_profile.prof", type="pstat")
#         print("Saved function profile as yappi_profile.prof (compatible with snakeviz)")

#         # Generate reports
#         save_pstats_report("yappi_profile.html", "yappi_profile.txt")

#         print("Generated reports:")
#         print(" - yappi_profile.html")
#         print(" - yappi_profile.txt")
