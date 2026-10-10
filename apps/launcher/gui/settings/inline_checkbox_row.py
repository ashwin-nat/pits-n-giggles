# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Sequence

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QRegion
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QWidget

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_BORDER_COLOR = "#4a4a4a"
_BORDER_RADIUS = 4
_TITLE_INDENT = 12
_TITLE_GAP = 4  # border-less space either side of the title

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class RowItem:
    """One checkbox in an InlineCheckBoxRow"""
    path: str        # field path, passed back to on_changed
    label: str       # short text shown next to the checkbox
    tooltip: str     # longer description, shown on hover
    checked: bool


class InlineCheckBoxRow(QWidget):
    """A titled container holding a single row of labelled checkboxes, e.g. one per session type.
    The title sits on the top border line. The border is painted here, with a gap behind the title,
    so the row has no background of its own and works on any parent colour.

    Usage:
        row = InlineCheckBoxRow("Autosave data at the end of", items, on_changed=callback)
        layout.addWidget(row)
        row.checkboxes  # {path: QCheckBox}, for the caller to track
    """

    def __init__(self,
                 title: str,
                 items: Sequence[RowItem],
                 on_changed: Callable[[str, bool], None],
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.checkboxes: Dict[str, QCheckBox] = {}

        self._title_label = QLabel(title, self)
        self._title_label.setFont(QFont("Roboto", 9, QFont.Weight.Bold))
        self._title_label.setStyleSheet("background: transparent; border: none;")
        self._title_label.adjustSize()
        self._title_label.move(_TITLE_INDENT, 0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(_TITLE_INDENT, self._title_label.height() // 2 + 8, _TITLE_INDENT, 8)
        layout.setSpacing(24)
        for item in items:
            checkbox = QCheckBox(item.label)
            checkbox.setFont(QFont("Roboto", 10))
            checkbox.setStyleSheet("QCheckBox { background: transparent; }")
            checkbox.setChecked(item.checked)
            checkbox.setToolTip(item.tooltip)
            checkbox.stateChanged.connect(
                lambda state, p=item.path: on_changed(p, state == Qt.CheckState.Checked.value))
            self.checkboxes[item.path] = checkbox
            layout.addWidget(checkbox)
        layout.addStretch()

    def paintEvent(self, event) -> None:  # pylint: disable=invalid-name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(_BORDER_COLOR), 1))

        title_rect = self._title_label.geometry()
        gap = QRect(title_rect.left() - _TITLE_GAP, 0, title_rect.width() + 2 * _TITLE_GAP, title_rect.height())
        painter.setClipRegion(QRegion(self.rect()).subtracted(QRegion(gap)))

        top = title_rect.height() / 2
        painter.drawRoundedRect(QRectF(0.5, top, self.width() - 1, self.height() - top - 0.5),
                                _BORDER_RADIUS, _BORDER_RADIUS)
