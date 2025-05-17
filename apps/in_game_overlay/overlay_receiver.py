import logging
import time

import socketio

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

class TelemetryReceiver:
    def __init__(self, server_url="http://localhost:4768", logger=None):
        self.logger = logger or self._create_default_logger()
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.server_url = server_url

        # Register default connection handlers
        self.sio.on("connect", self._on_connect)
        self.sio.on("disconnect", self._on_disconnect)
        self.sio.on("connect_error", self._on_connect_error)

    def _create_default_logger(self):
        logging.basicConfig(level=logging.DEBUG)
        return logging.getLogger("receiver")

    # Default handlers
    def _on_connect(self):
        self.logger.info("Connected to server.")
        self.sio.emit("register-client", {"type": "on-screen-hud-overlay"})

    def _on_disconnect(self):
        self.logger.info("Disconnected from server.")

    def _on_connect_error(self, data):
        self.logger.error(f"Connection failed: {data}")

    # Public method to register additional event handlers
    def register_event_handler(self, event_name, callback):
        """Register a callback for a given event."""
        self.sio.on(event_name, callback)
        self.logger.debug(f"Registered handler for event: '{event_name}'")

    def run(self):
        try:
            self.logger.info("Attempting to connect...")
            self.sio.connect(self.server_url, transports=["polling"], wait_timeout=10)
            self.logger.info("Connected, entering receive loop...")

            while True:
                time.sleep(1)

        except Exception as e:
            self.logger.error(f"Error during connection: {e}")
        finally:
            if self.sio.connected:
                self.logger.info("Disconnecting...")
                self.sio.disconnect()

if __name__ == "__main__":
    # Example usage with a custom telemetry handler
    def my_telemetry_handler(data):
        print(f"Telemetry data: {data}")

    receiver = TelemetryReceiver()
    receiver.register_event_handler("on-screen-hud-overlay-update", my_telemetry_handler)
    receiver.run()
