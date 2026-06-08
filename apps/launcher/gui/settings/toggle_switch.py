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

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class ToggleSwitchWidget(QWidget):
    """Pill-shaped on/off toggle switch."""

    toggled = Signal(bool)

    _WIDTH = 46
    _HEIGHT = 24
    _RADIUS = 12
    _KNOB_MARGIN = 2
    _COLOR_ON = QColor("#0e639c")
    _COLOR_OFF = QColor("#3e3e3e")
    _COLOR_KNOB = QColor("#ffffff")

    def __init__(self, checked: bool = False, parent: QWidget = None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(self._WIDTH, self._HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setChecked(self, checked: bool) -> None:
        if self._checked != checked:
            self._checked = checked
            self.update()

    def isChecked(self) -> bool:
        return self._checked

    def mousePressEvent(self, event) -> None:
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()
        event.accept()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        # Background pill
        painter.setBrush(self._COLOR_ON if self._checked else self._COLOR_OFF)
        painter.drawRoundedRect(0, 0, self._WIDTH, self._HEIGHT, self._RADIUS, self._RADIUS)

        # Knob
        knob_size = self._HEIGHT - 2 * self._KNOB_MARGIN
        knob_x = (self._WIDTH - knob_size - self._KNOB_MARGIN) if self._checked else self._KNOB_MARGIN
        painter.setBrush(self._COLOR_KNOB)
        painter.drawEllipse(knob_x, self._KNOB_MARGIN, knob_size, knob_size)
