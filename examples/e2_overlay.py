from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QColor
from base import BaseOverlay, OverlaysConfig
import random
from PySide6.QtWidgets import QWidget

class SectorStatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self.sector_status = [1, 2, 3]  # 0: neutral, 1: green, 2: purple, 3: red

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        sector_width = width / 3

        colors = {
            0: QColor(50, 50, 50),   # Neutral/Grey
            1: QColor(0, 255, 0),    # Green (Best)
            2: QColor(128, 0, 128),  # Purple (Personal Best)
            3: QColor(255, 0, 0)     # Red (Worse)
        }

        for i, status in enumerate(self.sector_status):
            color = colors.get(status, QColor(50, 50, 50))
            painter.fillRect(int(i * sector_width), 0, int(sector_width), self.height(), color)

    def set_sector_status(self, status_list):
        if len(status_list) == 3:
            self.sector_status = status_list
            self.update()

class LapTimerOverlay(BaseOverlay):
    def build_ui(self):

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        font = QFont("Consolas", 14, QFont.Bold)

        self.curr_label = QLabel("Current: 1:42.532")
        self.curr_label.setFont(font)
        self.curr_label.setStyleSheet("color: #00FFFF;")

        self.last_label = QLabel("Last: 1:43.210")
        self.last_label.setFont(font)
        self.last_label.setStyleSheet("color: #FFFFFF;")

        self.best_label = QLabel("Best: 1:41.978")
        self.best_label.setFont(font)
        self.best_label.setStyleSheet("color: #00FF00;")

        layout.addWidget(self.curr_label)
        layout.addWidget(self.last_label)
        layout.addWidget(self.best_label)

        self.sector_bar = SectorStatusBar()
        layout.addWidget(self.sector_bar)

        self.setLayout(layout)

        self.resize(220, 140)

    def update_data(self, data):
        # Dummy data for sector status
        sector_status = [random.randint(0, 3) for _ in range(3)]
        self.sector_bar.set_sector_status(sector_status)

        delta = random.uniform(-0.3, 0.3)
        self.current_lap_time += delta

        if random.random() < 0.2:
            self.last_lap_time = self.current_lap_time
            if self.last_lap_time < self.best_lap_time:
                self.best_lap_time = self.last_lap_time
            self.current_lap_time = 100 + random.uniform(-1.0, 1.0)

        self.curr_label.setText(f"Current: {self.format_time(self.current_lap_time)}")
        self.last_label.setText(f"Last: {self.format_time(self.last_lap_time)}")
        self.best_label.setText(f"Best: {self.format_time(self.best_lap_time)}")

    @staticmethod
    def format_time(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}:{secs:06.3f}"

from PySide6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    cfg = OverlaysConfig(x=100, y=100, width=240, height=120)
    overlay = LapTimerOverlay(cfg, locked=False)
    overlay.show()
    sys.exit(app.exec())
