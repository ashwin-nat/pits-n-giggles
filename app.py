from telemetry_handler import F12023TelemetryHandler
from telemetry_server import TelemetryServer
import threading
import time
import sys

http_port = 5000
f1_telemetry_port = 20777


def http_server_task() -> None:
    """Entry to point to start the HTTP server
    """

    telemetry_server = TelemetryServer(http_port, debug_mode=True)
    print("Starting HTTP Server")
    telemetry_server.run()

def f1_telemetry_client_task():
    """Entry point to start the F1 23 telemetry client
    """

    telemetry_client = F12023TelemetryHandler(f1_telemetry_port)
    print("Starting F1 telemetry client. Open http://127.0.0.1:" + str(http_port))
    telemetry_client.run()

if __name__ == '__main__':

    # First init the telemetry client on  a main thread
    client_thread = threading.Thread(target=f1_telemetry_client_task)
    client_thread.daemon = True
    client_thread.start()

    # Run the HTTP server on the main thread. flask does not like running on separate threads
    http_server_task()

    # Set up a keyboard interrupt handler
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Ctrl+C pressed. Exiting...")
        sys.exit()