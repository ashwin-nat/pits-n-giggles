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

import argparse
import logging
import socket
import sys
import threading
import time
import webbrowser
from typing import Set

from telemetry_handler import initPktCap, PacketCaptureMode, initAutosaves, F12023TelemetryHandler, initDirectories
from telemetry_server import TelemetryWebServer


def initLogger(file_name: str = None, debug_mode: bool = False) -> logging.Logger:
    """Initialize and configure the logger.

    Args:
        file_name (str, optional): The name of the log file. Defaults to None.
        debug_mode (bool, optional): Whether to enable debug mode. Defaults to False.

    Returns:
        logging.Logger: The configured logger.
    """
    # Create a formatter with a time-based format
    format_str = '%(asctime)s [%(levelname)s] [%(funcName)s:%(lineno)d] - %(message)s' if debug_mode else \
                 '%(asctime)s [%(levelname)s] - %(message)s'
    formatter = logging.Formatter(format_str)

    # Create a lock to make the logger thread-safe
    lock = threading.Lock()

    # Create the logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Create console handler and set the formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if a file name is provided
    if file_name:
        file_handler = logging.FileHandler(file_name)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Add lock to the logger to make it thread-safe
    logger.addHandler(logging.NullHandler())
    logger._lock = lock

    return logger


def getLocalIpAddresses() -> Set[str]:
    """Get local IP addresses including '127.0.0.1' and 'localhost'.

    Returns:
        Set[str]: Set of local IP addresses.
    """
    ip_addresses = {'127.0.0.1', 'localhost'}
    for host_name in socket.gethostbyname_ex(socket.gethostname())[2]:
        ip_addresses.add(host_name)
    return ip_addresses


def openWebPage(http_port: int) -> None:
    """Open the webpage on a new browser tab.

    Args:
        http_port (int): Port number of the HTTP server.
    """
    time.sleep(1)
    webbrowser.open(f'http://localhost:{http_port}', new=2)


def httpServerTask(http_port: int, packet_capture_enabled: bool, client_poll_interval_ms: int,
                   disable_browser_autoload: bool) -> None:
    """Entry point to start the HTTP server.

    Args:
        http_port (int): Port number for the HTTP server.
        packet_capture_enabled (bool): Whether packet capture is enabled.
        client_poll_interval_ms (int): Client poll interval in milliseconds.
        disable_browser_autoload (bool): Whether to disable browser autoload.
    """
    # Create a thread to open the webpage
    if not disable_browser_autoload:
        webpage_open_thread = threading.Thread(target=openWebPage, args=(http_port,))
        webpage_open_thread.start()

    telemetry_server = TelemetryWebServer(
        port=http_port,
        packet_capture_enabled=packet_capture_enabled,
        client_poll_interval_ms=client_poll_interval_ms,
        debug_mode=False
    )
    log_str = "Starting F1 2023 telemetry server. Open one of the below addresses in your browser\n"
    ip_addresses = getLocalIpAddresses()
    for ip_addr in ip_addresses:
        log_str += f"    http://{ip_addr}:{http_port}\n"
    log_str += "NOTE: The tables will be empty until the red lights appear on the screen before the race start\n"
    log_str += "That is when the game starts sending telemetry data"
    logging.info(log_str)
    telemetry_server.run()


def f1TelemetryServerTask(packet_capture: PacketCaptureMode, port_number: int,
                              overtakes_autosave: bool, replay_server: bool,
                              post_race_data_autosave: bool) -> None:
    """Entry point to start the F1 23 telemetry server.

    Args:
        packet_capture (PacketCaptureMode): Packet capture mode.
        port_number (int): Port number for the telemetry client.
        overtakes_autosave (bool): Whether to autosave overtakes to a CSV file.
        replay_server (bool): Whether to enable the TCP replay debug server.
        post_race_data_autosave (bool): Whether to autosave race data at the end of the race.
    """
    time.sleep(2)
    if packet_capture != PacketCaptureMode.DISABLED:
        initPktCap(packet_capture)
    initAutosaves(overtakes_autosave, post_race_data_autosave)
    telemetry_client = F12023TelemetryHandler(port_number, packet_capture, replay_server)
    telemetry_client.run()


if __name__ == '__main__':
    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description="F1 2023 Telemetry Client and Server")

    # Add command-line arguments with default values
    parser.add_argument('-p', '--packet-capture-mode', type=PacketCaptureMode,
                        choices=list(PacketCaptureMode),
                        default=PacketCaptureMode.DISABLED,
                        metavar='packet_capture_mode {"disabled", "enabled", "enabled-with-autosave"}',
                        help="Packet capture mode (disabled, enabled, enabled-with-autosave)")
    parser.add_argument('-t', '--telemetry-port', type=int, default=20777, metavar='TELEMETRY_PORT',
                        help="Port number for F1 telemetry client")
    parser.add_argument('-s', '--server-port', type=int, default=5000, metavar='SERVER_PORT',
                        help="Port number for HTTP server")
    parser.add_argument('-o', '--overtakes-autosave', action='store_true',
                        help="Autosave all overtakes to a CSV file")
    parser.add_argument('-f', '--post-race-data-autosave', action='store_true',
                        help="Autosave all race data into a JSON file at the end of the race")
    parser.add_argument('--replay-server', action='store_true',
                        help="Enable the TCP replay debug server")
    parser.add_argument('--disable-browser-autoload', action='store_true',
                        help="Set this flag to not open the browser tab automatically")
    parser.add_argument('-r', '--refresh-interval', type=int, default=200, metavar='REFRESH_INTERVAL',
                        help="How often the web page should refresh itself with new data")
    parser.add_argument('l', '--log-file', type=str, default=None, metavar='LOG_FILE',
                        help='Write output to specified log file (append)')
    parser.add_argument('-d', '--debug', action='store_true',
                        help="Enable debug logs")

    # Parse the command-line arguments
    args = parser.parse_args()
    initDirectories()
    initLogger(file_name=args.log_file, debug_mode=args.debug)

    # First init the telemetry client on a main thread
    client_thread = threading.Thread(target=f1TelemetryServerTask,
                                     args=(args.packet_capture_mode, args.telemetry_port,
                                           args.overtakes_autosave, args.replay_server,
                                           args.post_race_data_autosave))
    client_thread.daemon = True
    client_thread.start()

    # Run the HTTP server on the main thread. Flask does not like running on separate threads
    packet_capture_enabled = \
        args.packet_capture_mode in [PacketCaptureMode.ENABLED, PacketCaptureMode.ENABLED_WITH_AUTOSAVE]
    httpServerTask(args.server_port, packet_capture_enabled, args.refresh_interval,
                   args.disable_browser_autoload)

    # Set up a keyboard interrupt handler
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Ctrl+C pressed. Exiting...")
        sys.exit()