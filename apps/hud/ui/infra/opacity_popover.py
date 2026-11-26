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

from typing import Optional

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QFont, QGuiApplication, QHideEvent
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QSlider,
                               QVBoxLayout, QWidget)

from lib.logger import PngLogger

from ..overlays import BaseOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class OpacityPopover(QWidget):
    """Popup that edits one overlay's opacity override, previewing every change live.

    Usage: `popover.open_for(overlay, global_pos)`. Clicking outside closes it (Qt.Popup).
    """

    _STYLE = """
        QWidget#OpacityPopoverInner {
            background-color: rgba(32, 32, 32, 255);
            border: 1px solid #E10600;
            border-radius: 8px;
        }
        QLabel, QCheckBox {
            color: white;
            font-family: "Formula1";
            font-size: 14px;
            background: transparent;
        }
        QLabel#OpacityPopoverTitle {
            font-size: 16px;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #8a8a8a;
            border-radius: 3px;
            background-color: #1e1e1e;
        }
        QCheckBox::indicator:checked {
            border: 1px solid #E10600;
            background-color: #E10600;
        }
        QCheckBox:disabled, QLabel:disabled {
            color: rgba(255, 255, 255, 110);
        }
        QSlider::groove:horizontal {
            border: 1px solid #3e3e3e;
            height: 6px;
            background-color: #1e1e1e;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background-color: #E10600;
            border: 1px solid #E10600;
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }
        QSlider::handle:horizontal:disabled {
            background-color: #5a5a5a;
            border: 1px solid #5a5a5a;
        }
    """

    def __init__(self, logger: PngLogger):
        super().__init__(None, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(280)
        self._logger = logger
        self._overlay: Optional[BaseOverlay] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        inner = QWidget(self)
        inner.setObjectName("OpacityPopoverInner")
        outer.addWidget(inner)

        layout = QVBoxLayout(inner)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        self._title = QLabel(inner)
        self._title.setObjectName("OpacityPopoverTitle")
        self._title.setFont(QFont("Formula1"))
        layout.addWidget(self._title)

        self._enabled = QCheckBox("Override global opacity", inner)
        self._enabled.toggled.connect(self._on_change)
        layout.addWidget(self._enabled)

        row = QHBoxLayout()
        row.setSpacing(8)
        self._slider = QSlider(Qt.Orientation.Horizontal, inner)
        self._slider.setMaximum(100)
        self._slider.valueChanged.connect(self._on_change)
        self._value = QLabel(inner)
        self._value.setMinimumWidth(44)
        self._value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self._slider, 1)
        row.addWidget(self._value)
        layout.addLayout(row)

        self.setStyleSheet(self._STYLE)

    def open_for(self, overlay: BaseOverlay, global_pos: QPoint):
        """Point the popover at overlay and show it at global_pos, kept on that screen."""
        self._logger.debug("%s | Opening opacity popover at (%d, %d)",
                           overlay.OVERLAY_ID, global_pos.x(), global_pos.y())
        self._overlay = overlay
        self._title.setText(overlay.OVERLAY_ID.display_name)

        # Populate without previewing: the values already match the overlay
        self._enabled.blockSignals(True)
        self._slider.blockSignals(True)
        self._enabled.setChecked(overlay.config.opacity_override.enabled)
        self._slider.setMinimum(overlay.min_override_opacity())
        self._enabled.blockSignals(False)
        self._slider.blockSignals(False)
        self._sync_widgets()

        self.adjustSize()
        self.move(self._clamped_pos(global_pos))
        self.show()

    def hideEvent(self, event: QHideEvent):
        """Log the close: an outside click, or the lock."""
        self._logger.debug("%s | Opacity popover closed", self._overlay.OVERLAY_ID)
        super().hideEvent(event)

    def _on_change(self):
        self._overlay.set_opacity_override(self._enabled.isChecked(), self._slider.value())
        self._sync_widgets()

    def _sync_widgets(self):
        enabled = self._enabled.isChecked()
        self._slider.setEnabled(enabled)
        self._value.setEnabled(enabled)
        # The slider shows the resolved opacity: the global value while disabled, so enabling keeps the look
        self._slider.blockSignals(True)
        self._slider.setValue(self._overlay.opacity)
        self._slider.blockSignals(False)
        self._value.setText(f"{self._slider.value()}%")

    def _clamped_pos(self, global_pos: QPoint) -> QPoint:
        screen = QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()
        area: QRect = screen.availableGeometry()
        x = min(max(global_pos.x(), area.left()), area.right() - self.width())
        y = min(max(global_pos.y(), area.top()), area.bottom() - self.height())
        return QPoint(x, y)
