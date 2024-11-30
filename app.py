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
import socket
import sys
import threading
import time
import webbrowser
import logging
from typing import Set, Optional

from src.telemetry_handler import initPktCap, PacketCaptureMode, initAutosaves, F1TelemetryHandler, initDirectories
from src.telemetry_server import initTelemetryWebServer
from src.png_logger import initLogger
from src.config import load_config

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

png_logger: Optional[logging.Logger] = None

# -------------------------------------- FUNCTION DEFINITIONS ----------------------------------------------------------

def parseArgs() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: The parsed args namespace
    """

    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description="F1 Telemetry Client and Server")

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

def openWebPage(http_port: int) -> None:
    """Open the webpage on a new browser tab.

    Args:
        http_port (int): Port number of the HTTP server.
    """
    time.sleep(1)
    webbrowser.open(f'http://localhost:{http_port}', new=2)

def httpServerTask(
        http_port: int,
        packet_capture_enabled: bool,
        client_update_interval_ms: int,
        disable_browser_autoload: bool) -> None:
    """Entry point to start the HTTP server.

    Args:
        http_port (int): Port number for the HTTP server.
        packet_capture_enabled (bool): Whether packet capture is enabled.
        client_update_interval_ms (int): Client poll interval in milliseconds.
        disable_browser_autoload (bool): Whether to disable browser autoload.
    """
    # Create a thread to open the webpage
    if not disable_browser_autoload:
        webpage_open_thread = threading.Thread(target=openWebPage, args=(http_port,))
        webpage_open_thread.start()

    log_str = "Starting F1 telemetry server. Open one of the below addresses in your browser\n"
    ip_addresses = getLocalIpAddresses()
    for ip_addr in ip_addresses:
        log_str += f"    http://{ip_addr}:{http_port}\n"
    log_str += "NOTE: The tables will be empty until the red lights appear on the screen before the race start\n"
    log_str += "That is when the game starts sending telemetry data"
    png_logger.info(log_str)

    initTelemetryWebServer(
        port=http_port,
        packet_capture_enabled=packet_capture_enabled,
        client_update_interval_ms=client_update_interval_ms,
        debug_mode=False
    )

def f1TelemetryServerTask(
        packet_capture: PacketCaptureMode,
        port_number: int,
        replay_server: bool,
        post_race_data_autosave: bool,
        udp_custom_action_code: Optional[int],
        udp_tyre_delta_action_code: Optional[int]) -> None:
    """Entry point to start the F1 23 telemetry server.

    Args:
        packet_capture (PacketCaptureMode): Packet capture mode.
        port_number (int): Port number for the telemetry client.
        replay_server (bool): Whether to enable the TCP replay debug server.
        post_race_data_autosave (bool): Whether to autosave race data at the end of the race.
        udp_custom_action_code (Optional[int]): UDP custom action code.
        udp_tyre_delta_action_code (Optional[int]): UDP tyre delta action code.
    """
    time.sleep(2)
    if packet_capture != PacketCaptureMode.DISABLED:
        initPktCap(packet_capture)
    initAutosaves(post_race_data_autosave, udp_custom_action_code, udp_tyre_delta_action_code)
    telemetry_client = F1TelemetryHandler(port_number, packet_capture, replay_server)
    telemetry_client.run()

def main() -> None:
    """Entry point for the application."""

    global png_logger
    # Initialize the ArgumentParser
    args = parseArgs()
    config = load_config(args.config_file)

    png_logger = initLogger(file_name=config.log_file, max_size=config.log_file_size, debug_mode=args.debug)
    png_logger.info("Starting the app with the following options:")
    png_logger.info(config)

    initDirectories()

    # First init the telemetry client on a main thread
    client_thread = threading.Thread(target=f1TelemetryServerTask,
                                    args=(config.packet_capture_mode, config.telemetry_port,
                                        args.replay_server, config.post_race_data_autosave,
                                        config.udp_custom_action_code, config.udp_tyre_delta_action_code))
    client_thread.daemon = True
    client_thread.start()

    # Run the HTTP server on the main thread. Flask does not like running on separate threads
    packet_capture_enabled = \
        config.packet_capture_mode in [PacketCaptureMode.ENABLED, PacketCaptureMode.ENABLED_WITH_AUTOSAVE]
    httpServerTask(config.server_port, packet_capture_enabled, config.refresh_interval,
                   config.disable_browser_autoload)

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

if __name__ == '__main__':
    main()