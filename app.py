from telemetry_handler import F12023TelemetryHandler
from telemetry_server import TelemetryServer
import threading
import time
import sys

http_port = 5000
f1_telemetry_port = 20777


def http_server_thread():

    telemetry_server = TelemetryServer(http_port, debug_mode=True)
    print("Starting HTTP Server")
    telemetry_server.run()

def f1_telemetry_client_thread():

    telemetry_client = F12023TelemetryHandler(f1_telemetry_port)
    print("Starting F1 telemetry client. Open http://127.0.0.1:" + str(http_port))
    telemetry_client.run()

if __name__ == '__main__':


    client_thread = threading.Thread(target=f1_telemetry_client_thread)
    # http_server_thread = threading.Thread(target=http_server_thread)

    client_thread.daemon = True
    # http_server_thread.daemon = True

    client_thread.start()
    # http_server_thread.start()

    http_server_thread()

    # Set up a keyboard interrupt handler
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Ctrl+C pressed. Exiting...")
        sys.exit()