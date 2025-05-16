import sys
import random
import os
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import Qt, QUrl, QTimer, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel

class HUDDataManager(QObject):
    speedChanged = pyqtSignal(int)
    lapChanged = pyqtSignal(int)
    borderModeChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._speed = 0
        self._lap = 0
        self._bordered = True

    @pyqtSlot(result=dict)
    def get_race_data(self):
        # Generate random data for speed and lap
        self._speed = random.randint(50, 250)
        self._lap = random.randint(1, 5)

        # Emit signals to update the data
        self.speedChanged.emit(self._speed)
        self.lapChanged.emit(self._lap)

        # Return the current data as a dictionary
        return {
            "speed": self._speed,
            "lap": self._lap
        }

    @pyqtSlot(result=bool)
    def toggle_border_mode(self):
        # Toggle border mode
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
        self.web_page.setBackgroundColor(Qt.GlobalColor.transparent)

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
        self.update_timer.timeout.connect(self.update_race_data)
        self.update_timer.start(1000)  # Update every second

    def update_race_data(self):
        # Fetch and update race data
        self.data_manager.get_race_data()

    def setup_window(self, bordered=False):
        if bordered:
            self.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.WindowStaysOnTopHint
            )
        else:
            self.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set initial size and position
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(
            screen.width() - 250,
            50,
            250,
            150
        )

    @pyqtSlot()
    def toggle_bordered_mode(self):
        bordered = self.data_manager.toggle_border_mode()
        self.hide()
        self.setup_window(bordered=bordered)
        self.show()


def main():
    print('starting app')
    app = QApplication(sys.argv)
    hud = RacingHUDOverlay()
    hud.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
