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
import webbrowser
from typing import List, Optional, Set

from colorama import Fore, Style, init

from apps.backend.common.config import load_config
from apps.backend.common.png_logger import initLogger
from apps.backend.state_mgmt_layer import initStateManagementLayer
from apps.backend.telemetry_layer import initTelemetryLayer
from apps.backend.ui_intf_layer import TelemetryWebServer, initUiIntfLayer
from lib.pid_report import report_pid_from_child

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class PngRunner:
    """Pits n' Giggles Backend Runner"""
    def __init__(self, logger: logging.Logger, config_file: str, replay_server: bool, debug_mode: bool):
        """Init the runner. Register necessary tasks

        Args:
            logger (logging.Logger): Logger object
            config_file (str): Path to the config file
            replay_server (bool): If true, runs in TCP debug mode, else UDP live mode
            debug_mode (bool): If true, runs in debug mode
        """
        self.m_logger: logging.Logger = logger
        self.m_config = load_config(config_file, logger)
        self.m_tasks: List[asyncio.Task] = []

        self.m_logger.info("PID=%d Starting the app with the following options:", os.getpid())
        self.m_logger.info(f"Python version {sys.version}")
        self.m_logger.info(self.m_config)

        initStateManagementLayer(logger=self.m_logger, process_car_setups=self.m_config.process_car_setup)

        initTelemetryLayer(
            port_number=self.m_config.telemetry_port,
            replay_server=replay_server,
            logger=self.m_logger,
            post_race_data_autosave=self.m_config.post_race_data_autosave,
            udp_custom_action_code=self.m_config.udp_custom_action_code,
            udp_tyre_delta_action_code=self.m_config.udp_tyre_delta_action_code,
            forwarding_targets=self.m_config.forwarding_targets,
            tasks=self.m_tasks
        )
        self.m_web_server = self._setupUiIntfLayer(
            http_port=self.m_config.server_port,
            logger=self.m_logger,
            client_update_interval_ms=self.m_config.refresh_interval,
            disable_browser_autoload=self.m_config.disable_browser_autoload,
            stream_overlay_start_sample_data=self.m_config.stream_overlay_start_sample_data,
            tasks=self.m_tasks,
            ver_str=self._getVersion(),
            debug_mode=debug_mode
        )

        # Run all tasks concurrently
        self._printDoNotCloseWarning()
        self.m_logger.debug("Registered %d Tasks: %s", len(self.m_tasks), [task.get_name() for task in self.m_tasks])

    async def run(self) -> None:
        """Main entry point to run the application."""
        try:
            await asyncio.gather(*self.m_tasks)
        except asyncio.CancelledError:
            png_logger.debug("Main task was cancelled.")
            await self.m_web_server.stop()
            for task in self.m_tasks:
                task.cancel()
            raise  # Ensure proper cancellation behavior

    def _setupUiIntfLayer(self,
        http_port: int,
        logger: logging.Logger,
        client_update_interval_ms: int,
        disable_browser_autoload: bool,
        stream_overlay_start_sample_data: bool,
        tasks: List[asyncio.Task],
        ver_str: str,
        debug_mode: Optional[bool] = False) -> TelemetryWebServer:
        """Entry point to start the HTTP server.

        Args:
            http_port (int): Port number for the HTTP server.
            logger (logging.Logger): Logger instance.
            client_update_interval_ms (int): Client poll interval in milliseconds.
            disable_browser_autoload (bool): Whether to disable browser autoload.
            stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives
            tasks (List[asyncio.Task]): List of tasks to be executed
            ver_str (str): Version string
            debug_mode (bool, optional): Debug mode. Defaults to False.

        Returns:
            TelemetryWebServer: The initialized web server object
        """
        # Create a task to open the webpage
        if not disable_browser_autoload:
            tasks.append(asyncio.create_task(self._openWebPage(http_port), name="Web page opener Task"))

        log_str = "Starting F1 telemetry server. Open one of the below addresses in your browser\n"
        ip_addresses = self._getLocalIpAddresses()
        for ip_addr in ip_addresses:
            log_str += f"    http://{ip_addr}:{http_port}\n"
        log_str += "NOTE: The tables will be empty until the red lights appear on the screen before the race start\n"
        log_str += "That is when the game starts sending telemetry data"
        self.m_logger.info(log_str)

        return initUiIntfLayer(
            port=http_port,
            logger=logger,
            client_update_interval_ms=client_update_interval_ms,
            debug_mode=debug_mode,
            stream_overlay_start_sample_data=stream_overlay_start_sample_data,
            tasks=tasks,
            ver_str=ver_str
        )

    def _getLocalIpAddresses(self) -> Set[str]:
        """Get local IP addresses including '127.0.0.1' and 'localhost'.

        Returns:
            Set[str]: Set of local IP addresses.
        """
        ip_addresses = {'127.0.0.1', 'localhost'}
        try:
            for host_name in socket.gethostbyname_ex(socket.gethostname())[2]:
                ip_addresses.add(host_name)
        except socket.gaierror as e:
            # Log the error or handle it as per your requirement
            self.m_logger.warning("Error occurred: %s. Using default IP addresses.", e)
        return ip_addresses

    async def _openWebPage(self, http_port: int) -> None:
        """Open the webpage on a new browser tab.

        Args:
            http_port (int): Port number of the HTTP server.
        """
        await asyncio.sleep(1)
        webbrowser.open(f'http://localhost:{http_port}', new=2)
        self.m_logger.debug("Webpage opened. Task completed")

    def _printDoNotCloseWarning(self) -> None:
        """
        Prints a warning message in red and bold.
        Works across Windows CMD, PowerShell, and Linux/macOS terminals.
        """
        init(autoreset=True)  # Ensures colors reset automatically and enables ANSI on Windows

        RED = Fore.RED
        BOLD = Style.BRIGHT

        border = "*" * 60  # Fixed-width border
        message = [
            "WARNING: DO NOT CLOSE THIS WINDOW!",
            "This command line window is required",
            "for the application to run properly.",
            "If you close this window, the application",
            "will stop working."
        ]

        print(RED + BOLD + border)
        for line in message:
            print(RED + BOLD + f"* {line.center(56)} *")
        print(RED + BOLD + border)


    def _getVersion(self) -> str:
        """Get the version string from env variable

        Returns:
            str: Version string
        """

        return os.environ.get('PNG_VERSION', 'dev')

# -------------------------------------- FUNCTION DEFINITIONS ----------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description="Pits n' Giggles Realtime Telemetry Server")

    # Add command-line arguments with default values
    parser.add_argument("config_file", nargs="?", default="png_config.ini", help="Configuration file name (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument('--replay-server', action='store_true', help="Enable the TCP replay debug server")
    parser.add_argument('--log-file-name', type=str, default=None, help="Log file name")

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
        debug_mode=args.debug
    )
    await app.run()

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

if __name__ == '__main__':
    report_pid_from_child()
    args_obj = parseArgs()
    png_logger = initLogger(file_name=args_obj.log_file_name, max_size=100000, debug_mode=args_obj.debug)
    try:
        asyncio.run(main(png_logger, args_obj))
    except KeyboardInterrupt:
        png_logger.info("Program interrupted by user.")
    except asyncio.CancelledError:
        png_logger.info("Program shutdown gracefully.")

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

# if __name__ == "__main__":
#     yappi.set_clock_type("wall")  # Use "cpu" for CPU-bound tasks
#     yappi.start()

#     args_obj = parseArgs()
#     png_logger = initLogger(file_name='png_log.log', max_size=100000, debug_mode=args_obj.debug)
#     try:
#         asyncio.run(main(png_logger, args_obj))
#     except KeyboardInterrupt:
#         png_logger.info("Program interrupted by user.")
#     except asyncio.CancelledError:
#         png_logger.info("Program shutdown gracefully.")
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
