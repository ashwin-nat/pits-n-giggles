from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QColor
from base import BaseOverlay, OverlaysConfig
import random

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
        self.setLayout(layout)

        self.resize(220, 120)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.setLayout(layout)

    def make_row(self, title, label):
        row = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #ddd;")
        row.addWidget(lbl)
        row.addWidget(label)
        return row

    def update_data(self, data):
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
    overlay = LapTimerOverlay(cfg, locked=True)
    overlay.show()
    sys.exit(app.exec())
