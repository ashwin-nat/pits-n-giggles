import sys
import random
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel


class LapTimerOverlay(QWidget):
    def __init__(self, locked: bool = True):
        super().__init__()
        self.locked = locked

        self._init_ui()
        self._apply_window_flags()

        # Dummy data
        self.current_lap_time = 102.532
        self.last_lap_time = 103.210
        self.best_lap_time = 101.978

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dummy_times)
        self.update_timer.start(1000)

    # ---------------- UI ---------------- #
    def _init_ui(self):
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

    # ---------------- Window Behavior ---------------- #
    def _apply_window_flags(self):
        """Apply window flags and attributes based on lock state."""
        if self.locked:
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool
            )
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.setFixedSize(self.size())  # prevent resize
        else:
            self.setWindowFlags(
                Qt.Window |
                Qt.WindowStaysOnTopHint |
                Qt.WindowTitleHint |
                Qt.WindowSystemMenuHint |
                Qt.WindowCloseButtonHint
            )
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.setMinimumSize(150, 80)
            self.setMaximumSize(600, 400)
            self.setFixedSize(QSize())  # allow resize

        # Important: must be called after changing flags
        self.show()

    def toggle_lock(self):
        """Toggle between locked and unlocked states."""
        self.locked = not self.locked
        self._apply_window_flags()

    # ---------------- Paint & Data ---------------- #
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 160))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

    def update_dummy_times(self):
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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Hardcoded flag for now — toggle this to True/False
    locked = False

    overlay = LapTimerOverlay(locked=locked)
    overlay.move(100, 100)
    overlay.show()

    sys.exit(app.exec())
