import argparse
from typing import Set
import socket
import threading
import time
import sys

from telemetry_handler import F12023TelemetryHandler, initPktCap
from telemetry_server import TelemetryServer

def get_local_ip_addresses() -> Set[str]:
    """Get local IP addresses including '127.0.0.1' and 'localhost'.
    """
    ip_addresses = {'127.0.0.1', 'localhost'}
    for host_name in socket.gethostbyname_ex(socket.gethostname())[2]:
        ip_addresses.add(host_name)
    return ip_addresses

def http_server_task(http_port: int) -> None:
    """Entry point to start the HTTP server.
    """
    telemetry_server = TelemetryServer(http_port, debug_mode=False)
    print("Starting F1 2023 telemetry server. Open one of the below addresses in your browser")
    ip_addresses = get_local_ip_addresses()
    for ip_addr in ip_addresses:
        print(f"    http://{ip_addr}:{http_port}")
    print("NOTE: The tables will be empty until the red lights appear on the screen before the race start")
    print("That is when the game starts sending telemetry data")
    telemetry_server.run()

def f1_telemetry_client_task(packet_capture: bool, port_number: int) -> None:
    """Entry point to start the F1 23 telemetry client.
    """
    if packet_capture:
        initPktCap()
    telemetry_client = F12023TelemetryHandler(port_number, packet_capture)
    telemetry_client.run()

if __name__ == '__main__':
    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description="F1 2023 Telemetry Client and Server")

    # Add command-line arguments with default values
    parser.add_argument('--no-packet-capture', dest='packet_capture_enabled', action='store_true', help="Disable packet capture", default=False)
    parser.add_argument('--telemetry-port', type=int, default=20777, help="Port number for F1 telemetry client")
    parser.add_argument('--server-port', type=int, default=5000, help="Port number for HTTP server")

    # Parse the command-line arguments
    args = parser.parse_args()

    # First init the telemetry client on a main thread
    client_thread = threading.Thread(target=f1_telemetry_client_task, args=(args.packet_capture_enabled, args.telemetry_port))
    client_thread.daemon = True
    client_thread.start()

    # Run the HTTP server on the main thread. Flask does not like running on separate threads
    http_server_task(args.server_port)

    # Set up a keyboard interrupt handler
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Ctrl+C pressed. Exiting...")
        sys.exit()
