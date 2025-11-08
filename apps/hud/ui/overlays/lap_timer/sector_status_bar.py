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

from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget

# -------------------------------------- CLASSES -----------------------------------------------------------------------
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
