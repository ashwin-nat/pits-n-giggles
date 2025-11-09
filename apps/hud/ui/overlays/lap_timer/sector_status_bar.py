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

from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------
class SectorStatusBar(QWidget):

    DEFAULT_SECTOR_STATUS = [F1Utils.SECTOR_STATUS_NA] * 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self.sector_status = self.DEFAULT_SECTOR_STATUS

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        sector_width = width / 3

        # Make colours consistent with the bootstrap colours used in driver view
        colors = {
            F1Utils.SECTOR_STATUS_NA: QColor(0x6c, 0x75, 0x7d),
            F1Utils.SECTOR_STATUS_YELLOW: QColor(0xff, 0xc1, 0x07),
            F1Utils.SECTOR_STATUS_GREEN: QColor(0x28, 0xa7, 0x45),
            F1Utils.SECTOR_STATUS_PURPLE: QColor(0x80, 0, 0x80),
            F1Utils.SECTOR_STATUS_INVALID: QColor(0xdc, 0x35, 0x45)
        }

        for i, status in enumerate(self.sector_status):
            color = colors.get(status, QColor(50, 50, 50))
            painter.fillRect(int(i * sector_width), 0, int(sector_width), self.height(), color)

    def set_sector_status(self, status_list):
        if len(status_list) == 3:
            self.sector_status = status_list
            self.update()
