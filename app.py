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
import asyncio
import logging
import socket
import threading
import time
import webbrowser
from typing import List, Optional, Set, Tuple

from colorama import Fore, Style, init

from src.config import load_config
from src.png_logger import initLogger
from src.telemetry_data import initDriverData
from src.telemetry_handler import (F1TelemetryHandler, initDirectories,
                                   initForwarder, initTelemetryGlobals)
from typing import List, Optional, Set, Tuple

from colorama import Fore, Style, init

from src.config import load_config
from src.png_logger import initLogger
from src.telemetry_data import initDriverData
from src.telemetry_handler import (F1TelemetryHandler, initDirectories,
                                   initForwarder, initTelemetryGlobals)
from src.telemetry_server import initTelemetryWebServer

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

png_logger: Optional[logging.Logger] = None

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

    # Parse the command-line arguments
    return parser.parse_args()

def getLocalIpAddresses() -> Set[str]:
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
        png_logger.warning("Error occurred: %s. Using default IP addresses.", e)
    return ip_addresses

async def openWebPage(http_port: int) -> None:
    """Open the webpage on a new browser tab.

    Args:
        http_port (int): Port number of the HTTP server.
    """
    await asyncio.sleep(1)
    webbrowser.open(f'http://localhost:{http_port}', new=2)
    png_logger.debug("Webpage opened. Task completed")

def setupWebServerTask(
def setupWebServerTask(
        http_port: int,
        client_update_interval_ms: int,
        disable_browser_autoload: bool,
        stream_overlay_start_sample_data: bool,
        tasks: List[asyncio.Task]) -> None:
        stream_overlay_start_sample_data: bool,
        tasks: List[asyncio.Task]) -> None:
    """Entry point to start the HTTP server.

    Args:
        http_port (int): Port number for the HTTP server.
        client_update_interval_ms (int): Client poll interval in milliseconds.
        disable_browser_autoload (bool): Whether to disable browser autoload.
        stream_overlay_start_sample_data (bool): Whether to show sample data in overlay until real data arrives
        tasks (List[asyncio.Task]): List of tasks to be executed
        tasks (List[asyncio.Task]): List of tasks to be executed
    """
    # Create a thread to open the webpage
    if not disable_browser_autoload:
        tasks.append(asyncio.create_task(openWebPage(http_port), name="Web page opener Task"))

    log_str = "Starting F1 telemetry server. Open one of the below addresses in your browser\n"
    ip_addresses = getLocalIpAddresses()
    for ip_addr in ip_addresses:
        log_str += f"    http://{ip_addr}:{http_port}\n"
    log_str += "NOTE: The tables will be empty until the red lights appear on the screen before the race start\n"
    log_str += "That is when the game starts sending telemetry data"
    png_logger.info(log_str)

    initTelemetryWebServer(
        port=http_port,
        client_update_interval_ms=client_update_interval_ms,
        debug_mode=False,
        stream_overlay_start_sample_data=stream_overlay_start_sample_data,
        tasks=tasks
        stream_overlay_start_sample_data=stream_overlay_start_sample_data,
        tasks=tasks
    )

def setupGameTelemetryTask(
        port_number: int,
        replay_server: bool,
        post_race_data_autosave: bool,
        udp_custom_action_code: Optional[int],
        udp_tyre_delta_action_code: Optional[int],
        forwarding_targets: List[Tuple[str, int]],
        tasks: List[asyncio.Task]) -> None:
    """Entry point to start the F1 telemetry server.

    Args:
        port_number (int): Port number for the telemetry client.
        replay_server (bool): Whether to enable the TCP replay debug server.
        post_race_data_autosave (bool): Whether to autosave race data at the end of the race.
        udp_custom_action_code (Optional[int]): UDP custom action code.
        udp_tyre_delta_action_code (Optional[int]): UDP tyre delta action code.
        forwarding_targets (List[Tuple[str, int]]): List of IP addr port pairs to forward packets to
    """
    time.sleep(2) # TODO: revisit this sleep
    time.sleep(2) # TODO: revisit this sleep
    initTelemetryGlobals(post_race_data_autosave, udp_custom_action_code, udp_tyre_delta_action_code)
    initForwarder(forwarding_targets)
    telemetry_client = F1TelemetryHandler(port_number, forwarding_targets, replay_server)
    tasks.append(asyncio.create_task(telemetry_client.run(), name="Game Telemetry Listener Task"))


def printDoNotCloseWarning() -> None:
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

async def main() -> None:
async def main() -> None:
    """Entry point for the application."""

    global png_logger
    # Initialize the ArgumentParser
    args = parseArgs()
    config = load_config(args.config_file)

    png_logger = initLogger(file_name=config.log_file, max_size=config.log_file_size, debug_mode=args.debug)
    png_logger.info("Starting the app with the following options:")
    png_logger.info(config)

    initDirectories()
    initDriverData(
        config.post_race_data_autosave,
        config.udp_custom_action_code,
        config.udp_tyre_delta_action_code,
        config.process_car_setup
    )

    tasks: List[asyncio.Task] = []

    # First init the telemetry client on a main thread
    client_thread = threading.Thread(target=f1TelemetryServerTask,
                                    args=(config.telemetry_port,
                                        args.replay_server, config.post_race_data_autosave,
                                        config.udp_custom_action_code, config.udp_tyre_delta_action_code,
                                        config.forwarding_targets))
    client_thread.daemon = True
    client_thread.start()

    # Run the HTTP server on the main thread. Flask does not like running on separate threads
    printDoNotCloseWarning()

    setupWebServerTask(config.server_port, config.refresh_interval,
                   config.disable_browser_autoload, config.stream_overlay_start_sample_data, tasks)

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

if __name__ == '__main__':
    asyncio.run(main())

    asyncio.run(main())
