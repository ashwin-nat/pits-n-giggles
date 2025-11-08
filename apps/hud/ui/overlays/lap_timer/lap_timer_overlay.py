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

from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QFont
from base import BaseOverlay
import random
from .sector_status_bar import SectorStatusBar

# -------------------------------------- CLASSES -----------------------------------------------------------------------

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

        self.resize(220, 140) # Increased height to accommodate the sector bar

    def make_row(self, title, label):
        row = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #ddd;")
        row.addWidget(lbl)
        row.addWidget(label)
        return row

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
