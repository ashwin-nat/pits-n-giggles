# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

import json
import random
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow

from apps.in_game_overlay.overlay_receiver import OverlayUpdateReceiver


class BackendBridge(QObject):
    dataChanged = pyqtSignal(str)

    def send_data(self, data):
        # Convert dict to JSON string to ensure proper serialization
        json_data = json.dumps(data)
        self.dataChanged.emit(json_data)

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, sourceID):
        # Override the console message method
        print(f"JS {message}")

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 HUD Overlay")
        self.setGeometry(100, 100, 500, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        # Setup WebEngine
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # Set custom page with JavaScript console logging
        self.page = CustomWebEnginePage(self.view)
        self.view.setPage(self.page)

        # Create WebChannel before loading the page
        self.channel = QWebChannel()
        self.bridge = BackendBridge()
        self.channel.registerObject("backend", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Load HTML file
        html_path = Path(__file__).parent / "overlay.html"
        self.view.setUrl(QUrl.fromLocalFile(str(html_path.resolve())))

        # Give page time to load before sending data
        # QTimer.singleShot(1000, self.start_data_timer)

    def start_data_timer(self):
        # Timer for sending data every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.send_random_data)
        self.timer.start(1000)

    def on_data_update(self, data):
        # Handle data received from JavaScript
        self.bridge.send_data(data)

    def send_random_data(self):
        value = random.randint(0, 99)
        payload = {"value": value}
        print(f"Sending data: {payload}")
        self.on_data_update(payload)

    def toggle_bordered_mode(self):
        if self.windowFlags() & Qt.WindowType.FramelessWindowHint:
            # Currently borderless → switch to bordered/windowed
            self.setWindowFlags(
                Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        else:
            # Currently bordered/windowed → switch to borderless
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self.show()  # Necessary to re-apply window flags

def client_recv_thread(window: OverlayWindow, server_port: int = 4768):
    """
    Function to run the client receiver in a separate thread.

    Args:
        window (OverlayWindow): The overlay window instance.
        server_port (int): The port number for the server connection.
    """

    server_url = f"http://localhost:{server_port}"
    receiver = OverlayUpdateReceiver(server_url=server_url, logger=None)
    receiver.register_event_handler(
        event_name="on-screen-hud-overlay-update",
        callback=lambda data: window.on_data_update(data))
    receiver.run()

if __name__ == "__main__":
    port = 4768
    app = QApplication(sys.argv)
    window = OverlayWindow()

    recv_thread = threading.Thread(
        target=client_recv_thread,
        args=(window,port),
        daemon=True
    )
    recv_thread.start()

    # window.toggle_bordered_mode()
    window.show()
    sys.exit(app.exec())