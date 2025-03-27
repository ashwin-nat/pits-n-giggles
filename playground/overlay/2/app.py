import sys
import random
import os
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class HUDDataManager(QObject):
    speedChanged = pyqtSignal(int)
    lapChanged = pyqtSignal(int)
    borderModeChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._speed = 0
        self._lap = 0
        self._bordered = False

    @pyqtSlot(result=dict)
    def get_race_data(self):
        self._speed = random.randint(50, 250)
        self._lap = random.randint(1, 5)

        self.speedChanged.emit(self._speed)
        self.lapChanged.emit(self._lap)

        return {
            "speed": self._speed,
            "lap": self._lap
        }

    @pyqtSlot(result=bool)
    def toggle_border_mode(self):
        self._bordered = not self._bordered
        self.borderModeChanged.emit(self._bordered)
        return self._bordered

class RacingHUDOverlay(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create web channel for communication
        self.web_channel = QWebChannel()
        self.data_manager = HUDDataManager()
        self.web_channel.registerObject('dataManager', self.data_manager)

        # Create web view
        self.web_view = QWebEngineView()

        # Custom page to set up web channel
        self.web_page = QWebEnginePage(self)
        self.web_page.setWebChannel(self.web_channel)
        self.web_view.setPage(self.web_page)

        # Make web view transparent
        self.web_page.setBackgroundColor(Qt.transparent)

        # Set up window
        self.setCentralWidget(self.web_view)

        # Load HTML file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, 'hud.html')
        self.web_view.load(QUrl.fromLocalFile(html_path))

        # Initial window setup
        self.setup_window(bordered=False)

        # Timer for updating data
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.data_manager.get_race_data)
        self.update_timer.start(1000)  # Update every second

    def setup_window(self, bordered=False):
        if bordered:
            # Resizable window with title bar
            self.setWindowFlags(
                Qt.Window |
                Qt.WindowStaysOnTopHint
            )
        else:
            # Frameless, transparent overlay
            self.setWindowFlags(
                Qt.WindowStaysOnTopHint |
                Qt.FramelessWindowHint |
                Qt.Tool
            )
            self.setAttribute(Qt.WA_TranslucentBackground)

        # Set initial size and position
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(
            screen.width() - 250,  # Right side of screen
            50,  # 50 pixels from top
            250,  # Width
            150   # Height
        )

    def keyPressEvent(self, event):
        # Toggle border mode on F12
        if event.key() == Qt.Key_F12:
            self.data_manager.toggle_border_mode()
            self.setup_window(bordered=self.data_manager._bordered)

def main():
    app = QApplication(sys.argv)
    hud = RacingHUDOverlay()
    hud.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()